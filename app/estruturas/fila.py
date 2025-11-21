class No:
    """
    Classe auxiliar que representa um elemento da fila.
    """

    def __init__(self, dado):
        self.dado = dado  # Onde guardamos os dados do cliente (nome, tel)
        self.proximo = None  # Ponteiro para o próximo da fila


class Fila:
    def __init__(self):
        self.inicio = None  # Cabeça da fila (Quem será atendido agora)
        self.fim = None  # Final da fila (Onde entram os novos)
        self.tamanho = 0

    def entrar(self, dado):
        """
        Enqueue: Adiciona um elemento no final da fila.
        """
        novo_no = No(dado)

        if self.fim is None:
            # Se a fila estava vazia, o novo nó é tanto o início quanto o fim
            self.inicio = novo_no
            self.fim = novo_no
        else:
            # O atual último aponta para o novo
            self.fim.proximo = novo_no
            # O novo vira o último
            self.fim = novo_no

        self.tamanho += 1

    def sair(self):
        """
        Dequeue: Remove e retorna o elemento do início da fila.
        """
        if self.inicio is None:
            return None  # Fila vazia

        # Pegamos o dado do primeiro
        dado_removido = self.inicio.dado

        # O início anda para o próximo da fila
        self.inicio = self.inicio.proximo

        if self.inicio is None:
            # Se a fila ficou vazia, o fim também deve ser None
            self.fim = None

        self.tamanho -= 1
        return dado_removido

    def esta_vazia(self):
        return self.inicio is None

    def listar_para_template(self):
        """
        Método auxiliar para transformar a fila encadeada em uma lista simples
        apenas para conseguirmos mostrar no HTML facilmente.
        """
        lista_visual = []
        atual = self.inicio
        while atual is not None:
            lista_visual.append(atual.dado)
            atual = atual.proximo
        return lista_visual