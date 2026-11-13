#include "chave.hpp"

#include <random>

namespace tracker {

std::string gerar_chave() {
    static const char* const HEX = "0123456789abcdef";
    std::random_device aleatorio; // gerador do sistema (no Linux, /dev/urandom)
    std::uniform_int_distribution<int> digito(0, 15);
    std::string chave;
    for (int i = 0; i < 32; i++) chave += HEX[digito(aleatorio)];
    return chave;
}

} // namespace tracker
