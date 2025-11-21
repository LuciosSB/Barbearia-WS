class TabelaHash:
    def __init__(self, tamanho=100):
        """
        Inicializa a Tabela Hash.
        :param tamanho: Tamanho do array interno (buckets).
        Quanto maior, menos colisões, mas mais memória usa.
        """
        self.tamanho = tamanho
        # Criamos uma lista de listas. Cada posição é um "bucket".
        # Se houver colisão, adicionamos na lista interna (Encadeamento).
        self.tabela = [[] for _ in range(self.tamanho)]
        self.quantidade = 0

    def _hash(self, chave):
        """
        Função Hash personalizada.
        Converte a string (ex: '2025-11-21-14:00') em um índice numérico.
        """
        soma = 0
        for char in chave:
            # ord(char) pega o código ASCII do caractere
            # Multiplicamos por um primo (31) para espalhar melhor os bits e evitar colisões
            soma = soma * 31 + ord(char)

        # O operador % garante que o índice esteja dentro do tamanho da tabela
        return soma % self.tamanho

    def inserir(self, chave, valor):
        """
        Insere um agendamento.
        :param chave: Data+Horario (String única)
        :param valor: Dados do Cliente (Dicionário ou Objeto)
        :return: True se inseriu, False se já existe (colisão de chave idêntica)
        """
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        # Verifica se a chave já existe nesse bucket (atualização ou erro)
        for i, (k, v) in enumerate(bucket):
            if k == chave:
                # Se já existe, não deixamos sobrescrever sem querer,
                # pois é um agendamento. Retornamos erro.
                return False

        # Se não existe, adiciona no final da lista desse bucket
        bucket.append((chave, valor))
        self.quantidade += 1
        return True

    def buscar(self, chave):
        """
        Busca um agendamento pela chave (Data+Horario).
        :return: O valor (dados do cliente) ou None se não achar.
        """
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        for k, v in bucket:
            if k == chave:
                return v

        return None

    def remover(self, chave):
        """
        Remove um agendamento (caso o cliente cancele).
        """
        indice = self._hash(chave)
        bucket = self.tabela[indice]

        for i, (k, v) in enumerate(bucket):
            if k == chave:
                del bucket[i]
                self.quantidade -= 1
                return True
        return False

    def listar_tudo(self):
        """
        Método auxiliar para vermos todos os agendamentos (para o dono da barbearia).
        :return: Lista de todos os itens.
        """
        todos_itens = []
        for bucket in self.tabela:
            for item in bucket:
                todos_itens.append(item)  # item é uma tupla (chave, valor)
        return todos_itens