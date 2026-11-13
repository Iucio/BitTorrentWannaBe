"""Painel no terminal do BitTorrentWannaBe.

Uma tela em ASCII que se atualiza sozinha e mostra o estado do cliente:
a sessão, o progresso do download peça a peça, os peers, a velocidade e o
registro de atividade. Usa só a biblioteca padrão do Python e não altera
nenhum outro arquivo do cliente: tudo o que o cliente imprime vira o log
do painel.

As demos já abrem o painel sozinhas (seeder_demo.py, leecher_demo.py e
cliente_demo.py). Ele aparece depois das perguntas iniciais (como a escolha
dos guardiões) e fecha com q ou Ctrl+C; a demo então continua no terminal
normal. PAINEL=0 desliga e volta às mensagens de antes.

Dentro de outro programa:
    import painel
    painel.acompanhar(cliente, sessao, "semear")   # até apertar q
    painel.acompanhar(cliente, sessao, "baixar")   # roda o download e volta ao terminar
    painel.acompanhar(cliente, None, "guardiao")   # cliente sem arquivo, só guardião

Também roda sozinho (de dentro da pasta Cliente):
    python3 painel.py semear [arquivo] [torrent]   compartilha um arquivo
    python3 painel.py baixar [torrent]             baixa um arquivo
Sem os caminhos, usa o vídeo da demonstração.

Variáveis de ambiente:
    TRACKER_URL    endereço do Tracker (padrão http://127.0.0.1:6969)
    TRACKER_CHAVE  chave de acesso dada por ./tracker cadastrar
    NO_COLOR       com qualquer valor, desliga as cores
    PAINEL         0 desliga o painel nas demos

Teclas: [q] sai   [l] liga e desliga o lockdown (se a versão do cliente tiver)
"""

import collections
import contextlib
import os
import re
import shutil
import sys
import threading
import time
from pathlib import Path

import Cliente
import Sessao
from servicos.torrent_reader import ler_torrent

QUADROS_POR_SEGUNDO = 4
LARGURA_MINIMA, LARGURA_MAXIMA = 80, 110

LETREIRO = r"""
 ___ _ _  _____                    _ __      __                   ___
| _ |_) ||_   _|__ _ _ _ _ ___ _ _| |\ \    / /_ _ _ _  _ _  __ _| _ ) ___
| _ \ |  _|| |/ _ \ '_| '_/ -_) ' \  _\ \/\/ / _` | ' \| ' \/ _` | _ \/ -_)
|___/_|\__||_|\___/_| |_| \___|_||_\__|\_/\_/\__,_|_||_|_||_\__,_|___/\___|
""".strip("\n").splitlines()

# ---------------------------------------------------------------------------
# Cores e montagem de linhas
# ---------------------------------------------------------------------------

USAR_COR = "NO_COLOR" not in os.environ
CORES = {
    "borda": "2", "titulo": "1;36", "letreiro": "1;36", "rotulo": "2",
    "valor": "1", "ok": "1;32", "aviso": "1;33", "erro": "1;31",
    "cheio": "32", "vazio": "2", "seeder": "32", "leecher": "36",
    "sistema": "35", "hora": "2",
}


def pintar(texto, cor):
    if not USAR_COR or not cor or not texto:
        return texto
    return f"\x1b[{CORES[cor]}m{texto}\x1b[0m"


def ajustar(pedacos, largura):
    """Junta pedaços (texto, cor) e corta ou completa até `largura` caracteres visíveis."""
    saida, usado = [], 0
    for texto, cor in pedacos:
        if usado >= largura:
            break
        texto = texto[: largura - usado]
        saida.append(pintar(texto, cor))
        usado += len(texto)
    return "".join(saida) + " " * (largura - usado)


def caixa(titulo, linhas, largura, etiqueta=None):
    """Desenha uma caixa com título no topo e, opcionalmente, uma etiqueta à direita."""
    traco = largura - 7 - len(titulo) - (len(etiqueta[0]) + 4 if etiqueta else 0)
    topo = [("+-- ", "borda"), (titulo, "titulo"), (" " + "-" * traco, "borda")]
    if etiqueta:
        topo += [(" [", "borda"), (etiqueta[0], etiqueta[1]), ("] ", "borda")]
    topo.append(("-+", "borda"))
    saida = [ajustar(topo, largura)]
    for linha in linhas:
        saida.append(pintar("| ", "borda") + ajustar(linha, largura - 4) + pintar(" |", "borda"))
    saida.append(pintar("+" + "-" * (largura - 2) + "+", "borda"))
    return saida


