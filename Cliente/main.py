import Cliente

# Início de um main. v0

dic_demo = {"announce":"11.23.54.232", "info": {"name": "exemplo.txt", "piece": "abcdefjk", "piece length": 262144}, "private": 1}
dic_demo2 = {"announce":"11.23.54.232", "info": {"name": "exemplo2.txt", "piece": "abcdefjk", "piece length": 262144}, "private": 1}

cliente = Cliente.Cliente()
sessao = cliente.adicionar_sessao(dic_demo) # Vou fazer alguma coisa com esse arquivo (upload ou download)
sessao2 = cliente.adicionar_sessao(dic_demo2)

print(cliente.get_sessoes())