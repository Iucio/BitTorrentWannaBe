import Cliente, os, time

# python3 cliente_demo.py
# Cliente ligado na rede sem arquivo nenhum. Fica na SALA, então qualquer seeder
# pode escolhê-lo como guardião das partes da chave de um arquivo

tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
chave = os.environ.get("TRACKER_CHAVE", "") # ./tracker cadastrar <nome> mostra a chave

cliente = Cliente.Cliente(chave, tracker)
print(f"[BitTorrentWannaBe] Na rede como {cliente.peer_id.decode('latin1')}. Ctrl+C para sair")

try:
    while True:
        time.sleep(0.25)
except KeyboardInterrupt:
    cliente.shutdown() # Sai da SALA
