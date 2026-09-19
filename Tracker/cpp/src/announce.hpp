#pragma once

#include <functional>

#include "modelos.hpp"
#include "repositorio.hpp"

namespace tracker {

struct Config {
    Segundos interval = 1800;    // 30 min
    Segundos min_interval = 900; // 15 min
};

Segundos relogio_sistema();

class Tracker {
public:
    explicit Tracker(Repositorio& repo, Config config = {},
                     std::function<Segundos()> relogio = relogio_sistema);

    AnnounceResponse announce(const AnnounceRequest& req);

private:
    AnnounceResponse falha(std::string motivo) const;
    void contar(const std::vector<Peer>& peers, AnnounceResponse& resp) const;
    std::vector<Peer> escolher_peers(std::vector<Peer> candidatos,
                                     const std::string& peer_id) const;

    Repositorio& repo_;
    Config config_;
    std::function<Segundos()> relogio_;
};

} // namespace tracker
