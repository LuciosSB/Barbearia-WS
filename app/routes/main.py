from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app import agendamentos_db, fila_atendimento
from datetime import datetime, date

main_bp = Blueprint('main', __name__)

# Horários de funcionamento da barbearia
HORARIOS_FUNCIONAMENTO = [
    "09:00", "10:00", "11:00", "12:00",
    "14:00", "15:00", "16:00", "17:00", "18:00"
]


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/agendar', methods=['POST'])
def agendar():
    dados = request.get_json()

    # Validação básica
    if not dados or 'data' not in dados or 'horario' not in dados or 'nome' not in dados:
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos!'}), 400

    nome = dados['nome'].strip()
    telefone_raw = dados.get('telefone', '')
    data_str = dados['data']
    horario = dados['horario']

    # Validações de Texto (Nome/Telefone)
    if len(nome) < 3:
        return jsonify({'sucesso': False, 'mensagem': 'Nome muito curto.'}), 400

    telefone_limpo = "".join(filter(str.isdigit, telefone_raw))
    if len(telefone_limpo) < 10:
        return jsonify({'sucesso': False, 'mensagem': 'Telefone inválido.'}), 400

    # --- VALIDAÇÃO DE DATA E HORA (NOVA) ---
    try:
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
        hoje = date.today()

        # 1. Não pode ser data passada (Ontem, mês passado...)
        if data_agendamento < hoje:
            return jsonify({'sucesso': False, 'mensagem': 'Não é possível agendar no passado!'}), 400

        # 2. Se for HOJE, verifica se o horário já passou
        if data_agendamento == hoje:
            # Pega a hora atual do servidor
            agora = datetime.now().time()
            # Converte o horário do agendamento ("14:00") para objeto time
            hora_agendamento = datetime.strptime(horario, '%H:%M').time()

            if hora_agendamento <= agora:
                return jsonify({'sucesso': False, 'mensagem': 'Este horário já passou!'}), 400

    except ValueError:
        return jsonify({'sucesso': False, 'mensagem': 'Formato de data inválido.'}), 400

    # Inserção na Tabela Hash
    chave_unica = f"{data_str}-{horario}"

    sucesso = agendamentos_db.inserir(chave_unica, {
        'nome': nome,
        'telefone': telefone_raw
    })

    if sucesso:
        print(f"Agendamento: {nome} - {data_str} {horario}")
        return jsonify({'sucesso': True, 'mensagem': 'Agendamento realizado!'}), 201
    else:
        return jsonify({'sucesso': False, 'mensagem': 'Horário indisponível.'}), 409


@main_bp.route('/admin')
def admin_panel():
    lista_completa = agendamentos_db.listar_tudo()

    # Ordena cronologicamente
    lista_completa.sort(key=lambda x: x[0])

    hoje_str = str(date.today())  # Ex: "2025-11-21"

    agendamentos_hoje = []
    agendamentos_futuros = []

    for chave, dados in lista_completa:
        # A chave é "YYYY-MM-DD-HH:MM". Pegamos só a parte da data.
        data_chave = chave.split('-')[0] + "-" + chave.split('-')[1] + "-" + chave.split('-')[2]

        if data_chave == hoje_str:
            agendamentos_hoje.append((chave, dados))
        else:
            agendamentos_futuros.append((chave, dados))

    lista_fila = fila_atendimento.listar_para_template()

    return render_template('admin.html',
                           agendamentos_hoje=agendamentos_hoje,
                           agendamentos_futuros=agendamentos_futuros,
                           fila=lista_fila)

@main_bp.route('/admin/checkin/<chave>')
def checkin(chave):
    """
    Move o cliente da Agenda (Hash) para a Fila de Espera (Queue).
    """
    # 1. Busca na Hash
    cliente = agendamentos_db.buscar(chave)

    if cliente:
        # 2. Adiciona dados extras (hora que chegou, etc) se quiser
        cliente['horario_agendado'] = chave  # Guardamos a chave para referencia

        # 3. Entra na Fila
        fila_atendimento.entrar(cliente)

        # 4. Remove da Agenda (Opcional: poderiamos só marcar como 'chegou')
        # Vamos remover para simular que ele saiu da lista de "futuros" e foi para "presentes"
        agendamentos_db.remover(chave)

    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/editar/<chave>', methods=['GET', 'POST'])
def editar(chave):
    # Busca os dados atuais
    dados_atuais = agendamentos_db.buscar(chave)
    if not dados_atuais:
        return "Agendamento não encontrado", 404

    # Separa Data e Hora da chave antiga para preencher o formulário
    # Chave formato: YYYY-MM-DD-HH:MM (temos que tratar os traços com cuidado)
    partes = chave.split('-')
    # Data é tudo menos o último pedaço (Hora)
    data_atual = f"{partes[0]}-{partes[1]}-{partes[2]}"
    hora_atual = partes[3]

    if request.method == 'POST':
        nova_data = request.form['data']
        novo_horario = request.form['horario']

        # Lógica de "Move": Remove o velho -> Insere o novo
        agendamentos_db.remover(chave)

        nova_chave = f"{nova_data}-{novo_horario}"
        agendamentos_db.inserir(nova_chave, dados_atuais)  # Mantém nome/telefone, muda chave

        return redirect(url_for('main.admin_panel'))

    return render_template('editar.html',
                           chave=chave,
                           cliente=dados_atuais,
                           data=data_atual,
                           hora=hora_atual)

@main_bp.route('/admin/atender')
def atender_proximo():
    """
    Chama o próximo da fila (Dequeue).
    """
    if not fila_atendimento.esta_vazia():
        cliente_atendido = fila_atendimento.sair()
        print(f"Atendendo agora: {cliente_atendido['nome']}")

    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/cancelar/<chave>')
def cancelar(chave):
    """
    Remove um agendamento da Tabela Hash.
    Libera o horário para outra pessoa marcar.
    """
    sucesso = agendamentos_db.remover(chave)

    if sucesso:
        print(f"Agendamento cancelado: {chave}")
    else:
        print(f"Erro ao cancelar: {chave} não encontrado.")

    # Volta para o painel admin
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/api/horarios/<data>', methods=['GET'])
def verificar_horarios(data):
    """
    Rota que o Frontend chama para saber quais botões bloquear.
    Verifica na Tabela Hash quais horários daquela data já existem.
    """
    ocupados = []

    for horario in HORARIOS_FUNCIONAMENTO:
        chave = f"{data}-{horario}"
        # O método .buscar() da Hash retorna algo se existir, ou None se estiver livre
        if agendamentos_db.buscar(chave) is not None:
            ocupados.append(horario)

    return jsonify({'ocupados': ocupados})