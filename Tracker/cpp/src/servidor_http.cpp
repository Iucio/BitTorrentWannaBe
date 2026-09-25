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
    int servidor = socket(AF_INET, SOCK_STREAM, 0);
    if (servidor < 0) return false;

    int reuse = 1;
    setsockopt(servidor, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof reuse);

    sockaddr_in endereco{};
    endereco.sin_family = AF_INET;
    endereco.sin_addr.s_addr = htonl(INADDR_ANY);
    endereco.sin_port = htons(porta);
    if (bind(servidor, reinterpret_cast<sockaddr*>(&endereco), sizeof endereco) != 0 ||
        listen(servidor, 16) != 0) {
        close(servidor);
        return false;
    }
    std::cout << "[tracker] ouvindo em 0.0.0.0:" << porta << std::endl;

    while (true) {
        sockaddr_in remoto{};
        socklen_t tamanho = sizeof remoto;
        int cliente = accept(servidor, reinterpret_cast<sockaddr*>(&remoto), &tamanho);
        if (cliente < 0) continue;

        char ip[INET_ADDRSTRLEN] = {0};
        inet_ntop(AF_INET, &remoto.sin_addr, ip, sizeof ip);
        atender(cliente, ip, handler);
        close(cliente);
    }
}

} // namespace tracker
