import Cliente, os
from servicos.torrent_reader import ler_torrent
from servicos.gerador_torrent import gerar_torrent

# Tracker rodando na mesma máquina: ./tracker 6969
TRACKER = "http://127.0.0.1:6969"

# Início do programa
cliente = Cliente.Cliente()

# Exemplo de torrent (adiquirido pela Internet ou localmente)
gerar_torrent("exemplo.txt", TRACKER)
dic_demo = ler_torrent("exemplo.txt.torrent")

print(f"dicionario formado pelo cliente ao ler o .Torrent:\n{dic_demo}\n")

# Inicio das sessoes nos arquivos (upload ou download)
sessao = cliente.instanciar_sessao(dic_demo) # retorna info_hash da sessao


# Primeiro announce
print("=== Primeiro announce ===")
resposta = cliente.announce(sessao) # A Sessao mostra a url antes de enviar
print(f"Resposta do Tracker:\n{resposta}\n")

# Omissao do event
print("=== Omissao do campo event nos announces seguintes ===")
resposta = cliente.announce(sessao)
print(f"Resposta do Tracker:\n{resposta}\n")

# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()

#os.remove("exemplo.txt")
#os.remove("exemplo.txt.torrent")