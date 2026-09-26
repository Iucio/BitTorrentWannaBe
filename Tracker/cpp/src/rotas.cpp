#include "rotas.hpp"

#include "json.hpp"
#include "url.hpp"

namespace tracker {

RespostaHttp rotear(Tracker& tracker, const std::string& alvo, const std::string& ip) {
    const auto interrogacao = alvo.find('?');
    const std::string caminho = alvo.substr(0, interrogacao);
    const std::string query = interrogacao == std::string::npos ? "" : alvo.substr(interrogacao + 1);

    // /teste pra funcionar com o outro la por enquanto, dps fazer um proprio pra testes se for o caso
    if (caminho != "/announce" && caminho != "/teste") {
        return {404, "{\"failure_reason\":\"caminho desconhecido\"}"};
    }

    auto lido = ler_announce(query, ip);
    if (auto* erro = std::get_if<std::string>(&lido)) {
        AnnounceResponse resp;
        resp.falha = *erro;
        return {400, resposta_para_json(resp)};
    }
    // erro de regra: volta com 200 + failure_reason, como no BitTorrent real (tipo o do min_interval > q a ultima requisiçãod a pessoa)
    return {200, resposta_para_json(tracker.announce(std::get<AnnounceRequest>(lido)))};
}

} // namespace tracker
