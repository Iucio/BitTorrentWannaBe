#include "json.hpp"

#include <cstdio>
#include <sstream>

namespace tracker {

std::string json_string(const std::string& s) {
    std::string out = "\"";
    for (unsigned char c : s) {
        switch (c) {
        case '"': out += "\\\""; break;
        case '\\': out += "\\\\"; break;
        case '\n': out += "\\n"; break;
        case '\r': out += "\\r"; break;
        case '\t': out += "\\t"; break;
        default:
            if (c < 0x20 || c >= 0x7f) {
                char buf[7];
                std::snprintf(buf, sizeof buf, "\\u%04x", c);
                out += buf;
            } else {
                out += static_cast<char>(c);
            }
        }
    }
    return out + "\"";
}

std::string resposta_para_json(const AnnounceResponse& resp) {
    std::ostringstream out;
    if (resp.falha) {
        out << "{\"failure_reason\":" << json_string(*resp.falha) << "}";
        return out.str();
    }

    out << "{\"interval\":" << resp.interval
        << ",\"min_interval\":" << resp.min_interval
        << ",\"complete\":" << resp.complete
        << ",\"incomplete\":" << resp.incomplete
        << ",\"peers\":[";
    for (std::size_t i = 0; i < resp.peers.size(); i++) {
        const auto& p = resp.peers[i];
        if (i) out << ",";
        out << "{\"peer_id\":" << json_string(p.peer_id)
            << ",\"ip\":" << json_string(p.ip)
            << ",\"port\":" << p.porta << "}";
    }
    out << "]}";
    return out.str();
}

} // namespace tracker
