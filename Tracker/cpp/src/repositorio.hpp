#pragma once

#include <map>
#include <optional>
#include <string>
#include <vector>

#include "modelos.hpp"

namespace tracker {

// Acesso ao banco. Hoje em memória, entra no de Carlos lá dps
// dá pra trocar por SQLite (sql/schema.sql)
class Repositorio {
public:
    virtual ~Repositorio() = default;

    virtual std::optional<Peer> buscar_peer(const std::string& info_hash,
                                            const std::string& peer_id) const = 0;
    virtual void salvar_peer(const std::string& info_hash, const Peer& peer) = 0; // insere ou atualiza
    virtual void remover_peer(const std::string& info_hash, const std::string& peer_id) = 0;
    virtual std::vector<Peer> listar_peers(const std::string& info_hash) const = 0;
    virtual void remover_expirados(Segundos limite) = 0; // ultimo_announce < limite
};

class RepositorioMemoria : public Repositorio {
public:
    std::optional<Peer> buscar_peer(const std::string& info_hash,
                                    const std::string& peer_id) const override;
    void salvar_peer(const std::string& info_hash, const Peer& peer) override;
    void remover_peer(const std::string& info_hash, const std::string& peer_id) override;
    std::vector<Peer> listar_peers(const std::string& info_hash) const override;
    void remover_expirados(Segundos limite) override;

private:
    std::map<std::string, std::map<std::string, Peer>> swarms_; // info_hash -> peer_id -> Peer
};

} // namespace tracker
