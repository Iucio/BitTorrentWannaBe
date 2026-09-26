#pragma once

#include <string>

#include "modelos.hpp"

namespace tracker {

// String entre aspas e escapada
std::string json_string(const std::string& s);

std::string resposta_para_json(const AnnounceResponse& resp);

} // namespace tracker
