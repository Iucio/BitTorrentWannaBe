#pragma once

#include <functional>
#include <random>

#include "modelos.hpp"
#include "repositorio.hpp"

namespace tracker {

struct Config {
    Segundos interval = 1800;    // 30 min
    Segundos min_interval = 900; // 15 min
    int fator_expiracao = 2;     // sem announce há interval * fator => remove
    int numwant_max = 50;        // teto de peers por resposta
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
    std::vector<Peer> escolher_peers(std::vector<Peer> candidatos, const std::string& peer_id,
                                     int numwant);

    Repositorio& repo_;
    Config config_;
    std::function<Segundos()> relogio_;
    std::mt19937 rng_;
};

} // namespace tracker
