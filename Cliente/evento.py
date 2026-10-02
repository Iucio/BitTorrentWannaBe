from enum import StrEnum

# Fica num módulo próprio porque Cliente e Sessao usam, e um importar o outro dá import circular
class Event(StrEnum):
    STARTED = "started" # Início da aplicação (primeiro announce)
    COMPLETED = "completed" # Download completo de um arquivo
    STOPPED = "stopped" # Término da aplicação (ultimo announce)
    # Sessao de donwload
    ACTIVE = "" # Omição do event na url. (Nenum arquivo foi baixado por completo e o cliente não saiu da rede)
    # Sessao de Upload
    SEEDER = "seeder"
