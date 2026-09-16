#pragma once

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace tracker {

using Segundos = std::int64_t;

// Nenhum = announce de rotina (sem event na url)
enum class Evento { Nenhum, Started, Completed, Stopped };

struct AnnounceRequest {
    std::string info_hash; // 20 bytes
    std::string peer_id;   // 20 bytes
    std::string ip;
    std::uint16_t porta = 0;
    std::int64_t uploaded = 0;
    std::int64_t downloaded = 0;
    std::int64_t left = 0;
    Evento evento = Evento::Nenhum;
    int numwant = 50;
};

struct Peer {
    std::string peer_id;
    std::string ip;
    std::uint16_t porta = 0;
    std::int64_t uploaded = 0;
    std::int64_t downloaded = 0;
    std::int64_t left = 0;
    Segundos ultimo_announce = 0;

    bool completo() const { return left == 0; } // seeder
};

struct AnnounceResponse {
    std::optional<std::string> falha; // se preenchido, vira failure_reason
    Segundos interval = 0;
    Segundos min_interval = 0;
    int complete = 0;   // seeders
    int incomplete = 0; // leechers
    std::vector<Peer> peers;
};

} // namespace tracker
