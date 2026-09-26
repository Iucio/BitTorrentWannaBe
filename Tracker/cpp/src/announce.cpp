#include "announce.hpp"

#include <algorithm>
#include <chrono>

namespace tracker {

Segundos relogio_sistema() {
    using namespace std::chrono;
    return duration_cast<seconds>(steady_clock::now().time_since_epoch()).count();
}

Tracker::Tracker(Repositorio& repo, Config config, std::function<Segundos()> relogio)
    : repo_(repo), config_(config), relogio_(std::move(relogio)), rng_(std::random_device{}()) {}

AnnounceResponse Tracker::announce(const AnnounceRequest& req) {
    const Segundos agora = relogio_();
    repo_.remover_expirados(agora - config_.interval * config_.fator_expiracao);

    AnnounceResponse resp;
    resp.interval = config_.interval;
    resp.min_interval = config_.min_interval;

    // saindo da rede: remove e devolve só as contagens
    if (req.evento == Evento::Stopped) {
        repo_.remover_peer(req.info_hash, req.peer_id);
        contar(repo_.listar_peers(req.info_hash), resp);
        return resp;
    }

    // só o announce de rotina respeita o min_interval
    auto existente = repo_.buscar_peer(req.info_hash, req.peer_id);
    if (existente && req.evento == Evento::Nenhum &&
        agora - existente->ultimo_announce < config_.min_interval) {
        return falha("announce antes do min_interval");
    }

    Peer peer;
    peer.peer_id = req.peer_id;
    peer.ip = req.ip;
    peer.porta = req.porta;
    peer.uploaded = req.uploaded;
    peer.downloaded = req.downloaded;
    peer.left = req.left;
    peer.ultimo_announce = agora;
    repo_.salvar_peer(req.info_hash, peer);

    auto peers = repo_.listar_peers(req.info_hash);
    contar(peers, resp);
    resp.peers = escolher_peers(std::move(peers), req.peer_id, req.numwant);
    return resp;
}

AnnounceResponse Tracker::falha(std::string motivo) const {
    AnnounceResponse resp;
    resp.falha = std::move(motivo);
    return resp;
}

void Tracker::contar(const std::vector<Peer>& peers, AnnounceResponse& resp) const {
    for (const auto& p : peers) {
        if (p.completo()) resp.complete++;
        else resp.incomplete++;
    }
}

std::vector<Peer> Tracker::escolher_peers(std::vector<Peer> candidatos, const std::string& peer_id,
                                          int numwant) {
    // o próprio cliente não entra na lista
    candidatos.erase(std::remove_if(candidatos.begin(), candidatos.end(),
                                    [&](const Peer& p) { return p.peer_id == peer_id; }),
                     candidatos.end());
    // embaralha pra não mandar sempre os mesmos peers
    std::shuffle(candidatos.begin(), candidatos.end(), rng_);

    const auto limite = static_cast<std::size_t>(std::clamp(numwant, 0, config_.numwant_max));
    if (candidatos.size() > limite) candidatos.resize(limite);
    return candidatos;
}

} // namespace tracker
