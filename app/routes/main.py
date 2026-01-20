import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db, login_manager
from app.models import Agendamento, Usuario, Produto, Configuracao
from datetime import datetime, date, timedelta
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

def gerar_horarios_do_dia(data_obj):
    dia_semana = data_obj.weekday()

    if dia_semana == 6:
        return []

    if dia_semana == 5:
        chave_ini = 'sabado_inicio'
        chave_fim = 'sabado_fim'
        padrao_ini = 9
        padrao_fim = 17
    else:
        chave_ini = 'semana_inicio'
        chave_fim = 'semana_fim'
        padrao_ini = 9
        padrao_fim = 19

    conf_ini = Configuracao.query.filter_by(chave=chave_ini).first()
    conf_fim = Configuracao.query.filter_by(chave=chave_fim).first()

    hora_ini = int(conf_ini.valor.split(':')[0]) if conf_ini else padrao_ini
    hora_fim = int(conf_fim.valor.split(':')[0]) if conf_fim else padrao_fim

    lista_horarios = []
    for h in range(hora_ini, hora_fim):
        lista_horarios.append(f"{h:02d}:00")

    return lista_horarios



@main_bp.route('/setup')
def setup_inicial():
    if not Usuario.query.first():
        novo_admin = Usuario(username="admin")
        novo_admin.set_senha("admin123")
        db.session.add(novo_admin)

    configs_padrao = {
        'semana_inicio': '09:00',
        'semana_fim': '19:00',
        'sabado_inicio': '09:00',
        'sabado_fim': '17:00'
    }

    for chave, valor in configs_padrao.items():
        conf = Configuracao.query.filter_by(chave=chave).first()
        if not conf:
            nova_conf = Configuracao(chave=chave, valor=valor)
            db.session.add(nova_conf)

    db.session.commit()
    return "Setup realizado! Usuário Admin e Horários Padrão criados."


@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.admin_panel'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Usuario.query.filter_by(username=username).first()

        if user and user.verificar_senha(password):
            login_user(user)
            return redirect(url_for('main.admin_panel'))
        else:
            flash('Usuário ou senha incorretos.', 'error')

    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main_bp.route('/')
def index():
    lista_produtos = Produto.query.all()
    return render_template('index.html', produtos=lista_produtos)


@main_bp.route('/api/horarios/<data>', methods=['GET'])
def verificar_horarios(data):
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'ocupados': [], 'slots': []})

    slots_do_dia = gerar_horarios_do_dia(data_obj)

    agendamentos = Agendamento.query.filter_by(data=data_obj).all()
    ocupados = [a.horario for a in agendamentos]

    return jsonify({
        'ocupados': ocupados,
        'slots': slots_do_dia
    })


@main_bp.route('/agendar', methods=['POST'])
def agendar():
    dados = request.get_json()

    if not dados or 'data' not in dados or 'horario' not in dados or 'nome' not in dados:
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos!'}), 400

    nome = dados['nome'].strip()
    telefone = dados.get('telefone', '').strip()
    observacoes = dados.get('observacoes', '').strip()
    data_str = dados['data']
    horario = dados['horario']

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        hoje = date.today()

        if data_obj < hoje:
            return jsonify({'sucesso': False, 'mensagem': 'Data inválida.'}), 400

        if data_obj == hoje:
            agora_brasil = datetime.utcnow() - timedelta(hours=3)
            hora_atual = agora_brasil.time()
            hora_agendamento = datetime.strptime(horario, '%H:%M').time()

            if hora_agendamento <= hora_atual:
                return jsonify({'sucesso': False, 'mensagem': 'Horário já passou!'}), 400
        slots_validos = gerar_horarios_do_dia(data_obj)
        if horario not in slots_validos:
            return jsonify({'sucesso': False, 'mensagem': 'Horário inválido para este dia.'}), 400
    except ValueError:
        return jsonify({'sucesso': False, 'mensagem': 'Erro no formato da data.'}), 400

    agendamento_existente = Agendamento.query.filter_by(data=data_obj, horario=horario).first()
    if agendamento_existente:
        return jsonify({'sucesso': False, 'mensagem': 'Horário indisponível.'}), 409

    novo_agendamento = Agendamento(
        nome=nome,
        telefone=telefone,
        data=data_obj,
        horario=horario,
        status='agendado',
        observacoes=observacoes
    )
    db.session.add(novo_agendamento)
    db.session.commit()
    return jsonify({'sucesso': True, 'mensagem': 'Agendamento realizado!'}), 201

@main_bp.route('/keep-alive')
def keep_alive():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().strftime('%H:%M:%S')})


@main_bp.route('/admin/alterar-senha', methods=['POST'])
@login_required
def alterar_senha():
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']
    usuario = current_user
    if not usuario.verificar_senha(senha_atual):
        flash('A senha atual está incorreta.', 'error')
        return redirect(url_for('main.admin_panel'))

    if len(nova_senha) < 4:
        flash('A nova senha deve ter pelo menos 4 caracteres.', 'error')
        return redirect(url_for('main.admin_panel'))

    usuario.set_senha(nova_senha)
    db.session.commit()

    flash('Senha alterada com sucesso! Entre novamente com a nova senha.', 'success')
    return redirect(url_for('main.logout'))

