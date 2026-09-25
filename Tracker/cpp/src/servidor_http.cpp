#include "servidor_http.hpp"

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <iostream>
#include <sstream>

namespace tracker {

namespace {

const char* texto_status(int status) {
    // TODO
    return "";
}

void enviar(int cliente, const RespostaHttp& resp) {
    // TODO
}

std::string ler_cabecalho(int cliente) {
    // TODO
    return "";
}

void atender(int cliente, const std::string& ip, const Handler& handler) {
    // TODO
}

} // namespace

bool servir(std::uint16_t porta, const Handler& handler) {
    // TODO
    return false;
}

} // namespace tracker
