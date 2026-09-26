#pragma once

#include <cstdint>
#include <functional>
#include <string>

namespace tracker {

struct RespostaHttp {
    int status = 200;
    std::string corpo;
    std::string content_type = "application/json";
};

// alvo: "/announce?..."   ip: quem conectou
using Handler = std::function<RespostaHttp(const std::string& alvo, const std::string& ip)>;

// Servidor http minimo, só GET, uma conexão por vez
bool servir(std::uint16_t porta, const Handler& handler);

} // namespace tracker
