#include "url.hpp"

#include <cctype>

namespace tracker {

namespace {

int hex(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    return -1;
}

} // namespace

std::optional<std::string> percent_decode(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (std::size_t i = 0; i < s.size(); i++) {
        if (s[i] == '+') {
            out += ' ';
        } else if (s[i] == '%') {
            if (i + 2 >= s.size()) return std::nullopt;
            int alto = hex(s[i + 1]), baixo = hex(s[i + 2]);
            if (alto < 0 || baixo < 0) return std::nullopt;
            out += static_cast<char>(alto * 16 + baixo);
            i += 2;
        } else {
            out += s[i];
        }
    }
    return out;
}

std::optional<std::map<std::string, std::string>> parse_query(const std::string& query) {
    std::map<std::string, std::string> params;
    std::size_t inicio = 0;
    while (inicio <= query.size()) {
        std::size_t fim = query.find('&', inicio);
        if (fim == std::string::npos) fim = query.size();
        std::string par = query.substr(inicio, fim - inicio);
        if (!par.empty()) {
            std::size_t igual = par.find('=');
            auto chave = percent_decode(par.substr(0, igual));
            auto valor = percent_decode(igual == std::string::npos ? "" : par.substr(igual + 1));
            if (!chave || !valor) return std::nullopt;
            params[*chave] = *valor;
        }
        inicio = fim + 1;
    }
    return params;
}

} // namespace tracker
