#include <cstdlib>
#include <iostream>
#include <string>

#include "announce.hpp"
#include "repositorio.hpp"
#include "rotas.hpp"
#include "servidor_http.hpp"

// Uso: ./tracker [porta]   (padrão 80)
int main(int argc, char** argv) {
    int porta = argc > 1 ? std::atoi(argv[1]) : 80;
    if (porta < 1 || porta > 65535) {
        std::cerr << "porta invalida: " << argv[1] << "\n";
        return 1;
    }

    tracker::RepositorioMemoria repo;
    tracker::Tracker tracker(repo);

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
