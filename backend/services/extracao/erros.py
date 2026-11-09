# Falha ao ler o conteúdo
class ErroExtracao(Exception):
    pass


# Tipo de arquivo sem leitura de texto (não é erro)
class TipoSemSuporte(Exception):
    pass
