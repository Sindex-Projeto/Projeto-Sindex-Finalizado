import sqlite3
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

from repository.texto import sem_acento

# Banco de dados
db = SQLAlchemy()


# Datas
def agora():
    return datetime.now(timezone.utc)


def para_iso(data):
    if data is None:
        return None
    if data.tzinfo is None:
        return data.isoformat() + "Z"
    return data.isoformat()


# Prepara o SQLite: liga as chaves estrangeiras e cria a função sem_acento() usada nas buscas
@event.listens_for(Engine, "connect")
def ativar_chaves_estrangeiras(conexao, _registro):
    if isinstance(conexao, sqlite3.Connection):
        conexao.create_function("sem_acento", 1, sem_acento, deterministic=True)
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
