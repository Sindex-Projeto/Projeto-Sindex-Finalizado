import unicodedata


# Tira acentos e maiúsculas ("Matemática" vira "matematica")
def sem_acento(texto):
    if texto is None:
        return None

    decomposto = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn").lower()


# Faz %, _ e \ valerem como letras comuns dentro de um LIKE
def escapar_like(texto):
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
