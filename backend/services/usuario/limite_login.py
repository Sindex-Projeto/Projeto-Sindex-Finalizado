import threading
import time
from collections import defaultdict, deque

# Limite de erros de senha (15 minutos)
MAX_FALHAS_POR_CONTA = 5
MAX_FALHAS_POR_IP = 20
JANELA_SEGUNDOS = 15 * 60

# Erros recentes, guardados na memória do servidor
_falhas = defaultdict(deque)
_trava = threading.Lock()


def _chaves(email, ip):
    return (f"conta|{ip}|{email}", MAX_FALHAS_POR_CONTA), (f"ip|{ip}", MAX_FALHAS_POR_IP)


def _podar(fila, agora):
    while fila and agora - fila[0] > JANELA_SEGUNDOS:
        fila.popleft()


# Quanto tempo falta para poder tentar de novo (0 = liberado)
def segundos_de_espera(email, ip, agora=None):
    agora = time.time() if agora is None else agora
    espera = 0

    with _trava:
        for chave, maximo in _chaves(email, ip):
            fila = _falhas[chave]
            _podar(fila, agora)

            if len(fila) >= maximo:
                libera_em = fila[0] + JANELA_SEGUNDOS
                espera = max(espera, int(libera_em - agora) + 1)

    return espera


# Anota um erro de senha
def registrar_falha(email, ip, agora=None):
    agora = time.time() if agora is None else agora

    with _trava:
        for chave, _maximo in _chaves(email, ip):
            _falhas[chave].append(agora)


# Zera os erros depois de um login certo
def limpar_conta(email, ip):
    with _trava:
        _falhas.pop(_chaves(email, ip)[0][0], None)


# Zera tudo (usado nos testes)
def reiniciar():
    with _trava:
        _falhas.clear()
