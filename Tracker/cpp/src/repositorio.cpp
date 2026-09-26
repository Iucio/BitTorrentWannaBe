#include "repositorio.hpp"

namespace tracker {

std::optional<Peer> RepositorioMemoria::buscar_peer(const std::string& info_hash,
                                                    const std::string& peer_id) const {
    auto swarm = swarms_.find(info_hash);
    if (swarm == swarms_.end()) return std::nullopt;
    auto peer = swarm->second.find(peer_id);
    if (peer == swarm->second.end()) return std::nullopt;
    return peer->second;
}

void RepositorioMemoria::salvar_peer(const std::string& info_hash, const Peer& peer) {
    swarms_[info_hash][peer.peer_id] = peer;
}

void RepositorioMemoria::remover_peer(const std::string& info_hash, const std::string& peer_id) {
    auto swarm = swarms_.find(info_hash);
    if (swarm == swarms_.end()) return;
    swarm->second.erase(peer_id);
    if (swarm->second.empty()) swarms_.erase(swarm);
}

std::vector<Peer> RepositorioMemoria::listar_peers(const std::string& info_hash) const {
    std::vector<Peer> peers;
    auto swarm = swarms_.find(info_hash);
    if (swarm == swarms_.end()) return peers;
    for (const auto& [_, peer] : swarm->second) peers.push_back(peer);
    return peers;
}

void RepositorioMemoria::remover_expirados(Segundos limite) {
    for (auto swarm = swarms_.begin(); swarm != swarms_.end();) {
        auto& peers = swarm->second;
        for (auto peer = peers.begin(); peer != peers.end();) {
            if (peer->second.ultimo_announce < limite) peer = peers.erase(peer);
            else ++peer;
        }
        if (peers.empty()) swarm = swarms_.erase(swarm);
        else ++swarm;
    }
}

} // namespace tracker
