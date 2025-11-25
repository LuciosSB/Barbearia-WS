class TabelaHash:
    def __init__(self, tamanho=100):
        self.tamanho = tamanho
        self.tabela = [[] for _ in range(self.tamanho)]
        self.quantidade = 0

    def _hash(self, chave):
        soma = 0
        for char in chave:
            soma = soma * 31 + ord(char)

        return soma % self.tamanho

    def inserir(self, chave, valor):
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        for i, (k, v) in enumerate(bucket):
            if k == chave:
                return False

        bucket.append((chave, valor))
        self.quantidade += 1
        return True

    def buscar(self, chave):
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        for k, v in bucket:
            if k == chave:
                return v

        return None

    def remover(self, chave):
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        for i, (k, v) in enumerate(bucket):
            if k == chave:
                del bucket[i]
                self.quantidade -= 1
                return True
        return False

    def listar_tudo(self):
        todos_itens = []
        for bucket in self.tabela:
            for item in bucket:
                todos_itens.append(item)  # item é uma tupla (chave, valor)
        return todos_itens