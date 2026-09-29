// Testes do Repositorio. Roda a mesma bateria no RepositorioMemoria e no
// RepositorioSQLite, para garantir que os dois se comportam igual.
// Uso: ./teste_repositorio   (ou ctest dentro da pasta build)

#include <cstdio>
#include <functional>
#include <iostream>
#include <string>

#include "announce.hpp"
#include "repositorio.hpp"
#include "repositorio_sqlite.hpp"

using namespace tracker;

static int falhas = 0;

#define VERIFICA(cond)                                                              \
    do {                                                                            \
        if (!(cond)) {                                                              \
            std::cerr << "  FALHOU (linha " << __LINE__ << "): " #cond << "\n";    \
            falhas++;                                                               \
        }                                                                           \
    } while (0)

// 20 bytes com \0 no meio, como um SHA-1 de verdade pode ter
static std::string hash_binario(char c) {
    std::string h(20, c);
    h[5] = '\0';
    return h;
}

static Peer peer(const std::string& id, std::int64_t left, Segundos quando) {
    Peer p;
    p.peer_id = id;
    p.ip = "192.168.0.10";
    p.porta = 6881;
    p.left = left;
    p.ultimo_announce = quando;
    return p;
}

static void testar_repositorio(Repositorio& repo) {
    const std::string arq1 = hash_binario('A');
    const std::string arq2 = hash_binario('B');
    const std::string id1 = "-UF0001-aaaaaaaaaaaa";
    const std::string id2 = "-UF0001-bbbbbbbbbbbb";

    VERIFICA(!repo.buscar_peer(arq1, id1));

    repo.salvar_peer(arq1, peer(id1, 100, 1000));
    auto achado = repo.buscar_peer(arq1, id1);
    VERIFICA(achado && achado->left == 100 && achado->porta == 6881 && achado->ip == "192.168.0.10");

    // mesmo peer de novo = atualiza, não duplica
    repo.salvar_peer(arq1, peer(id1, 0, 2000));
    VERIFICA(repo.listar_peers(arq1).size() == 1);
    VERIFICA(repo.buscar_peer(arq1, id1)->completo());

    // vários peers no mesmo arquivo, e o mesmo peer em outro arquivo
    repo.salvar_peer(arq1, peer(id2, 50, 2000));
    repo.salvar_peer(arq2, peer(id1, 10, 2000));
    VERIFICA(repo.listar_peers(arq1).size() == 2);
    VERIFICA(repo.listar_peers(arq2).size() == 1);

    // info_hash que só difere depois do \0 não pode colidir
    std::string quase_igual = arq1;
    quase_igual[10] = 'Z';
    VERIFICA(repo.listar_peers(quase_igual).empty());

    repo.remover_peer(arq1, id2);
    VERIFICA(!repo.buscar_peer(arq1, id2));
    VERIFICA(repo.listar_peers(arq1).size() == 1);

    repo.salvar_peer(arq2, peer(id2, 10, 500)); // antigo
    repo.remover_expirados(1000);
    VERIFICA(!repo.buscar_peer(arq2, id2));
    VERIFICA(repo.buscar_peer(arq2, id1)); // recente, continua
}

static void testar_tracker(Repositorio& repo) {
    Segundos agora = 1'700'000'000;
    Tracker t(repo, Config{}, [&] { return agora; });

    AnnounceRequest req;
    req.info_hash = hash_binario('C');
    req.ip = "10.0.0.1";
    req.porta = 7000;

    req.peer_id = "-UF0001-seeder000000";
    req.left = 0;
    req.evento = Evento::Started;
    t.announce(req);

    req.peer_id = "-UF0001-leecher00000";
    req.left = 123;
    auto resp = t.announce(req);
    VERIFICA(!resp.falha);
    VERIFICA(resp.complete == 1 && resp.incomplete == 1);
    VERIFICA(resp.peers.size() == 1); // não devolve o próprio peer

    req.evento = Evento::Nenhum;
    VERIFICA(t.announce(req).falha); // antes do min_interval

    agora += 60 * 60 * 2; // 2h sem announce: os dois expiram
    req.evento = Evento::Started;
    resp = t.announce(req);
    VERIFICA(resp.complete == 0 && resp.incomplete == 1);
}

static void testar_persistencia() {
    const std::string arquivo = "teste_persistencia.db";
    std::remove(arquivo.c_str());
    {
        RepositorioSQLite repo(arquivo);
        repo.salvar_peer(hash_binario('D'), peer("-UF0001-persistente0", 0, 42));
    }
    {
        RepositorioSQLite repo(arquivo); // reabre: o dado tem que estar lá
        auto p = repo.buscar_peer(hash_binario('D'), "-UF0001-persistente0");
        VERIFICA(p && p->ultimo_announce == 42);
    }
    for (const char* sufixo : {"", "-wal", "-shm"}) std::remove((arquivo + sufixo).c_str());
}

static void rodar(const char* nome, const std::function<void()>& teste) {
    const int antes = falhas;
    teste();
    std::cout << (falhas == antes ? "[ok]    " : "[FALHA] ") << nome << "\n";
}

int main() {
    rodar("memoria: operacoes basicas", [] { RepositorioMemoria r; testar_repositorio(r); });
    rodar("sqlite: operacoes basicas", [] { RepositorioSQLite r(":memory:"); testar_repositorio(r); });
    rodar("memoria: announce", [] { RepositorioMemoria r; testar_tracker(r); });
    rodar("sqlite: announce", [] { RepositorioSQLite r(":memory:"); testar_tracker(r); });
    rodar("sqlite: persiste depois de fechar", testar_persistencia);

    std::cout << (falhas ? "\nFALHOU\n" : "\ntodos os testes passaram\n");
    return falhas ? 1 : 0;
}
