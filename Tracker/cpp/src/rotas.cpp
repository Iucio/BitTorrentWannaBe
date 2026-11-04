#include "rotas.hpp"

#include "json.hpp"
#include "url.hpp"

namespace tracker {

namespace {

RespostaHttp erro_400(const std::string& motivo) {
    AnnounceResponse resp;
    resp.falha = motivo;
    return {400, resposta_para_json(resp)};
}

} // namespace

RespostaHttp rotear(Tracker& tracker, const std::string& alvo, const std::string& ip) {
    const auto interrogacao = alvo.find('?');
    const std::string caminho = alvo.substr(0, interrogacao);
    const std::string query = interrogacao == std::string::npos ? "" : alvo.substr(interrogacao + 1);

    if (caminho == "/peers") {
        auto lido = ler_consulta_peers(query);
        if (auto* erro = std::get_if<std::string>(&lido)) return erro_400(*erro);
        return {200, resposta_para_json(tracker.peers(std::get<ConsultaPeers>(lido)))};
    }

    // /teste pra funcionar com o outro la por enquanto, dps fazer um proprio pra testes se for o caso
    if (caminho != "/announce" && caminho != "/teste") {
        return {404, "{\"failure_reason\":\"caminho desconhecido\"}"};
    }

    auto lido = ler_announce(query, ip);
    if (auto* erro = std::get_if<std::string>(&lido)) return erro_400(*erro);
    // erro de regra: volta com 200 + failure_reason, como no BitTorrent real (tipo o do min_interval > q a ultima requisiçãod a pessoa)
    return {200, resposta_para_json(tracker.announce(std::get<AnnounceRequest>(lido)))};
}

} // namespace tracker
