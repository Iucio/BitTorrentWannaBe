#pragma once

#include <map>
#include <optional>
#include <string>

namespace tracker {

// %XX -> byte, '+' -> espaço
std::optional<std::string> percent_decode(const std::string& s);

// "a=1&b=2" -> {a: 1, b: 2}
std::optional<std::map<std::string, std::string>> parse_query(const std::string& query);

} // namespace tracker
