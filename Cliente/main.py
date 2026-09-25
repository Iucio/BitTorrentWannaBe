import Cliente
from servicos.parser import bencode

# Início de um main. v0.1

#dic_demo = {"announce":"11.23.54.232:80", "info": {"name": "exemplo.txt", "piece": "abcdefjk", "piece length": 262144}, "private": 1}
#dic_demo2 = {"announce":"11.23.54.232:80", "info": {"name": "exemplo2.txt", "piece": "abcdefjk", "piece length": 262144}, "private": 1}

# Início do programa
cliente = Cliente.Cliente()

# Exemplo de torrents (adiquiridos pela Internet ou localmente)
torrent = "d8:announce28:http://11.23.54.232:80/teste4:infod4:name11:exemplo.txt5:piece8:abcdefjk12:piece lengthi262144ee7:privatei1ee"
torrent2 = "d8:announce28:http://11.23.54.232:80/teste4:infod4:name12:exemplo2.txt5:piece8:abcdefjk12:piece lengthi262144ee7:privatei1ee"


dic_demo = bencode(torrent)
dic_demo2 = bencode(torrent2)

print(f"dicionario formado pelo cliente ao ler o .Torrent:\n{dic_demo}\n")

# Inicio das sessoes nos arquivos (upload ou download)
sessao = cliente.adicionar_sessao(dic_demo) 
sessao2 = cliente.adicionar_sessao(dic_demo2)


# Primeiro announce
print(f"Primeiro announce (url):\n{cliente.announce(sessao)}\n")
# Omissao do event
print(f"Omissao do campo event nos announces seguintes (url):\n{cliente.announce(sessao)}\n")

print(f"Outra sessao com outro info_hash (url): \n{cliente.announce(sessao2)}")
# Desligamento da aplicação
# Envia announces contendo o campo event=stopped para cada sessao (info_hash) 
cliente.shutdown()