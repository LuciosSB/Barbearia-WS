class No:
    def __init__(self, dado):
        self.dado = dado
        self.proximo = None


class Fila:
    def __init__(self):
        self.inicio = None
        self.fim = None
        self.tamanho = 0

    def entrar(self, dado):
        novo_no = No(dado)

        if self.fim is None:
            self.inicio = novo_no
            self.fim = novo_no
        else:
            self.fim.proximo = novo_no
            self.fim = novo_no

        self.tamanho += 1

    def sair(self):
        if self.inicio is None:
            return None

        dado_removido = self.inicio.dado

        self.inicio = self.inicio.proximo

        if self.inicio is None:

            self.fim = None

        self.tamanho -= 1
        return dado_removido

    def esta_vazia(self):
        return self.inicio is None

    def listar_para_template(self):
        lista_visual = []
        atual = self.inicio
        while atual is not None:
            lista_visual.append(atual.dado)
            atual = atual.proximo
        return lista_visual