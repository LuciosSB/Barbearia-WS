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

    if not dados or 'data' not in dados or 'horario' not in dados or 'nome' not in dados:
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos!'}), 400

    nome = dados['nome'].strip()
    telefone_raw = dados.get('telefone', '')
    data_str = dados['data']
    horario = dados['horario']

    if len(nome) < 3:
        return jsonify({'sucesso': False, 'mensagem': 'Nome muito curto.'}), 400

    telefone_limpo = "".join(filter(str.isdigit, telefone_raw))
    if len(telefone_limpo) < 10:
        return jsonify({'sucesso': False, 'mensagem': 'Telefone inválido.'}), 400

    try:
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
        hoje = date.today()

        if data_agendamento < hoje:
            return jsonify({'sucesso': False, 'mensagem': 'Não é possível agendar no passado!'}), 400

        if data_agendamento == hoje:
            agora = datetime.now().time()
            hora_agendamento = datetime.strptime(horario, '%H:%M').time()

            if hora_agendamento <= agora:
                return jsonify({'sucesso': False, 'mensagem': 'Este horário já passou!'}), 400

    except ValueError:
        return jsonify({'sucesso': False, 'mensagem': 'Formato de data inválido.'}), 400

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

    lista_completa.sort(key=lambda x: x[0])

    hoje_str = str(date.today())  # Ex: "2025-11-21"

    agendamentos_hoje = []
    agendamentos_futuros = []

    for chave, dados in lista_completa:
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
    cliente = agendamentos_db.buscar(chave)

    if cliente:
        cliente['horario_agendado'] = chave

        fila_atendimento.entrar(cliente)
        agendamentos_db.remover(chave)

    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/editar/<chave>', methods=['GET', 'POST'])
def editar(chave):
    dados_atuais = agendamentos_db.buscar(chave)
    if not dados_atuais:
        return "Agendamento não encontrado", 404

    partes = chave.split('-')
    data_atual = f"{partes[0]}-{partes[1]}-{partes[2]}"
    hora_atual = partes[3]

    if request.method == 'POST':
        nova_data = request.form['data']
        novo_horario = request.form['horario']

        agendamentos_db.remover(chave)

        nova_chave = f"{nova_data}-{novo_horario}"
        agendamentos_db.inserir(nova_chave, dados_atuais)

        return redirect(url_for('main.admin_panel'))

    return render_template('editar.html',
                           chave=chave,
                           cliente=dados_atuais,
                           data=data_atual,
                           hora=hora_atual)

@main_bp.route('/admin/atender')
def atender_proximo():
    if not fila_atendimento.esta_vazia():
        cliente_atendido = fila_atendimento.sair()
        print(f"Atendendo agora: {cliente_atendido['nome']}")

    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/cancelar/<chave>')
def cancelar(chave):
    sucesso = agendamentos_db.remover(chave)

    if sucesso:
        print(f"Agendamento cancelado: {chave}")
    else:
        print(f"Erro ao cancelar: {chave} não encontrado.")

    # Volta para o painel admin
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/api/horarios/<data>', methods=['GET'])
def verificar_horarios(data):
    ocupados = []

    for horario in HORARIOS_FUNCIONAMENTO:
        chave = f"{data}-{horario}"
        if agendamentos_db.buscar(chave) is not None:
            ocupados.append(horario)

    return jsonify({'ocupados': ocupados})