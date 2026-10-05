#include <cstdlib>
#include <iostream>
#include <memory>
#include <string>

#include "announce.hpp"
#include "repositorio_sqlite.hpp"
#include "rotas.hpp"
#include "servidor_http.hpp"

// Uso: ./tracker [porta] [banco]   (padrões: 80 e tracker.db)
int main(int argc, char** argv) {
    int porta = argc > 1 ? std::atoi(argv[1]) : 80;
    if (porta < 1 || porta > 65535) {
        std::cerr << "porta invalida: " << argv[1] << "\n";
        return 1;
    }

    const std::string caminho_banco = argc > 2 ? argv[2] : "tracker.db";
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