def barra(fracao, largura):
    cheio = round(fracao * largura)
    return [("[", "borda"), ("#" * cheio, "cheio"), ("." * (largura - cheio), "vazio"), ("]", "borda")]


def tamanho(nbytes):
    for unidade in ("B", "KB", "MB", "GB"):
        if nbytes < 1024 or unidade == "GB":
            return f"{nbytes:.0f} {unidade}" if unidade == "B" else f"{nbytes:.1f} {unidade}"
        nbytes /= 1024


def relogio(segundos):
    segundos = int(segundos)
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}:{segundos % 60:02d}"


# ---------------------------------------------------------------------------
# Captura do que o cliente imprime
# ---------------------------------------------------------------------------

# Linhas que não interessam no log: a barra de progresso (progressbar2) e o
# letreiro em caixa que o Cliente imprime ao iniciar
IGNORAR = re.compile(r"\d+%|N/A|ETA|Elapsed Time|\(\d+ of \d+\)|^\+-+\+$|^\| BitTorrentWannaBe \|$")


class Registro:
    """Substitui o stdout e o stderr: cada linha impressa vira um evento do log."""

    def __init__(self, tamanho_maximo=300):
        self.linhas = collections.deque(maxlen=tamanho_maximo)  # [hora, texto, vezes]
        self.ouvintes = []
        self._parcial = ""
        self._lock = threading.Lock()

    def write(self, texto):
        novas = []
        with self._lock:
            for parte in re.split(r"(\r|\n)", texto):
                if parte == "\n":
                    linha, self._parcial = self._parcial.strip(), ""
                    if linha and not IGNORAR.search(linha):
                        self._guardar(linha)
                        novas.append(linha)
                elif parte == "\r":
                    self._parcial = ""  # a barra de progresso reescreve a mesma linha
                else:
                    self._parcial += parte
        for linha in novas:
            for ouvinte in self.ouvintes:
                ouvinte(linha)
        return len(texto)

    def _guardar(self, linha):
        # Linhas iguais a menos dos números (ex.: "Mandando peca 12", "Mandando peca 13")
        # viram uma só, com a última versão e quantas vezes apareceu
        hora = time.strftime("%H:%M:%S")
        anterior = self.linhas[-1] if self.linhas else None
        if anterior and re.sub(r"\d+", "#", anterior[1]) == re.sub(r"\d+", "#", linha):
            anterior[0], anterior[1], anterior[2] = hora, linha, anterior[2] + 1
        else:
            self.linhas.append([hora, linha, 1])

    def flush(self):
        pass

    def isatty(self):
        return False

    def ultimas(self, quantidade):
        with self._lock:
            return [tuple(l) for l in list(self.linhas)[-quantidade:]] if quantidade > 0 else []


def cor_do_log(linha):
    texto = linha.lower()
    if "erro" in texto or "corrompid" in texto or "recusou" in texto or "falh" in texto:
        return "erro"
    if "lockdown" in texto or ("choke" in texto and "unchoke" not in texto):
        return "aviso"
    if linha.startswith("[Seeder]"):
        return "seeder"
    if linha.startswith(("[MiniLeecher]", "[GerenciadorDownload]", "[Orquestrador]")):
        return "leecher"
    if linha.startswith("[BitTorrentWannaBe]"):
        return "sistema"
    return None


# ---------------------------------------------------------------------------
# Acompanhamento do download sem mexer no código do cliente
# ---------------------------------------------------------------------------

class GerenciadorRastreado(Sessao.GerenciadorDownload):
    """Igual ao GerenciadorDownload, mas guarda cada instância para o painel ler o progresso."""

    instancias = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        GerenciadorRastreado.instancias.append(self)


# A Sessao cria o gerenciador dentro de download(); trocando a classe no módulo,
# o painel consegue ver as peças baixadas sem alterar o Sessao.py
Sessao.GerenciadorDownload = GerenciadorRastreado


