import Cliente, os
from servicos.torrent_reader import ler_torrent
from servicos.gerador_torrent import gerar_torrent

# Início do programa
cliente = Cliente.Cliente()

# Exemplo de torrent (adiquirido pela Internet ou localmente)
gerar_torrent("exemplo.txt", "http://tracker.com")
dic_demo = ler_torrent("exemplo.txt.torrent")

print(f"dicionario formado pelo cliente ao ler o .Torrent:\n{dic_demo}\n")

# Inicio das sessoes nos arquivos (upload ou download)
sessao = cliente.adicionar_sessao(dic_demo) # retorna info_hash da sessao


# Primeiro announce
print(f"Primeiro announce (url):\n{cliente.announce(sessao)}\n")
# Omissao do event
print(f"Omissao do campo event nos announces seguintes (url):\n{cliente.announce(sessao)}\n")

# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()

#os.remove("exemplo.txt")
#os.remove("exemplo.txt.torrent")