@main_bp.route('/admin')
@login_required
def admin_panel():
    hoje = date.today()

    agendamentos_hoje = Agendamento.query.filter_by(data=hoje, status='agendado').order_by(Agendamento.horario).all()
    agendamentos_futuros = Agendamento.query.filter(Agendamento.data > hoje, Agendamento.status == 'agendado').order_by(
        Agendamento.data, Agendamento.horario).all()
    fila = Agendamento.query.filter_by(status='na_fila').all()
    produtos = Produto.query.all()

    c_sem_ini = Configuracao.query.filter_by(chave='semana_inicio').first()
    c_sem_fim = Configuracao.query.filter_by(chave='semana_fim').first()
    c_sab_ini = Configuracao.query.filter_by(chave='sabado_inicio').first()
    c_sab_fim = Configuracao.query.filter_by(chave='sabado_fim').first()

    total_fila = len(fila)
    total_hoje = Agendamento.query.filter_by(data=hoje).count()
    data_limite = hoje + timedelta(days=6)
    total_semana = Agendamento.query.filter(Agendamento.data >= hoje, Agendamento.data <= data_limite).count()

    return render_template('admin.html',
                           agendamentos_hoje=agendamentos_hoje,
                           agendamentos_futuros=agendamentos_futuros,
                           fila=fila,
                           usuario=current_user,
                           produtos=produtos,
                           total_fila=total_fila,
                           total_hoje=total_hoje,
                           total_semana=total_semana,
                           c_sem_ini=c_sem_ini.valor if c_sem_ini else '09:00',
                           c_sem_fim=c_sem_fim.valor if c_sem_fim else '19:00',
                           c_sab_ini=c_sab_ini.valor if c_sab_ini else '09:00',
                           c_sab_fim=c_sab_fim.valor if c_sab_fim else '17:00'
                           )


@main_bp.route('/admin/configurar', methods=['POST'])
@login_required
def configurar_horarios():
    dados = {
        'semana_inicio': request.form['semana_inicio'],
        'semana_fim': request.form['semana_fim'],
        'sabado_inicio': request.form['sabado_inicio'],
        'sabado_fim': request.form['sabado_fim']
    }

    for chave, valor in dados.items():
        conf = Configuracao.query.filter_by(chave=chave).first()
        if conf:
            conf.valor = valor
        else:
            new_conf = Configuracao(chave=chave, valor=valor)
            db.session.add(new_conf)

    db.session.commit()
    flash('Horários de funcionamento atualizados!', 'success')
    return redirect(url_for('main.admin_panel'))


@main_bp.route('/admin/produto/novo', methods=['POST'])
@login_required
def novo_produto():
    nome = request.form['nome']
    preco = request.form['preco']
    if 'imagem' not in request.files:
        flash('Nenhum arquivo enviado', 'error')
        return redirect(url_for('main.admin_panel'))

    file = request.files['imagem']
    imagem_db = "sem_foto.png"

    if file.filename != '' and file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        file.save(os.path.join(upload_folder, filename))
        imagem_db = filename

    novo_prod = Produto(nome=nome, preco=preco, imagem=imagem_db)
    db.session.add(novo_prod)
    db.session.commit()

    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/produto/deletar/<int:id>')
@login_required
def deletar_produto(id):
    prod = Produto.query.get_or_404(id)
    db.session.delete(prod)
    db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/checkin/<int:id>')
@login_required
def checkin(id):
    agendamento = Agendamento.query.get_or_404(id)
    agendamento.status = 'na_fila'
    db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/atender')
@login_required
def atender_proximo():
    proximo = Agendamento.query.filter_by(status='na_fila').first()
    if proximo:
        proximo.status = 'atendido'
        db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/cancelar/<int:id>')
@login_required
def cancelar(id):
    agendamento = Agendamento.query.get_or_404(id)
    db.session.delete(agendamento)
    db.session.commit()
    return redirect(url_for('main.admin_panel'))

@main_bp.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    agendamento = Agendamento.query.get_or_404(id)
    if request.method == 'POST':
        nova_data = request.form['data']
        novo_horario = request.form['horario']
        agendamento.data = datetime.strptime(nova_data, '%Y-%m-%d').date()
        agendamento.horario = novo_horario
        db.session.commit()
        return redirect(url_for('main.admin_panel'))
    return render_template('editar.html', cliente=agendamento, data=agendamento.data, hora=agendamento.horario, id=id)

@main_bp.route('/limpar-banco-nuclear')
def limpar_banco():
    # Apaga as tabelas antigas para criar as novas
    sql = text("DROP TABLE IF EXISTS agendamentos, usuarios, produtos, configuracoes CASCADE;")
    db.session.execute(sql)
    db.session.commit()
    return "Banco de dados limpo com sucesso! Agora acesse /setup."