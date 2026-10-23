#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>

#include "announce.hpp"
#include "chave.hpp"
#include "repositorio_sqlite.hpp"
#include "rotas.hpp"
#include "servidor_http.hpp"

namespace {

const char* const BANCO_PADRAO = "tracker.db";

int cadastrar(const std::string& nome, const std::string& caminho_banco) {
    try {
        tracker::RepositorioSQLite repo(caminho_banco);
        const std::string chave = tracker::gerar_chave();
        const auto id = repo.cadastrar_cliente(nome, chave, tracker::relogio_sistema());
        std::cout << "cliente " << id << " cadastrado: " << nome << "\n"
                  << "chave de acesso: " << chave << std::endl;
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }
}

} // namespace

// Uso:
//   ./tracker [porta] [banco]            servidor (padrões: 80 e tracker.db)
//   ./tracker cadastrar <nome> [banco]   cadastra um cliente e mostra a chave dele
int main(int argc, char** argv) {
    if (argc > 1 && std::string(argv[1]) == "cadastrar") {
        if (argc < 3) {
            std::cerr << "uso: ./tracker cadastrar <nome> [banco]\n";
            return 1;
        }
        return cadastrar(argv[2], argc > 3 ? argv[3] : BANCO_PADRAO);
    }

    int porta = argc > 1 ? std::atoi(argv[1]) : 80;
    if (porta < 1 || porta > 65535) {
        std::cerr << "porta invalida: " << argv[1] << "\n";
        return 1;
    }

    const std::string caminho_banco = argc > 2 ? argv[2] : BANCO_PADRAO;
    std::unique_ptr<tracker::RepositorioSQLite> repo;
    try {
        repo = std::make_unique<tracker::RepositorioSQLite>(caminho_banco);
    } catch (const std::exception& e) {
        std::cerr << e.what() << std::endl;
        return 1;
    }
    std::cout << "[tracker] banco: " << caminho_banco << std::endl;
    tracker::Tracker tracker(*repo);

    bool ok = tracker::servir(static_cast<std::uint16_t>(porta),
                              [&](const std::string& alvo, const std::string& ip) {
                                  return tracker::rotear(tracker, alvo, ip);
                              });
    if (!ok) {
        std::cerr << "nao foi possivel abrir a porta " << porta
                  << " (ja esta em uso? portas < 1024 precisam de sudo)"
                  << std::endl;
        return 1;
    }
}
