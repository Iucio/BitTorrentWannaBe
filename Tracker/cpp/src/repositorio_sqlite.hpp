#pragma once

#include <string>

#include "repositorio.hpp"

struct sqlite3;
struct sqlite3_stmt;

namespace tracker {

// Repositório persistido em SQLite. O banco é um arquivo local do Tracker
// (ex.: "tracker.db"); ":memory:" cria um banco temporário, útil em testes.
// Lança std::runtime_error se não conseguir abrir ou preparar o banco.
class RepositorioSQLite : public Repositorio {
public:
    explicit RepositorioSQLite(const std::string& caminho);
    ~RepositorioSQLite() override;

    RepositorioSQLite(const RepositorioSQLite&) = delete;
    RepositorioSQLite& operator=(const RepositorioSQLite&) = delete;

    std::optional<Peer> buscar_peer(const std::string& info_hash,
                                    const std::string& peer_id) const override;
    void salvar_peer(const std::string& info_hash, const Peer& peer) override;
    void remover_peer(const std::string& info_hash, const std::string& peer_id) override;
    std::vector<Peer> listar_peers(const std::string& info_hash) const override;
    void remover_expirados(Segundos limite) override;

private:
    void fechar();
    void criar_ou_migrar_schema();
    void executar(const char* sql);
    sqlite3_stmt* preparar(const char* sql);
    [[noreturn]] void erro(const std::string& contexto) const;

    sqlite3* db_ = nullptr;
    // consultas preparadas uma vez só e reaproveitadas a cada announce
    sqlite3_stmt* st_buscar_ = nullptr;
    sqlite3_stmt* st_salvar_ = nullptr;
    sqlite3_stmt* st_remover_ = nullptr;
    sqlite3_stmt* st_listar_ = nullptr;
    sqlite3_stmt* st_expirados_ = nullptr;
};

} // namespace tracker
