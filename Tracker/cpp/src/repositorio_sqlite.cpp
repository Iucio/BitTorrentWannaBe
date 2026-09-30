#include "repositorio_sqlite.hpp"

#include <sqlite3.h>

#include <stdexcept>
#include <string>

namespace tracker {

namespace {

// Tabela de peers do swarm. info_hash e peer_id são 20 bytes crus (podem
// conter \0), por isso BLOB. A chave composta já serve de índice para as
// buscas por info_hash, que é a primeira coluna dela.
// uploaded/downloaded: totais da sessão atual do cliente, como ele informa no
// announce (voltam a zero quando o cliente reinicia).
const int VERSAO_SCHEMA = 2;
const char* const SCHEMA = R"sql(
CREATE TABLE IF NOT EXISTS peers (
    info_hash       BLOB    NOT NULL CHECK (length(info_hash) = 20),
    peer_id         BLOB    NOT NULL CHECK (length(peer_id) = 20),
    ip              TEXT    NOT NULL,
    porta           INTEGER NOT NULL CHECK (porta BETWEEN 1 AND 65535),
    left_bytes      INTEGER NOT NULL CHECK (left_bytes >= 0), -- 0 = seeder
    ultimo_announce INTEGER NOT NULL,                         -- unix timestamp (s)
    uploaded        INTEGER NOT NULL DEFAULT 0 CHECK (uploaded >= 0),
    downloaded      INTEGER NOT NULL DEFAULT 0 CHECK (downloaded >= 0),
    PRIMARY KEY (info_hash, peer_id)
) WITHOUT ROWID;

CREATE INDEX IF NOT EXISTS idx_peers_expiracao ON peers (ultimo_announce);
)sql";

// Banco criado pela versão 1 (sem uploaded/downloaded): acrescenta as colunas.
const char* const MIGRACAO_V1_PARA_V2 = R"sql(
ALTER TABLE peers ADD COLUMN uploaded   INTEGER NOT NULL DEFAULT 0 CHECK (uploaded >= 0);
ALTER TABLE peers ADD COLUMN downloaded INTEGER NOT NULL DEFAULT 0 CHECK (downloaded >= 0);
)sql";

// Garante que a consulta preparada volta ao estado inicial ao sair do escopo,
// mesmo se uma exceção for lançada no meio do caminho.
struct UsoStmt {
    sqlite3_stmt* st;
    ~UsoStmt() {
        sqlite3_reset(st);
        sqlite3_clear_bindings(st);
    }
};

void ligar_blob(sqlite3_stmt* st, int i, const std::string& bytes) {
    sqlite3_bind_blob(st, i, bytes.data(), static_cast<int>(bytes.size()), SQLITE_TRANSIENT);
}

std::string ler_blob(sqlite3_stmt* st, int col) {
    const auto* dados = static_cast<const char*>(sqlite3_column_blob(st, col));
    return dados ? std::string(dados, static_cast<std::size_t>(sqlite3_column_bytes(st, col)))
                 : std::string();
}

std::string ler_texto(sqlite3_stmt* st, int col) {
    const auto* dados = reinterpret_cast<const char*>(sqlite3_column_text(st, col));
    return dados ? std::string(dados, static_cast<std::size_t>(sqlite3_column_bytes(st, col)))
                 : std::string();
}

// colunas na ordem: peer_id, ip, porta, left_bytes, ultimo_announce, uploaded, downloaded
Peer ler_peer(sqlite3_stmt* st) {
    Peer p;
    p.peer_id = ler_blob(st, 0);
    p.ip = ler_texto(st, 1);
    p.porta = static_cast<std::uint16_t>(sqlite3_column_int(st, 2));
    p.left = sqlite3_column_int64(st, 3);
    p.ultimo_announce = sqlite3_column_int64(st, 4);
    p.uploaded = sqlite3_column_int64(st, 5);
    p.downloaded = sqlite3_column_int64(st, 6);
    return p;
}

} // namespace

RepositorioSQLite::RepositorioSQLite(const std::string& caminho) {
    if (sqlite3_open(caminho.c_str(), &db_) != SQLITE_OK) {
        std::string msg = db_ ? sqlite3_errmsg(db_) : "sem memoria";
        sqlite3_close(db_);
        db_ = nullptr;
        throw std::runtime_error("nao foi possivel abrir o banco '" + caminho + "': " + msg);
    }
    try {
        // WAL + NORMAL: cada escrita não força fsync, o announce continua rápido
        executar("PRAGMA journal_mode = WAL;");
        executar("PRAGMA synchronous = NORMAL;");
        criar_ou_migrar_schema();

        st_buscar_ = preparar(
            "SELECT peer_id, ip, porta, left_bytes, ultimo_announce, uploaded, downloaded "
            "FROM peers "
            "WHERE info_hash = ?1 AND peer_id = ?2;");
        st_salvar_ = preparar(
            "INSERT INTO peers (info_hash, peer_id, ip, porta, left_bytes, ultimo_announce, "
            "uploaded, downloaded) "
            "VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8) "
            "ON CONFLICT (info_hash, peer_id) DO UPDATE SET "
            "ip = excluded.ip, porta = excluded.porta, left_bytes = excluded.left_bytes, "
            "ultimo_announce = excluded.ultimo_announce, "
            "uploaded = excluded.uploaded, downloaded = excluded.downloaded;");
        st_remover_ = preparar("DELETE FROM peers WHERE info_hash = ?1 AND peer_id = ?2;");
        st_listar_ = preparar(
            "SELECT peer_id, ip, porta, left_bytes, ultimo_announce, uploaded, downloaded "
            "FROM peers "
            "WHERE info_hash = ?1;");
        st_expirados_ = preparar("DELETE FROM peers WHERE ultimo_announce < ?1;");
    } catch (...) {
        fechar(); // construtor falhou: o destrutor não roda, então libera aqui
        throw;
    }
}

