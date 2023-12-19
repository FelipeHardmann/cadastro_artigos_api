from passlib.context import CryptContext


CRIPTO = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verificar_senha(senha: str, hash_senha: str) -> bool:
    '''
        Função para verificar se a senha está
        correta comparando a senhaem texto puro,
        informada pelo usuário, e o hash da senha
        que estará salvo no banco de dados.
    '''
    return CRIPTO.verify(senha, hash_senha)


def gerar_hash_senha(senha: str) -> str:
    '''
        Função que gera e retorna o has da senha
    '''
    return CRIPTO.hash(senha)
