#pragma once

#include <string>

namespace tracker {

// Chave de acesso que o admin entrega ao cliente no cadastro:
// 32 caracteres hexadecimais (128 bits sorteados)
std::string gerar_chave();

} // namespace tracker