RepositorioSQLite::~RepositorioSQLite() { fechar(); }

void RepositorioSQLite::fechar() {
    for (auto** st : {&st_buscar_, &st_salvar_, &st_remover_, &st_listar_, &st_expirados_}) {
        sqlite3_finalize(*st);
        *st = nullptr;
    }
    sqlite3_close(db_);
    db_ = nullptr;
}

std::optional<Peer> RepositorioSQLite::buscar_peer(const std::string& info_hash,
                                                   const std::string& peer_id) const {
    UsoStmt uso{st_buscar_};
    ligar_blob(st_buscar_, 1, info_hash);
    ligar_blob(st_buscar_, 2, peer_id);
    const int rc = sqlite3_step(st_buscar_);
    if (rc == SQLITE_ROW) return ler_peer(st_buscar_);
    if (rc != SQLITE_DONE) erro("buscar_peer");
    return std::nullopt;
}

void RepositorioSQLite::salvar_peer(const std::string& info_hash, const Peer& peer) {
    UsoStmt uso{st_salvar_};
    ligar_blob(st_salvar_, 1, info_hash);
    ligar_blob(st_salvar_, 2, peer.peer_id);
    sqlite3_bind_text(st_salvar_, 3, peer.ip.data(), static_cast<int>(peer.ip.size()),
                      SQLITE_TRANSIENT);
    sqlite3_bind_int(st_salvar_, 4, peer.porta);
    sqlite3_bind_int64(st_salvar_, 5, peer.left);
    sqlite3_bind_int64(st_salvar_, 6, peer.ultimo_announce);
    sqlite3_bind_int64(st_salvar_, 7, peer.uploaded);
    sqlite3_bind_int64(st_salvar_, 8, peer.downloaded);
    if (sqlite3_step(st_salvar_) != SQLITE_DONE) erro("salvar_peer");
}

void RepositorioSQLite::remover_peer(const std::string& info_hash, const std::string& peer_id) {
    UsoStmt uso{st_remover_};
    ligar_blob(st_remover_, 1, info_hash);
    ligar_blob(st_remover_, 2, peer_id);
    if (sqlite3_step(st_remover_) != SQLITE_DONE) erro("remover_peer");
}

std::vector<Peer> RepositorioSQLite::listar_peers(const std::string& info_hash) const {
    UsoStmt uso{st_listar_};
    ligar_blob(st_listar_, 1, info_hash);
    std::vector<Peer> peers;
    int rc;
    while ((rc = sqlite3_step(st_listar_)) == SQLITE_ROW) peers.push_back(ler_peer(st_listar_));
    if (rc != SQLITE_DONE) erro("listar_peers");
    return peers;
}

void RepositorioSQLite::remover_expirados(Segundos limite) {
    UsoStmt uso{st_expirados_};
    sqlite3_bind_int64(st_expirados_, 1, limite);
    if (sqlite3_step(st_expirados_) != SQLITE_DONE) erro("remover_expirados");
}

// user_version fica gravado no próprio arquivo do banco e diz qual versão do
// schema ele tem: 0 = banco novo, 1 = sem uploaded/downloaded, 2 = atual.
void RepositorioSQLite::criar_ou_migrar_schema() {
    int versao = 0;
    sqlite3_stmt* st = preparar("PRAGMA user_version;");
    if (sqlite3_step(st) == SQLITE_ROW) versao = sqlite3_column_int(st, 0);
    sqlite3_finalize(st);

    if (versao > VERSAO_SCHEMA)
        throw std::runtime_error("banco criado por uma versao mais nova do Tracker");

    executar("BEGIN;");
    try {
        executar(SCHEMA); // banco novo: cria a tabela já com todas as colunas
        if (versao == 1) executar(MIGRACAO_V1_PARA_V2);
        executar(("PRAGMA user_version = " + std::to_string(VERSAO_SCHEMA) + ";").c_str());
        executar("COMMIT;");
    } catch (...) {
        sqlite3_exec(db_, "ROLLBACK;", nullptr, nullptr, nullptr);
        throw;
    }
}

void RepositorioSQLite::executar(const char* sql) {
    char* msg = nullptr;
    if (sqlite3_exec(db_, sql, nullptr, nullptr, &msg) != SQLITE_OK) {
        std::string texto = msg ? msg : "erro desconhecido";
        sqlite3_free(msg);
        throw std::runtime_error("sqlite: " + texto);
    }
}

sqlite3_stmt* RepositorioSQLite::preparar(const char* sql) {
    sqlite3_stmt* st = nullptr;
    if (sqlite3_prepare_v2(db_, sql, -1, &st, nullptr) != SQLITE_OK) erro("preparar consulta");
    return st;
}

void RepositorioSQLite::erro(const std::string& contexto) const {
    throw std::runtime_error("sqlite (" + contexto + "): " + sqlite3_errmsg(db_));
}

} // namespace tracker
