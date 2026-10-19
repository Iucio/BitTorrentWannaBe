#pragma once

#include <map>
#include <optional>
#include <string>
#include <vector>

#include "modelos.hpp"

namespace tracker {

// Acesso ao banco. Implementações:
//   RepositorioMemoria (abaixo) - usado nos testes
//   RepositorioSQLite (repositorio_sqlite.hpp) - usado pelo executável
class Repositorio {
public:
    virtual ~Repositorio() = default;

    virtual std::optional<Peer> buscar_peer(const std::string& info_hash,
                                            const std::string& peer_id) const = 0;
    virtual void salvar_peer(const std::string& info_hash, const Peer& peer) = 0; // insere ou atualiza
    virtual void remover_peer(const std::string& info_hash, const std::string& peer_id) = 0;
    virtual std::vector<Peer> listar_peers(const std::string& info_hash) const = 0;
    virtual void remover_expirados(Segundos limite) = 0; // ultimo_announce < limite

    // Clientes cadastrados pelo admin
    virtual std::int64_t cadastrar_cliente(const std::string& nome, const std::string& chave,
                                           Segundos criado_em) = 0; // devolve o id
};

class RepositorioMemoria : public Repositorio {
public:
    std::optional<Peer> buscar_peer(const std::string& info_hash,
                                    const std::string& peer_id) const override;
    void salvar_peer(const std::string& info_hash, const Peer& peer) override;
    void remover_peer(const std::string& info_hash, const std::string& peer_id) override;
    std::vector<Peer> listar_peers(const std::string& info_hash) const override;
    void remover_expirados(Segundos limite) override;

    std::int64_t cadastrar_cliente(const std::string& nome, const std::string& chave,
                                   Segundos criado_em) override;

private:
    std::map<std::string, std::map<std::string, Peer>> swarms_; // info_hash -> peer_id -> Peer
    std::vector<Cliente> clientes_;                              // id = posição + 1
};

} // namespace tracker
