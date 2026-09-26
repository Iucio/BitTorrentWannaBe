#pragma once

#include <string>

#include "announce.hpp"
#include "servidor_http.hpp"

namespace tracker {

// GET /announce ou /teste por enquanto -> JSON do announce
// Outro caminho -> 404 (invalido)
RespostaHttp rotear(Tracker& tracker, const std::string& alvo, const std::string& ip);

} // namespace tracker