def gerenciador_da(sessao):
    for gerenciador in reversed(GerenciadorRastreado.instancias):
        if gerenciador.info_hash == sessao.info_hash:
            return gerenciador
    return None


# ---------------------------------------------------------------------------
# Teclado sem precisar apertar Enter (Linux, macOS e Windows)
# ---------------------------------------------------------------------------

class Teclado:
    def __enter__(self):
        self._antigo = None
        if os.name != "nt" and sys.stdin.isatty():
            import termios
            import tty
            self._fd = sys.stdin.fileno()
            self._antigo = termios.tcgetattr(self._fd)
            tty.setcbreak(self._fd)
        return self

    def ler(self):
        if os.name == "nt":
            import msvcrt
            return msvcrt.getwch() if msvcrt.kbhit() else None
        if self._antigo is None:
            return None
        import select
        if select.select([sys.stdin], [], [], 0)[0]:
            return os.read(self._fd, 1).decode(errors="ignore")
        return None

    def __exit__(self, *erro):
        if self._antigo is not None:
            import termios
            termios.tcsetattr(self._fd, termios.TCSADRAIN, self._antigo)


# ---------------------------------------------------------------------------
# O painel
# ---------------------------------------------------------------------------

class Painel:
    def __init__(self, modo, tracker, chave, registro, saida):
        self.modo = modo  # "semear" ou "baixar"
        self.tracker = tracker
        self.chave = chave
        self.registro = registro
        self.saida = saida
        self.cliente = None
        self.sessao = None
        self.thread_download = None
        self.falha = None
        self.aviso = ""
        self.inicio = time.time()
        self.amostras = collections.deque(maxlen=4 * QUADROS_POR_SEGUNDO)
        self.concluido_em = None
        self.peers_conectados = {}  # quem está baixando de nós: "ip:porta" -> desde quando
        registro.ouvintes.append(self._ouvir)

    # Os prints do Cliente dizem quando um peer conecta e desconecta no lado do seeder
    def _ouvir(self, linha):
        conectou = re.search(r"Peer conectou: (\S+)", linha)
        desconectou = re.search(r"Peer desconectou: (\S+)", linha)
        if conectou:
            self.peers_conectados[conectou.group(1)] = time.time()
        elif desconectou:
            self.peers_conectados.pop(desconectou.group(1), None)

    # -- estado -----------------------------------------------------------

    def _pecas_que_tem(self):
        if self.sessao is None:
            return set()
        if self.modo == "semear":
            return set(self.sessao.pecas)
        gerenciador = gerenciador_da(self.sessao)
        try:
            with gerenciador.lock_pecas_baixadas:
                return set(gerenciador.pecas_baixadas)
        except AttributeError:  # ainda sem gerenciador, ou outra versão dele
            return set()

    def _tamanho_peca(self, indice):
        info = self.sessao.torrent["info"]
        return min(info["piece length"], info["length"] - indice * info["piece length"])

    def _estado(self, completo):
        if self.falha:
            return ("FALHOU", "erro")
        if getattr(self.sessao, "_lockdown", False) or getattr(self.cliente, "lockdown", False):
            return ("LOCKDOWN", "aviso")
        if self.modo == "guardiao":
            return ("NA REDE", "ok")
        if self.sessao is None:
            return ("CONECTANDO", "aviso")
        if self.modo == "semear":
            return ("SEMEANDO", "ok")
        if completo:
            return ("CONCLUIDO", "ok")
        if self.thread_download and not self.thread_download.is_alive():
            return ("PARADO", "erro")
        return ("BAIXANDO", "leecher")

    def _velocidades(self, baixados, enviados):
        agora = time.time()
        self.amostras.append((agora, baixados, enviados))
        t0, b0, e0 = self.amostras[0]
        intervalo = max(agora - t0, 1e-6)
        return (baixados - b0) / intervalo, (enviados - e0) / intervalo

    # -- partes da tela ---------------------------------------------------

    def _cabecalho(self, largura, altura):
        if largura >= 79 and altura >= 36:
            margem = " " * ((largura - len(LETREIRO[-1])) // 2)
            linhas = [ajustar([(margem + l, "letreiro")], largura) for l in LETREIRO]
            subtitulo = "compartilhamento de arquivos em rede fechada  -  Tracker + P2P"
            linhas.append(ajustar([(subtitulo.center(largura), "rotulo")], largura))
            return linhas
        return [ajustar([(" BitTorrentWannaBe ", "letreiro"), ("- Tracker + P2P", "rotulo")], largura)]

    def _caixa_cliente(self, largura):
        if self.cliente:
            peer_id = self.cliente.peer_id.decode("latin1")
            porta = str(self.cliente.porta)
        else:
            peer_id, porta = "...", "..."
        chave = "cadastrada" if self.chave else "sem chave"
        coluna = (largura - 4) // 2

        def par(rotulo, valor, cor="valor"):
            return [(f"{rotulo:<10}", "rotulo"), (valor, cor)]

        def linha(esquerda, direita):
            texto_esquerda = "".join(t for t, _ in esquerda)
            return esquerda + [(" " * max(1, coluna - len(texto_esquerda)), None)] + direita

        linhas = [
            linha(par("peer_id", peer_id), par("porta", porta)),
            linha(par("tracker", self.tracker), par("chave", chave, "ok" if self.chave else "aviso")),
            linha(par("no ar ha", relogio(time.time() - self.inicio)), par("modo", self.modo)),
        ]
        guardadas = self._partes_guardadas()
        if guardadas is not None and self.modo != "guardiao":
            linhas.append(par("guardiao", f"{len(guardadas)} parte(s) de chave guardada(s)"))
        return caixa("cliente", linhas, largura)

    def _partes_guardadas(self):
        """Partes da chave (Shamir) que outros seeders confiaram a este cliente; None se não é guardião."""
        guardiao = getattr(self.cliente, "guardiao", None)
        if guardiao is None:
            return None
        with guardiao.lock:
            return dict(guardiao.partes)

    def _caixa_guardiao(self, largura):
        guardadas = self._partes_guardadas() or {}
        linhas = [[("na SALA: qualquer seeder pode escolher este cliente para guardar uma parte da chave", "rotulo")],
                  [],
                  [("partes guardadas ", "rotulo"), (str(len(guardadas)), "valor")]]
        for info_hash, (x, _) in list(guardadas.items())[:6]:  # o y é o segredo: não aparece
            x = str(x) if len(str(x)) <= 12 else str(x)[:12] + "..."
            linhas.append([("  * ", "ok"), (f"arquivo {info_hash.hex()[:8]}", "valor"), (f"   parte x = {x}", "rotulo")])
        if len(guardadas) > 6:
            linhas.append([(f"  ... e mais {len(guardadas) - 6}", "rotulo")])
        return caixa("guardiao", linhas, largura, self._estado(False))

    def _caixa_sessao(self, largura, linhas_livres):
        interno = largura - 4
        if self.modo == "guardiao":
            return self._caixa_guardiao(largura)
        if self.sessao is None:
            texto = f"falha: {self.falha}" if self.falha else f"anunciando no tracker {self.tracker} ..."
            return caixa("sessao", [[(texto, "erro" if self.falha else "aviso")]], largura,
                         self._estado(False))

        info = self.sessao.torrent["info"]
        total = self.sessao.qtd_pecas
        tem = self._pecas_que_tem()
        bytes_tem = sum(self._tamanho_peca(i) for i in tem)
        completo = len(tem) == total
        baixa, envia = self._velocidades(bytes_tem if self.modo == "baixar" else 0,
                                         getattr(self.sessao, "uploaded", 0))
        fracao = len(tem) / total if total else 0
        linhas = []

        resumo = f" {fracao * 100:5.1f}%  {len(tem)}/{total} pecas"
        linhas.append(barra(fracao, interno - len(resumo) - 2) + [(resumo, "valor")])

        if self.modo == "baixar":
            faltam = info["length"] - bytes_tem
            if completo:
                self.concluido_em = self.concluido_em or time.time()
                tempo = [("   levou ", "rotulo"), (relogio(self.concluido_em - self.inicio), "ok")]
            else:
                eta = relogio(faltam / baixa) if baixa > 0 else "--:--:--"
                tempo = [("   termina em ", "rotulo"), (eta, "valor")]
            linhas.append([("baixado ", "rotulo"), (f"{tamanho(bytes_tem)} de {tamanho(info['length'])}", "valor"),
                           ("   velocidade ", "rotulo"), (f"{tamanho(baixa)}/s", "leecher")] + tempo)
        else:
            linhas.append([("arquivo ", "rotulo"), (tamanho(info["length"]), "valor"),
                           ("   enviado ", "rotulo"), (tamanho(getattr(self.sessao, "uploaded", 0)), "valor"),
                           ("   velocidade ", "rotulo"), (f"{tamanho(envia)}/s", "seeder")])

        linhas.append([("tracker ", "rotulo"),
                       (f"{self.sessao.complete} seeder(s), {self.sessao.incomplete} leecher(s), "
                        f"{len(set(self.sessao.swarm))} peer(s) na lista", "valor")])
        if "shamir" in info:
            linhas.append([("cifrado ", "rotulo"),
                           (f"AES-GCM, chave dividida em {info['shamir']['n']} partes "
                            f"(abre com {info['shamir']['k']})", "aviso")])
        linhas.append([])

        # Mapa de peças: cada caractere é uma peça (ou um grupo, se o arquivo for grande)
        largura_mapa = interno - 2
        linhas_mapa = max(1, min(6, linhas_livres - 8))
        celulas = min(total, largura_mapa * linhas_mapa)
        por_celula = total / celulas if celulas else 1
        mapa = []
        for c in range(celulas):
            inicio, fim = int(c * por_celula), max(int((c + 1) * por_celula), int(c * por_celula) + 1)
            quantas = sum(1 for i in range(inicio, fim) if i in tem)
            mapa.append("#" if quantas == fim - inicio else "+" if quantas else ".")
        legenda = "mapa de pecas" + (f" (1 caractere = {por_celula:.0f} pecas)" if por_celula > 1.5 else "")
        linhas.append([(legenda, "rotulo")])
        for i in range(0, len(mapa), largura_mapa):
            linhas.append(self._pintar_mapa("".join(mapa[i:i + largura_mapa])))
        linhas.append([])

        linhas += self._linhas_peers(interno)

        if self.modo == "baixar" and completo:
            gerenciador = gerenciador_da(self.sessao)
            destino = str(Path(getattr(gerenciador, "caminho", "?")).resolve())
            espaco = interno - len("download concluido: ")
            if len(destino) > espaco:
                destino = "..." + destino[-(espaco - 3):]
            linhas.append([])
            linhas.append([("download concluido: ", "ok"), (destino, "valor")])

        return caixa(info["name"], linhas, largura, self._estado(completo))

    @staticmethod
    def _pintar_mapa(trecho):
        pedacos = [("  ", None)]
        for caractere in trecho:
            cor = {"#": "cheio", "+": "aviso", ".": "vazio"}[caractere]
            if pedacos and pedacos[-1][1] == cor:
                pedacos[-1] = (pedacos[-1][0] + caractere, cor)
            else:
                pedacos.append((caractere, cor))
        return pedacos

    def _linhas_peers(self, interno):
        linhas = []
        if self.modo == "baixar":
            gerenciador = gerenciador_da(self.sessao)
            peers = {}
            if gerenciador:
                try:
                    with gerenciador.lock_mini_leechers_ativos:
                        ativos = list(gerenciador.mini_leechers_ativos)
                    with gerenciador.lock_mapa_peca_peers:
                        for donos in gerenciador.mapa_peca_peers.values():
                            for peer in donos:
                                peers[peer] = peers.get(peer, 0) + 1
                    peers = {p: peers.get(p, 0) for p in ativos}
                except AttributeError:  # outra versão do GerenciadorDownload
                    pass
            linhas.append([("baixando de ", "rotulo"), (f"{len(peers)} peer(s)", "valor")])
            for (ip, porta), quantas in list(peers.items())[:4]:
                linhas.append([("  > ", "leecher"), (f"{ip}:{porta}".ljust(24), "valor"),
                               (f"tem {quantas} pecas", "rotulo")])
        else:
            agora = time.time()
            peers = list(self.peers_conectados.items())
            linhas.append([("enviando para ", "rotulo"), (f"{len(peers)} peer(s)", "valor")])
            for endereco, desde in peers[:4]:
                linhas.append([("  < ", "seeder"), (endereco.ljust(24), "valor"),
                               (f"conectado ha {relogio(agora - desde)}", "rotulo")])
        if len(peers) > 4:
            linhas.append([(f"  ... e mais {len(peers) - 4}", "rotulo")])
        return linhas

    def _caixa_log(self, largura, linhas_disponiveis):
        quantidade = max(1, linhas_disponiveis - 2)
        linhas = []
        for hora, texto, vezes in self.registro.ultimas(quantidade):
            repeticao = [(f"  (x{vezes})", "rotulo")] if vezes > 1 else []
            linhas.append([(hora + " ", "hora"), (texto, cor_do_log(texto))] + repeticao)
        while len(linhas) < quantidade:
            linhas.insert(0, [])
        return caixa("atividade", linhas, largura)

    def _rodape(self, largura):
        teclas = [(" [q]", "valor"), (" sair   ", "rotulo")]
        if self.sessao is not None and hasattr(self.sessao, "lockdown"):
            teclas += [("[l]", "valor"), (" lockdown   ", "rotulo")]
        usado = sum(len(t) for t, _ in teclas)
        return ajustar(teclas + [(self.aviso.rjust(largura - usado - 1), "aviso")], largura)

    # -- desenho ----------------------------------------------------------

    def quadro(self):
        colunas, altura = shutil.get_terminal_size((100, 40))
        largura = max(LARGURA_MINIMA, min(LARGURA_MAXIMA, colunas))
        topo = self._cabecalho(largura, altura) + self._caixa_cliente(largura)
        livres = altura - len(topo) - 1
        sessao = self._caixa_sessao(largura, livres - 6)
        log = self._caixa_log(largura, altura - len(topo) - len(sessao) - 1)
        linhas = topo + sessao + log + [self._rodape(largura)]
        linhas = linhas[:altura]
        return "\x1b[H" + "\x1b[K\n".join(linhas) + "\x1b[K\x1b[J"

    def desenhar(self):
        self.saida.write(self.quadro())
        self.saida.flush()

    # -- teclas -----------------------------------------------------------

    def tecla(self, caractere):
        if caractere in ("q", "Q"):
            return False
        if caractere in ("l", "L") and self.sessao is not None:
            if not hasattr(self.sessao, "lockdown"):
                self.aviso = "esta versao do cliente ainda nao tem lockdown"
            else:
                ligar = not getattr(self.sessao, "_lockdown", False)
                self.sessao.lockdown(ligar)
                self.aviso = "lockdown ligado: novos pedidos recebem choke" if ligar else "lockdown desligado"
        return True


# ---------------------------------------------------------------------------
# Programa
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _tela(painel):
    """Enquanto o painel está aberto, o que o cliente imprime vai para o log e o
    terminal usa a tela alternativa. Ao sair, tudo volta como estava."""
    if os.name == "nt":
        os.system("")  # liga as sequências de cor e cursor no console do Windows
    antigos = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = painel.registro
    painel.saida.write("\x1b[?1049h\x1b[?25l")  # tela alternativa e cursor escondido
    try:
        with Teclado() as teclado:
            yield teclado
    finally:
        sys.stdout, sys.stderr = antigos
        painel.saida.write("\x1b[?25h\x1b[?1049l")
        painel.saida.flush()


def _laco(painel, teclado, voltar_ao_concluir=False):
    """Redesenha e lê o teclado. False se o usuário saiu (q ou Ctrl+C);
    True se o download terminou (só com voltar_ao_concluir)."""
    concluido_em = None
    try:
        while True:
            painel.desenhar()
            fim = time.time() + 1 / QUADROS_POR_SEGUNDO
            while time.time() < fim:
                caractere = teclado.ler()
                if caractere and not painel.tecla(caractere):
                    return False
                time.sleep(0.02)
            terminou = painel.thread_download is not None and not painel.thread_download.is_alive()
            if voltar_ao_concluir and terminou:
                concluido_em = concluido_em or time.time()
                painel.aviso = "download terminado, continuando..."
                if time.time() - concluido_em > 2:  # deixa ver o 100% antes de fechar
                    return True
    except KeyboardInterrupt:
        return False


def _desligado():
    return os.environ.get("PAINEL") == "0" or not sys.stdout.isatty()


def acompanhar(cliente, sessao=None, modo="semear"):
    """Mostra o painel enquanto o cliente trabalha e devolve o controle a quem chamou.

    modo "semear":   fica aberto até apertar q ou Ctrl+C.
    modo "baixar":   roda sessao.download() e fecha sozinho quando o download termina.
    modo "guardiao": cliente sem arquivo, guardando partes da chave; fica até q ou Ctrl+C.

    Retorna True se o download terminou (no modo baixar) e False se o usuário saiu.
    Não chama cliente.shutdown(): isso continua com quem chamou.
    Com PAINEL=0 (ou sem terminal), faz o mesmo de antes, sem desenhar nada.
    """
    if _desligado():
        if modo == "baixar":
            sessao.download()
            return True
        try:
            while True:
                time.sleep(0.25)
        except KeyboardInterrupt:
            return False

    tracker = getattr(sessao, "tracker", None) or getattr(getattr(cliente, "guardiao", None), "tracker", "") or ""
    painel = Painel(modo, tracker, getattr(cliente, "chave", ""), Registro(), sys.stdout)
    painel.cliente, painel.sessao = cliente, sessao
    with _tela(painel) as teclado:
        if modo == "baixar":
            painel.thread_download = threading.Thread(target=sessao.download, daemon=True)
            painel.thread_download.start()
        resultado = _laco(painel, teclado, voltar_ao_concluir=(modo == "baixar"))
    if modo == "baixar":
        concluiu = len(painel._pecas_que_tem()) == sessao.qtd_pecas
        print("[BitTorrentWannaBe] download concluido" if concluiu else "[BitTorrentWannaBe] download interrompido")
        return concluiu
    return resultado


# ---------------------------------------------------------------------------
# Rodando sozinho: python3 painel.py semear|baixar
# ---------------------------------------------------------------------------

def criar_cliente(chave):
    try:
        return Cliente.Cliente(chave)
    except TypeError:  # versões do Cliente sem chave de acesso
        return Cliente.Cliente()


def arquivos_dos_argumentos(argumentos):
    demo = Path(__file__).resolve().parent.parent / "Arquivo demo"
    modo = argumentos[0]
    if modo == "semear":
        arquivo = Path(argumentos[1]) if len(argumentos) > 1 else demo / "spyxfamily_op.mp4"
        torrent = Path(argumentos[2]) if len(argumentos) > 2 else arquivo.with_name(arquivo.name + ".torrent")
        return modo, arquivo, torrent
    torrent = Path(argumentos[1]) if len(argumentos) > 1 else demo / "spyxfamily_op.mp4.torrent"
    return modo, None, torrent


def main():
    argumentos = sys.argv[1:]
    if not argumentos or argumentos[0] not in ("semear", "baixar"):
        print(__doc__)
        sys.exit(1)
    modo, arquivo, caminho_torrent = arquivos_dos_argumentos(argumentos)
    for caminho in filter(None, (arquivo, caminho_torrent)):
        if not caminho.exists():
            sys.exit(f"arquivo nao encontrado: {caminho}")

    tracker = os.environ.get("TRACKER_URL", "http://127.0.0.1:6969")
    chave = os.environ.get("TRACKER_CHAVE", "")
    torrent = ler_torrent(caminho_torrent)
    painel = Painel(modo, tracker, chave, Registro(), sys.stdout)

    with _tela(painel) as teclado:
        painel.desenhar()
        try:
            painel.cliente = criar_cliente(chave)
            painel.desenhar()
            painel.sessao = painel.cliente.instanciar_sessao(torrent, arquivo, tracker)
        except SystemExit as erro:  # o Cliente encerra quando o Tracker recusa
            painel.falha = str(erro.code)
        except Exception as erro:
            painel.falha = f"{type(erro).__name__}: {erro}"

        if painel.sessao is not None and modo == "baixar":
            painel.thread_download = threading.Thread(target=painel.sessao.download, daemon=True)
            painel.thread_download.start()
        if painel.falha:
            painel.aviso = "aperte q para sair"
        _laco(painel, teclado)

        if painel.cliente is not None and painel.sessao is not None:
            painel.aviso = "desligando: avisando o tracker..."
            painel.desenhar()
            try:
                painel.cliente.shutdown()  # announce com event=stopped
            except Exception:
                pass

    print(f"BitTorrentWannaBe: {painel.falha}" if painel.falha else "BitTorrentWannaBe: sessao encerrada.")


if __name__ == "__main__":
    main()
