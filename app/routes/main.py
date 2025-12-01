import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db, login_manager
from app.models import Agendamento, Usuario, Produto
from datetime import datetime, date, timedelta

main_bp = Blueprint('main', __name__)

HORARIOS_FUNCIONAMENTO = [
    "09:00", "10:00", "11:00", "12:00",
    "14:00", "15:00", "16:00", "17:00", "18:00"
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

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

@main_bp.route('/setup')
def setup_inicial():
    if Usuario.query.first():
        return "Já existe um usuário configurado. Setup bloqueado."
    novo_admin = Usuario(username="admin")
    novo_admin.set_senha("admin123")
    db.session.add(novo_admin)
    db.session.commit()
    return "Usuário 'admin' criado com senha 'admin123'. Vá para /login."

@main_bp.route('/')
def index():
    lista_produtos = Produto.query.all()
    return render_template('index.html', produtos=lista_produtos)

@main_bp.route('/agendar', methods=['POST'])
def agendar():
    dados = request.get_json()

    if not dados or 'data' not in dados or 'horario' not in dados or 'nome' not in dados:
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos!'}), 400

    nome = dados['nome'].strip()
    telefone = dados.get('telefone', '').strip()
    data_str = dados['data']
    horario = dados['horario']

    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        hoje = date.today()
        if data_obj < hoje:
            return jsonify({'sucesso': False, 'mensagem': 'Data inválida.'}), 400
        if data_obj == hoje:
            hora_atual = datetime.now().time()
            hora_agendamento = datetime.strptime(horario, '%H:%M').time()
            if hora_agendamento <= hora_atual:
                return jsonify({'sucesso': False, 'mensagem': 'Horário já passou!'}), 400
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
        status='agendado'
    )
    db.session.add(novo_agendamento)
    db.session.commit()
    return jsonify({'sucesso': True, 'mensagem': 'Agendamento realizado!'}), 201

@main_bp.route('/api/horarios/<data>', methods=['GET'])
def verificar_horarios(data):
    try:
        data_obj = datetime.strptime(data, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'ocupados': []})
    agendamentos = Agendamento.query.filter_by(data=data_obj).all()
    ocupados = [a.horario for a in agendamentos]
    return jsonify({'ocupados': ocupados})

@main_bp.route('/admin')
@login_required
def admin_panel():
    hoje = date.today()

    agendamentos_hoje = Agendamento.query.filter_by(data=hoje, status='agendado').order_by(Agendamento.horario).all()
    agendamentos_futuros = Agendamento.query.filter(Agendamento.data > hoje, Agendamento.status == 'agendado').order_by(
        Agendamento.data, Agendamento.horario).all()
    fila = Agendamento.query.filter_by(status='na_fila').all()
    produtos = Produto.query.all()
    total_fila = len(fila)
    total_hoje = Agendamento.query.filter_by(data=hoje).count()
    data_limite = hoje + timedelta(days=6)
    total_semana = Agendamento.query.filter(Agendamento.data >= hoje, Agendamento.data <= data_limite).count()

    return render_template('admin.html',
                           agendamentos_hoje=agendamentos_hoje,
                           agendamentos_futuros=agendamentos_futuros,
                           fila=fila,
                           usuario=current_user,
                           total_fila=total_fila,
                           total_hoje=total_hoje,
                           total_semana=total_semana,
                           produtos=produtos)

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