#pragma once

#include <map>
#include <optional>
#include <string>
#include <variant>

#include "modelos.hpp"

namespace tracker {

// %XX -> byte, '+' -> espaço
std::optional<std::string> percent_decode(const std::string& s);

// "a=1&b=2" -> {a: 1, b: 2}
std::optional<std::map<std::string, std::string>> parse_query(const std::string& query);

// Monta o AnnounceRequest ou devolve a mensagem de erro.
// O parâmetro ip da url tem prioridade sobre ip_remetente.
std::variant<AnnounceRequest, std::string> ler_announce(const std::string& query,
                                                        const std::string& ip_remetente);

} // namespace tracker
