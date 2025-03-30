from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import os
import csv
import secrets
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'finance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = 'sua_salt_secreta_aqui'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Altere conforme seu servidor de email
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # Altere para seu email
app.config['MAIL_PASSWORD'] = 'sua_senha_de_app'  # Altere para sua senha de aplicativo
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'  # Altere para seu email
app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')

db = SQLAlchemy(app)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Modelo para usuários
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    credit_cards = db.relationship('CreditCard', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.email}>"

# Modelo para cartões de crédito
class CreditCard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    limit = db.Column(db.Float, nullable=False)
    due_day = db.Column(db.Integer, nullable=False)  # Dia de vencimento (1-31)
    closing_day = db.Column(db.Integer, nullable=False)  # Dia de fechamento (1-31)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# Modelo para transações
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    trans_type = db.Column(db.String(10), nullable=False)  # "entrada" ou "saida"
    category = db.Column(db.String(50), nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_type = db.Column(db.String(20), nullable=True)  # "diario", "semanal", "mensal", "anual"
    recurrence_end_date = db.Column(db.Date, nullable=True)
    recurrence_count = db.Column(db.Integer, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    credit_card_id = db.Column(db.Integer, db.ForeignKey('credit_card.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Transaction {self.date} {self.value} {self.trans_type}>"

# Função para converter a string de data em objeto date
def parse_date(date_str):
    """
    Tenta converter a string de data para o objeto date.
    Aceita os formatos: '10-08-2025', '10/08/2025' ou '10-ago.'
    (nesse último, assumindo o ano atual).
    """
    try:
        dt = datetime.strptime(date_str, '%d-%m-%Y')
    except ValueError:
        try:
            dt = datetime.strptime(date_str, '%d/%m/%Y')
        except ValueError:
            # Tenta interpretar abreviações de mês em português
            months_map = { "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5,
                           "jun": 6, "jul": 7, "ago": 8, "set": 9, "out": 10,
                           "nov": 11, "dez": 12 }
            date_str = date_str.replace('.', '').strip()
            parts = date_str.split('-')
            if len(parts) == 2:
                day = int(parts[0])
                month_str = parts[1].lower()
                month = months_map.get(month_str, 1)
                dt = datetime(datetime.now().year, month, day)
            else:
                dt = datetime.now()
    return dt.date()

# Função para carregar o usuário pelo ID (necessário para o Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Função para enviar email
def send_email(to, subject, template):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_DEFAULT_SENDER']
    msg['To'] = to
    
    part = MIMEText(template, 'html')
    msg.attach(part)
    
    try:
        server = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        server.ehlo()
        server.starttls()
        server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        server.sendmail(app.config['MAIL_DEFAULT_SENDER'], to, msg.as_string())
        server.close()
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

# Função para gerar token de redefinição de senha
def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

# Função para verificar se o arquivo tem extensão permitida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

# Função para confirmar token de redefinição de senha
def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except (SignatureExpired, BadSignature):
        return None

# Rota de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        if not name or not email or not password or not password2:
            flash('Todos os campos são obrigatórios.', 'danger')
            return redirect(url_for('register'))
        
        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('register'))
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Este email já está em uso.', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Agora você pode fazer login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        if not email or not password:
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Email ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
        
        if not user.active:
            flash('Esta conta está desativada.', 'danger')
            return redirect(url_for('login'))
        
        login_user(user, remember=remember)
        user.last_login = datetime.now()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
            
        flash(f'Bem-vindo, {user.name}!', 'success')
        return redirect(next_page)
    
    return render_template('login.html')

# Rota de logout
@app.route('/logout')
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# Rota para solicitar redefinição de senha
@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        if not email:
            flash('Por favor, informe seu email.', 'danger')
            return redirect(url_for('reset_password_request'))
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('Email não encontrado.', 'danger')
            return redirect(url_for('reset_password_request'))
        
        token = generate_token(user.email)
        reset_url = url_for('reset_password', token=token, _external=True)
        
        html = f'''
        <p>Olá {user.name},</p>
        <p>Para redefinir sua senha, clique no link abaixo:</p>
        <p><a href="{reset_url}">Redefinir Senha</a></p>
        <p>Se você não solicitou a redefinição de senha, ignore este email.</p>
        <p>Atenciosamente,<br>Sistema Financeiro</p>
        '''
        
        subject = "Redefinição de Senha - Sistema Financeiro"
        
        if send_email(user.email, subject, html):
            flash('Um email com instruções para redefinir sua senha foi enviado.', 'info')
        else:
            flash('Ocorreu um erro ao enviar o email. Por favor, tente novamente.', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html')

# Rota para redefinir senha
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    email = confirm_token(token)
    
    if not email:
        flash('O link de redefinição de senha é inválido ou expirou.', 'danger')
        return redirect(url_for('reset_password_request'))
    
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('reset_password_request'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password2 = request.form.get('password2')
        
        if not password or not password2:
            flash('Por favor, preencha todos os campos.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        if password != password2:
            flash('As senhas não coincidem.', 'danger')
            return redirect(url_for('reset_password', token=token))
        
        user.set_password(password)
        db.session.commit()
        
        flash('Sua senha foi redefinida com sucesso!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

# Rota de perfil do usuário
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        new_password2 = request.form.get('new_password2')
        
        if not name or not email:
            flash('Nome e email são obrigatórios.', 'danger')
            return redirect(url_for('profile'))
        
        # Verificar se o email já está em uso por outro usuário
        if email != current_user.email:
            user = User.query.filter_by(email=email).first()
            if user:
                flash('Este email já está em uso por outro usuário.', 'danger')
                return redirect(url_for('profile'))
        
        # Atualizar nome e email
        current_user.name = name
        current_user.email = email
        
        # Atualizar senha se fornecida
        if current_password and new_password and new_password2:
            if not current_user.check_password(current_password):
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('profile'))
            
            if new_password != new_password2:
                flash('As novas senhas não coincidem.', 'danger')
                return redirect(url_for('profile'))
            
            current_user.set_password(new_password)
            flash('Senha atualizada com sucesso!', 'success')
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html')

# Rota principal - Dashboard com extrato e saldo acumulado
@app.route('/')
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date).all()
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id).all()
    balance = 0.0
    txn_list = []
    
    # Obter data atual para filtrar transações
    current_date = datetime.now().date()
    current_month = current_date.month
    current_year = current_date.year
    current_month_income = 0.0
    current_month_expenses = 0.0
    
    # Primeiro, calcular o saldo atual (considerando apenas transações até a data atual)
    current_balance = 0.0
    for txn in transactions:
        # Atualizar saldo apenas para transações até a data atual
        if txn.date <= current_date:
            if txn.trans_type == 'entrada':
                current_balance += txn.value
            elif txn.trans_type == 'saida':
                current_balance -= txn.value
    
    # Agora, processar todas as transações para o histórico e calcular entradas/saídas do mês atual
    running_balance = 0.0
    for txn in transactions:
        # Atualizar saldo acumulado para exibição no histórico
        if txn.trans_type == 'entrada':
            running_balance += txn.value
        elif txn.trans_type == 'saida':
            running_balance -= txn.value
            
        # Verificar se a transação é do mês atual
        if txn.date.month == current_month and txn.date.year == current_year:
            if txn.trans_type == 'entrada':
                current_month_income += txn.value
            elif txn.trans_type == 'saida':
                current_month_expenses += txn.value
                
        txn_list.append({
            'id': txn.id,
            'date': txn.date.strftime("%d-%b-%Y"),
            'value': txn.value,
            'description': txn.description,
            'trans_type': txn.trans_type,
            'category': txn.category,
            'balance': running_balance
        })
    return render_template('index.html', transactions=txn_list, total_balance=running_balance, 
                           current_balance=current_balance,
                           current_month_income=current_month_income, current_month_expenses=current_month_expenses,
                           credit_cards=credit_cards)

# Função para gerar datas recorrentes
def generate_recurring_dates(start_date, recurrence_type, end_date=None, count=None):
    """Gera datas recorrentes com base no tipo de recorrência e critérios de término."""
    dates = [start_date]
    current_date = start_date
    
    # Se não houver critério de término, limitamos a 60 ocorrências para evitar loops infinitos
    max_occurrences = 60 if not count and not end_date else count or 9999
    
    while len(dates) < max_occurrences:
        if recurrence_type == 'diario':
            current_date = current_date + timedelta(days=1)
        elif recurrence_type == 'semanal':
            current_date = current_date + timedelta(weeks=1)
        elif recurrence_type == 'mensal':
            # Avançar um mês mantendo o mesmo dia (ou o último dia do mês se necessário)
            month = current_date.month + 1
            year = current_date.year
            if month > 12:
                month = 1
                year += 1
            
            # Determinar o último dia do próximo mês
            if month == 12:
                last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
            # Usar o dia original ou o último dia do mês se o dia original for maior
            day = min(current_date.day, last_day.day)
            current_date = datetime(year, month, day).date()
        elif recurrence_type == 'anual':
            current_date = datetime(current_date.year + 1, current_date.month, current_date.day).date()
        
        # Verificar se atingimos a data final
        if end_date and current_date > end_date:
            break
            
        dates.append(current_date)
    
    return dates

# Rota para adicionar uma transação manualmente
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        date_str = request.form.get('date')
        value_str = request.form.get('value')
        description = request.form.get('description')
        trans_type = request.form.get('trans_type')
        category = request.form.get('category')
        credit_card_id = request.form.get('credit_card_id')
        
        # Campos de recorrência
        is_recurring = 'is_recurring' in request.form
        recurrence_type = request.form.get('recurrence_type')
        recurrence_end_type = request.form.get('recurrence_end_type')
        recurrence_end_date_str = request.form.get('recurrence_end_date')
        recurrence_count_str = request.form.get('recurrence_count')
        
        if not date_str or not value_str or not description or not trans_type:
            flash("Todos os campos obrigatórios devem ser preenchidos.", 'danger')
            return redirect(url_for('add_transaction'))
        try:
            value = float(value_str.replace(',', '.'))
        except ValueError:
            flash("Valor inválido.", 'danger')
            return redirect(url_for('add_transaction'))
        
        date_obj = parse_date(date_str)
        
        # Verificar se foi selecionado um cartão de crédito
        card_id = None
        if credit_card_id and trans_type.lower() == 'saida':
            try:
                card_id = int(credit_card_id)
                # Verificar se o cartão existe
                card = CreditCard.query.get(card_id)
                if not card:
                    card_id = None
            except ValueError:
                card_id = None
        
        # Criar a transação principal
        new_txn = Transaction(
            date=date_obj, 
            value=value, 
            description=description,
            trans_type=trans_type.lower(), 
            category=category,
            is_recurring=is_recurring,
            credit_card_id=card_id,
            user_id=current_user.id
        )
        
        # Se for recorrente, configurar os campos de recorrência
        if is_recurring and recurrence_type:
            new_txn.recurrence_type = recurrence_type
            
            # Configurar data final ou contagem de recorrências
            recurrence_end_date = None
            recurrence_count = None
            
            if recurrence_end_type == 'date' and recurrence_end_date_str:
                recurrence_end_date = parse_date(recurrence_end_date_str)
                new_txn.recurrence_end_date = recurrence_end_date
            elif recurrence_end_type == 'count' and recurrence_count_str:
                try:
                    recurrence_count = int(recurrence_count_str)
                    new_txn.recurrence_count = recurrence_count
                except ValueError:
                    pass
            
            # Adicionar a transação principal
            db.session.add(new_txn)
            db.session.flush()  # Para obter o ID da transação principal
            
            # Gerar transações recorrentes
            recurring_dates = generate_recurring_dates(
                date_obj, 
                recurrence_type, 
                recurrence_end_date, 
                recurrence_count
            )
            
            # Criar transações para cada data (exceto a primeira, que já é a principal)
            for recurring_date in recurring_dates[1:]:
                recurring_txn = Transaction(
                    date=recurring_date,
                    value=value,
                    description=description,
                    trans_type=trans_type.lower(),
                    category=category,
                    is_recurring=True,
                    parent_id=new_txn.id,
                    credit_card_id=card_id,  # Adicionar o cartão de crédito às transações recorrentes
                    user_id=current_user.id
                )
                db.session.add(recurring_txn)
        else:
            # Adicionar transação não recorrente
            db.session.add(new_txn)
        
        db.session.commit()
        
        if is_recurring:
            flash(f"Transação recorrente adicionada com sucesso! Foram criadas {len(recurring_dates)} ocorrências.", 'success')
        else:
            flash("Transação adicionada com sucesso!", 'success')
            
        return redirect(url_for('index'))
        
    # Obter lista de cartões de crédito para o formulário
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id).all()
    return render_template('add_transaction.html', credit_cards=credit_cards)

# Configuração para upload de CSV
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'csv'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rota para importar transações via CSV
@app.route('/upload', methods=['GET','POST'])
@login_required
def upload_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Nenhum arquivo selecionado.", 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash("Nenhum arquivo selecionado.", 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                csv_reader = csv.DictReader(csvfile)
                for row in csv_reader:
                    date_str = row.get('data') or row.get('date')
                    value_str = row.get('valor') or row.get('value')
                    description = row.get('descricao') or row.get('description')
                    trans_type = row.get('tipo') or row.get('type') or 'entrada'
                    category = row.get('categoria') or row.get('category')
                    if not date_str or not value_str or not description:
                        continue
                    try:
                        value = float(value_str.replace('R$', '').replace(' ', '').replace(',', '.'))
                    except Exception:
                        continue
                    date_obj = parse_date(date_str)
                    txn = Transaction(date=date_obj, value=value, description=description,
                                      trans_type=trans_type.lower(), category=category, user_id=current_user.id)
                    db.session.add(txn)
                db.session.commit()
            flash("Arquivo CSV importado com sucesso!", 'success')
            return redirect(url_for('index'))
        else:
            flash("Formato de arquivo não permitido (apenas CSV).", 'danger')
            return redirect(request.url)
    return render_template('upload.html')

# Rota para editar uma transação
@app.route('/edit/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    if request.method == 'POST':
        date_str = request.form.get('date')
        value_str = request.form.get('value')
        description = request.form.get('description')
        trans_type = request.form.get('trans_type')
        category = request.form.get('category')
        credit_card_id = request.form.get('credit_card_id')
        
        if not date_str or not value_str or not description or not trans_type:
            return jsonify({'success': False, 'message': 'Todos os campos obrigatórios devem ser preenchidos.'})
        
        try:
            value = float(value_str.replace(',', '.'))
        except ValueError:
            return jsonify({'success': False, 'message': 'Valor inválido.'})
        
        date_obj = parse_date(date_str)
        
        # Verificar se foi selecionado um cartão de crédito
        card_id = None
        if credit_card_id and trans_type.lower() == 'saida':
            try:
                card_id = int(credit_card_id)
                # Verificar se o cartão existe
                card = CreditCard.query.get(card_id)
                if not card:
                    card_id = None
            except ValueError:
                card_id = None
        
        transaction.date = date_obj
        transaction.value = value
        transaction.description = description
        transaction.trans_type = trans_type.lower()
        transaction.category = category
        transaction.credit_card_id = card_id
        
        # Se for uma transação recorrente principal, atualizar também as transações filhas futuras
        if transaction.is_recurring and transaction.parent_id is None:
            # Buscar todas as transações filhas futuras
            future_transactions = Transaction.query.filter(
                Transaction.parent_id == transaction.id,
                Transaction.date > datetime.now().date()
            ).all()
            
            # Atualizar cada transação filha
            for child_txn in future_transactions:
                child_txn.value = value
                child_txn.description = description
                child_txn.trans_type = trans_type.lower()
                child_txn.category = category
                child_txn.credit_card_id = card_id
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Transação atualizada com sucesso!'})
    
    # Se for GET, retorna os dados da transação
    return jsonify({
        'id': transaction.id,
        'date': transaction.date.strftime("%d-%m-%Y"),
        'value': transaction.value,
        'description': transaction.description,
        'trans_type': transaction.trans_type,
        'category': transaction.category or '',
        'credit_card_id': transaction.credit_card_id or ''
    })

# Rota para excluir uma transação
@app.route('/delete/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Transação excluída com sucesso!'})

# Rota para projetar saldo futuro
@app.route('/future_balance')
@login_required
def future_balance():
    # Obter todas as transações ordenadas por data
    transactions = Transaction.query.order_by(Transaction.date).all()
    
    # Data atual
    current_date = datetime.now().date()
    
    # Calcular saldo atual
    current_balance = 0.0
    for txn in transactions:
        if txn.date <= current_date:
            if txn.trans_type == 'entrada':
                current_balance += txn.value
            else:
                current_balance -= txn.value
    
    # Projetar saldo para o mês atual e os próximos 11 meses (total de 12 meses)
    projection = []
    projected_balance = current_balance
    
    # Filtrar transações futuras
    future_transactions = [t for t in transactions if t.date > current_date]
    
    # Adicionar o mês atual à projeção
    current_month = current_date.replace(day=1)
    last_day_current_month = (current_month.replace(month=current_month.month % 12 + 1, day=1) if current_month.month < 12 else 
                             current_month.replace(year=current_month.year + 1, month=1, day=1)) - timedelta(days=1)
    
    # Adicionar o mês atual à projeção
    projection.append({
        'date': current_date.strftime("%b/%Y"),  # Mês atual
        'balance': current_balance,
        'transactions': 0  # Não contamos transações passadas
    })
    
    # Obter o primeiro dia do próximo mês
    next_month = current_date.replace(day=1)
    if current_date.month == 12:
        next_month = next_month.replace(year=current_date.year + 1, month=1)
    else:
        next_month = next_month.replace(month=current_date.month + 1)
    
    # Projetar para os próximos 12 meses
    for i in range(12):
        # Calcular o último dia do mês atual
        if next_month.month == 12:
            last_day = next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)
        
        # Filtrar transações do mês
        month_transactions = [t for t in future_transactions if next_month <= t.date <= last_day]
        
        # Calcular mudança no saldo para o mês
        month_balance_change = 0
        for txn in month_transactions:
            if txn.trans_type == 'entrada':
                month_balance_change += txn.value
            else:
                month_balance_change -= txn.value
        
        projected_balance += month_balance_change
        
        projection.append({
            'date': last_day.strftime("%b/%Y"),  # Formato mês/ano
            'balance': projected_balance,
            'transactions': len(month_transactions)
        })
        
        # Avançar para o próximo mês
        if next_month.month == 12:
            next_month = next_month.replace(year=next_month.year + 1, month=1)
        else:
            next_month = next_month.replace(month=next_month.month + 1)
    
    return jsonify({
        'current_balance': current_balance,
        'projection': projection
    })

# Rota para baixar o template CSV de exemplo
@app.route('/download_template')
@login_required
def download_template():
    template_path = os.path.join(app.config['UPLOAD_FOLDER'], 'template.csv')
    return send_file(template_path, as_attachment=True, download_name='template_transacoes.csv')

# Rota para exportar os dados em CSV (relatório)
@app.route('/export')
@login_required
def export_csv():
    transactions = Transaction.query.order_by(Transaction.date).all()
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['data', 'valor', 'descricao', 'tipo', 'categoria'])
    for txn in transactions:
        writer.writerow([txn.date.strftime("%d-%m-%Y"), txn.value, txn.description, txn.trans_type, txn.category])
    output = si.getvalue()
    return app.response_class(
        output,
        mimetype='text/csv',
        headers={"Content-Disposition": "attachment;filename=transactions_report.csv"}
    )

# Rota para listar transações recorrentes
@app.route('/recurring')
@login_required
def recurring_transactions():
    # Buscar todas as transações recorrentes principais (parent_id é NULL)
    recurring_groups = []
    parent_transactions = Transaction.query.filter_by(is_recurring=True, parent_id=None).all()
    
    for parent in parent_transactions:
        # Buscar todas as transações desta série (incluindo a principal)
        series_transactions = Transaction.query.filter(
            db.or_(
                Transaction.id == parent.id,
                Transaction.parent_id == parent.id
            )
        ).order_by(Transaction.date).all()
        
        # Contar transações futuras
        today = datetime.now().date()
        future_transactions = [t for t in series_transactions if t.date > today]
        next_date = future_transactions[0].date.strftime("%d-%b-%Y") if future_transactions else "Finalizada"
        
        # Obter informações do cartão de crédito, se houver
        credit_card_name = None
        if parent.credit_card_id:
            card = CreditCard.query.get(parent.credit_card_id)
            if card:
                credit_card_name = card.name
        
        recurring_groups.append({
            'id': parent.id,
            'description': parent.description,
            'value': parent.value,
            'trans_type': parent.trans_type,
            'category': parent.category,
            'recurrence_type': parent.recurrence_type,
            'next_date': next_date,
            'count': len(series_transactions) - len(future_transactions),  # Ocorrências passadas
            'total': len(series_transactions),  # Total de ocorrências
            'credit_card_id': parent.credit_card_id,
            'credit_card_name': credit_card_name
        })
    
    return render_template('recurring.html', recurring_groups=recurring_groups)

# Rota para obter detalhes de uma série recorrente
@app.route('/recurring/<int:series_id>')
@login_required
def get_recurring_series(series_id):
    # Buscar a transação principal
    parent = Transaction.query.get_or_404(series_id)
    
    if not parent.is_recurring:
        return jsonify({'success': False, 'message': 'Esta não é uma transação recorrente.'})
    
    # Buscar todas as transações desta série (incluindo a principal)
    series_transactions = Transaction.query.filter(
        db.or_(
            Transaction.id == parent.id,
            Transaction.parent_id == parent.id
        )
    ).order_by(Transaction.date).all()
    
    # Formatar os dados para retornar
    series_data = {
        'id': parent.id,
        'description': parent.description,
        'value': parent.value,
        'trans_type': parent.trans_type,
        'category': parent.category,
        'recurrence_type': parent.recurrence_type
    }
    
    occurrences = []
    for txn in series_transactions:
        occurrences.append({
            'id': txn.id,
            'date': txn.date.strftime("%d-%b-%Y"),
            'status': 'past' if txn.date <= datetime.now().date() else 'future'
        })
    
    return jsonify({
        'success': True,
        'series': series_data,
        'occurrences': occurrences
    })

# Rota para cancelar uma série recorrente
@app.route('/recurring/cancel/<int:series_id>', methods=['POST'])
@login_required
def cancel_recurring_series(series_id):
    # Obter a opção de cancelamento (future ou all)
    data = request.get_json()
    option = data.get('option', 'future')
    
    # Buscar a transação principal
    parent = Transaction.query.get_or_404(series_id)
    
    if not parent.is_recurring:
        return jsonify({'success': False, 'message': 'Esta não é uma transação recorrente.'})
    
    today = datetime.now().date()
    
    if option == 'all':
        # Excluir todas as transações da série (incluindo a principal)
        transactions_to_delete = Transaction.query.filter(
            db.or_(
                Transaction.id == parent.id,
                Transaction.parent_id == parent.id
            )
        ).all()
        
        for txn in transactions_to_delete:
            db.session.delete(txn)
    else:  # option == 'future'
        # Excluir apenas transações futuras
        future_transactions = Transaction.query.filter(
            db.and_(
                db.or_(
                    Transaction.id == parent.id,
                    Transaction.parent_id == parent.id
                ),
                Transaction.date > today
            )
        ).all()
        
        for txn in future_transactions:
            db.session.delete(txn)
        
        # Se a transação principal for futura, precisamos remover a flag de recorrência das restantes
        if parent.date > today:
            # Encontrar a transação mais recente no passado para torná-la a nova "principal"
            past_transactions = Transaction.query.filter(
                db.and_(
                    Transaction.parent_id == parent.id,
                    Transaction.date <= today
                )
            ).order_by(Transaction.date.desc()).first()
            
            if past_transactions:
                past_transactions.is_recurring = False
                past_transactions.recurrence_type = None
                past_transactions.recurrence_end_date = None
                past_transactions.recurrence_count = None
                past_transactions.parent_id = None
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Série cancelada com sucesso!'})

# Rota para cancelar uma única ocorrência
@app.route('/recurring/cancel-occurrence/<int:occurrence_id>', methods=['POST'])
def cancel_occurrence(occurrence_id):
    # Buscar a ocorrência
    occurrence = Transaction.query.get_or_404(occurrence_id)
    
    # Verificar se é uma ocorrência futura
    if occurrence.date <= datetime.now().date():
        return jsonify({'success': False, 'message': 'Não é possível cancelar ocorrências passadas.'})
    
    # Guardar o ID da série para retornar
    series_id = occurrence.parent_id or occurrence.id
    
    # Excluir a ocorrência
    db.session.delete(occurrence)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Ocorrência cancelada com sucesso!', 'seriesId': series_id})

# Rota para listar cartões de crédito
@app.route('/credit_cards')
def credit_cards():
    cards = CreditCard.query.all()
    cards_with_available = []
    
    for card in cards:
        # Calcular o limite disponível (limite total - soma das transações do cartão)
        card_transactions = Transaction.query.filter_by(credit_card_id=card.id, trans_type='saida').all()
        used_limit = sum(txn.value for txn in card_transactions)
        available_limit = card.limit - used_limit
        
        # Calcular próxima data de vencimento
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        
        # Se o dia de vencimento já passou este mês, a próxima data é no próximo mês
        if today.day > card.due_day:
            if current_month == 12:
                next_due_month = 1
                next_due_year = current_year + 1
            else:
                next_due_month = current_month + 1
                next_due_year = current_year
        else:
            next_due_month = current_month
            next_due_year = current_year
        
        next_due_date = datetime(next_due_year, next_due_month, card.due_day).date()
        
        cards_with_available.append({
            'id': card.id,
            'name': card.name,
            'limit': card.limit,
            'available_limit': available_limit,
            'due_day': card.due_day,
            'closing_day': card.closing_day,
            'next_due_date': next_due_date.strftime('%d-%b-%Y')
        })
    
    return render_template('credit_cards.html', credit_cards=cards_with_available)

# Rota para adicionar um cartão de crédito
@app.route('/credit_cards/add', methods=['POST'])
def add_credit_card():
    if request.method == 'POST':
        name = request.form.get('name')
        limit_str = request.form.get('limit')
        due_day_str = request.form.get('due_day')
        closing_day_str = request.form.get('closing_day')
        
        if not name or not limit_str or not due_day_str or not closing_day_str:
            flash("Todos os campos são obrigatórios.", 'danger')
            return redirect(url_for('credit_cards'))
        
        try:
            limit = float(limit_str.replace(',', '.'))
            due_day = int(due_day_str)
            closing_day = int(closing_day_str)
            
            if due_day < 1 or due_day > 31 or closing_day < 1 or closing_day > 31:
                flash("Os dias de vencimento e fechamento devem estar entre 1 e 31.", 'danger')
                return redirect(url_for('credit_cards'))
                
        except ValueError:
            flash("Valores inválidos para limite ou dias.", 'danger')
            return redirect(url_for('credit_cards'))
        
        new_card = CreditCard(
            name=name,
            limit=limit,
            due_day=due_day,
            closing_day=closing_day,
            user_id=current_user.id
        )
        
        db.session.add(new_card)
        db.session.commit()
        
        flash("Cartão de crédito adicionado com sucesso!", 'success')
        return redirect(url_for('credit_cards'))

# Rota para obter detalhes de um cartão
@app.route('/credit_cards/<int:card_id>')
def get_credit_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    
    # Calcular o limite disponível
    card_transactions = Transaction.query.filter_by(credit_card_id=card.id, trans_type='saida').all()
    used_limit = sum(txn.value for txn in card_transactions)
    available_limit = card.limit - used_limit
    
    # Calcular próxima data de vencimento
    today = datetime.now().date()
    current_month = today.month
    current_year = today.year
    
    # Se o dia de vencimento já passou este mês, a próxima data é no próximo mês
    if today.day > card.due_day:
        if current_month == 12:
            next_due_month = 1
            next_due_year = current_year + 1
        else:
            next_due_month = current_month + 1
            next_due_year = current_year
    else:
        next_due_month = current_month
        next_due_year = current_year
    
    next_due_date = datetime(next_due_year, next_due_month, card.due_day).date()
    
    # Obter transações da fatura atual
    # Determinar o período da fatura atual (do fechamento anterior até o próximo fechamento)
    if today.day >= card.closing_day:
        # Estamos após o fechamento deste mês, então a fatura vai do fechamento deste mês até o próximo
        if current_month == 12:
            next_closing_month = 1
            next_closing_year = current_year + 1
        else:
            next_closing_month = current_month + 1
            next_closing_year = current_year
            
        start_date = datetime(current_year, current_month, card.closing_day).date()
        end_date = datetime(next_closing_year, next_closing_month, card.closing_day).date()
    else:
        # Estamos antes do fechamento deste mês, então a fatura vai do fechamento do mês anterior até este mês
        if current_month == 1:
            prev_closing_month = 12
            prev_closing_year = current_year - 1
        else:
            prev_closing_month = current_month - 1
            prev_closing_year = current_year
            
        start_date = datetime(prev_closing_year, prev_closing_month, card.closing_day).date()
        end_date = datetime(current_year, current_month, card.closing_day).date()
    
    # Buscar transações no período da fatura
    invoice_transactions = Transaction.query.filter(
        Transaction.credit_card_id == card.id,
        Transaction.trans_type == 'saida',
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).order_by(Transaction.date.desc()).all()
    
    # Formatar transações para JSON
    transactions_json = []
    for txn in invoice_transactions:
        transactions_json.append({
            'id': txn.id,
            'date': txn.date.strftime('%d-%b-%Y'),
            'description': txn.description,
            'value': txn.value,
            'category': txn.category
        })
    
    return jsonify({
        'success': True,
        'card': {
            'id': card.id,
            'name': card.name,
            'limit': card.limit,
            'available_limit': available_limit,
            'due_day': card.due_day,
            'closing_day': card.closing_day,
            'next_due_date': next_due_date.strftime('%d-%b-%Y')
        },
        'transactions': transactions_json
    })

# Rota para atualizar um cartão
@app.route('/credit_cards/<int:card_id>', methods=['POST'])
def update_credit_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    
    name = request.form.get('name')
    limit_str = request.form.get('limit')
    due_day_str = request.form.get('due_day')
    closing_day_str = request.form.get('closing_day')
    
    if not name or not limit_str or not due_day_str or not closing_day_str:
        return jsonify({'success': False, 'message': 'Todos os campos são obrigatórios.'})
    
    try:
        limit = float(limit_str.replace(',', '.'))
        due_day = int(due_day_str)
        closing_day = int(closing_day_str)
        
        if due_day < 1 or due_day > 31 or closing_day < 1 or closing_day > 31:
            return jsonify({'success': False, 'message': 'Os dias de vencimento e fechamento devem estar entre 1 e 31.'})
            
    except ValueError:
        return jsonify({'success': False, 'message': 'Valores inválidos para limite ou dias.'})
    
    card.name = name
    card.limit = limit
    card.due_day = due_day
    card.closing_day = closing_day
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Cartão atualizado com sucesso!'})

# Rota para excluir um cartão
@app.route('/credit_cards/delete/<int:card_id>', methods=['POST'])
def delete_credit_card(card_id):
    card = CreditCard.query.get_or_404(card_id)
    
    # Desvincular transações associadas a este cartão
    transactions = Transaction.query.filter_by(credit_card_id=card.id).all()
    for txn in transactions:
        txn.credit_card_id = None
    
    db.session.delete(card)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Cartão excluído com sucesso!'})

# Rota para a página de saldo diário
@app.route('/daily_balance')
@login_required
def daily_balance():
    # Obter todas as transações ordenadas por data
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date).all()
    
    # Obter todos os cartões de crédito
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id).all()
    
    # Dicionário para armazenar saldo por dia
    daily_balances = {}
    
    # Data atual
    current_date = datetime.now().date()
    
    # Calcular saldo acumulado e transações por dia
    accumulated_balance = 0.0
    
    # Processar transações passadas
    for txn in transactions:
        date_str = txn.date.strftime("%d-%b-%Y")
        
        # Inicializar o registro do dia se não existir
        if date_str not in daily_balances:
            daily_balances[date_str] = {
                'date': date_str,
                'income': 0.0,
                'expense': 0.0,
                'daily_balance': 0.0,
                'accumulated_balance': 0.0,
                'transactions': []
            }
        
        # Atualizar valores do dia
        if txn.trans_type == 'entrada':
            daily_balances[date_str]['income'] += txn.value
            accumulated_balance += txn.value
        elif txn.trans_type == 'saida':
            daily_balances[date_str]['expense'] += txn.value
            accumulated_balance -= txn.value
        
        # Calcular saldo do dia
        daily_balances[date_str]['daily_balance'] = daily_balances[date_str]['income'] - daily_balances[date_str]['expense']
        daily_balances[date_str]['accumulated_balance'] = accumulated_balance
        
        # Adicionar transação à lista do dia
        daily_balances[date_str]['transactions'].append({
            'id': txn.id,
            'description': txn.description,
            'value': txn.value,
            'trans_type': txn.trans_type,
            'category': txn.category
        })
    
    # Projetar saldo para os próximos 365 dias
    projected_balance = accumulated_balance
    
    # Filtrar transações futuras (transações recorrentes e agendadas)
    future_transactions = [t for t in transactions if t.date > current_date]
    
    # Gerar datas para os próximos 365 dias
    for i in range(1, 366):  # Começando de 1 para não incluir o dia atual novamente
        future_date = current_date + timedelta(days=i)
        date_str = future_date.strftime("%d-%b-%Y")
        
        # Inicializar o registro do dia
        if date_str not in daily_balances:
            daily_balances[date_str] = {
                'date': date_str,
                'income': 0.0,
                'expense': 0.0,
                'daily_balance': 0.0,
                'accumulated_balance': projected_balance,  # Usar o saldo projetado atual
                'transactions': []
            }
        
        # Filtrar transações para este dia específico
        day_transactions = [t for t in future_transactions if t.date == future_date]
        
        # Calcular mudança no saldo para o dia
        day_income = 0.0
        day_expense = 0.0
        
        for txn in day_transactions:
            if txn.trans_type == 'entrada':
                day_income += txn.value
                projected_balance += txn.value
            elif txn.trans_type == 'saida':
                day_expense += txn.value
                projected_balance -= txn.value
            
            # Adicionar transação à lista do dia
            daily_balances[date_str]['transactions'].append({
                'id': txn.id,
                'description': txn.description,
                'value': txn.value,
                'trans_type': txn.trans_type,
                'category': txn.category
            })
        
        # Atualizar valores do dia
        daily_balances[date_str]['income'] = day_income
        daily_balances[date_str]['expense'] = day_expense
        daily_balances[date_str]['daily_balance'] = day_income - day_expense
        daily_balances[date_str]['accumulated_balance'] = projected_balance
    
    # Processar informações de faturas de cartões de crédito
    credit_card_data = []
    
    for card in credit_cards:
        card_data = {
            'id': card.id,
            'name': card.name,
            'due_dates': []
        }
        
        # Calcular datas de vencimento e valores das faturas para os próximos 12 meses
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        
        for i in range(12):
            # Calcular mês e ano do vencimento
            due_month = (current_month + i) % 12
            if due_month == 0:
                due_month = 12
            due_year = current_year + ((current_month + i - 1) // 12)
            
            # Ajustar para o último dia do mês se o dia de vencimento for maior
            last_day_of_month = 31  # Simplificação, poderia ser mais preciso
            if due_month in [4, 6, 9, 11]:
                last_day_of_month = 30
            elif due_month == 2:
                # Verificar se é ano bissexto
                if due_year % 4 == 0 and (due_year % 100 != 0 or due_year % 400 == 0):
                    last_day_of_month = 29
                else:
                    last_day_of_month = 28
            
            due_day = min(card.due_day, last_day_of_month)
            due_date = datetime(due_year, due_month, due_day).date()
            
            # Calcular mês de fechamento (mês anterior ao vencimento)
            if due_month == 1:
                closing_month = 12
                closing_year = due_year - 1
            else:
                closing_month = due_month - 1
                closing_year = due_year
            
            closing_day = min(card.closing_day, last_day_of_month)
            closing_date = datetime(closing_year, closing_month, closing_day).date()
            
            # Calcular próxima data de fechamento
            if due_month == 12:
                next_closing_month = 1
                next_closing_year = due_year + 1
            else:
                next_closing_month = due_month + 1
                next_closing_year = due_year
            
            next_closing_day = min(card.closing_day, last_day_of_month)
            next_closing_date = datetime(next_closing_year, next_closing_month, next_closing_day).date()
            
            # Buscar transações no período da fatura
            invoice_transactions = Transaction.query.filter(
                Transaction.credit_card_id == card.id,
                Transaction.trans_type == 'saida',
                Transaction.date > closing_date,
                Transaction.date <= next_closing_date
            ).all()
            
            # Calcular valor total da fatura (apenas parcelas do mês atual)
            invoice_amount = sum(txn.value for txn in invoice_transactions if txn.date.month == due_date.month and txn.date.year == due_date.year)
            
            # Verificar se a fatura já foi paga (simplificação)
            is_paid = due_date < today
            
            # Adicionar à lista de vencimentos se houver valor
            if invoice_amount > 0:
                card_data['due_dates'].append({
                    'date': due_date.strftime("%d-%b-%Y"),
                    'amount': invoice_amount,
                    'paid': is_paid
                })
        
        credit_card_data.append(card_data)
    
    # Converter para lista e incluir todos os dias, não apenas os que têm transações
    # Isso garante que o saldo acumulado seja contínuo
    daily_balance_list = list(daily_balances.values())
    
    # Ordenar por data (mais antiga primeiro)
    daily_balance_list.sort(key=lambda x: datetime.strptime(x['date'], "%d-%b-%Y"))
    
    # Garantir que o saldo acumulado seja progressivo
    prev_balance = 0.0
    for i, day_data in enumerate(daily_balance_list):
        if i > 0:
            prev_balance = daily_balance_list[i-1]['accumulated_balance']
            day_data['accumulated_balance'] = prev_balance + day_data['daily_balance']
    
    # Filtrar dias sem movimentações para o gráfico, mas manter todos os dias para cálculos
    # Isso será usado apenas no frontend, o filtro final será feito no JavaScript
    
    return render_template('daily_balance.html', 
                           daily_balance_data=daily_balance_list,
                           credit_card_data=credit_card_data)

# Rota para exibir faturas pendentes e calcular saldo após pagamento
@app.route('/pending_invoices')
@login_required
def pending_invoices():
    # Obter todas as transações para calcular o saldo atual
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date).all()
    
    # Calcular saldo atual
    current_balance = 0.0
    current_date = datetime.now().date()
    
    for txn in transactions:
        if txn.date <= current_date:
            if txn.trans_type == 'entrada':
                current_balance += txn.value
            elif txn.trans_type == 'saida':
                current_balance -= txn.value
    
    # Obter todos os cartões de crédito
    credit_cards = CreditCard.query.filter_by(user_id=current_user.id).all()
    
    # Lista para armazenar faturas pendentes
    pending_invoices = []
    
    for card in credit_cards:
        # Calcular datas de vencimento e valores das faturas para os próximos 6 meses
        today = datetime.now().date()
        current_month = today.month
        current_year = today.year
        
        for i in range(6):
            # Calcular mês e ano do vencimento
            due_month = (current_month + i) % 12
            if due_month == 0:
                due_month = 12
            due_year = current_year + ((current_month + i - 1) // 12)
            
            # Ajustar para o último dia do mês se o dia de vencimento for maior
            last_day_of_month = 31  # Simplificação, poderia ser mais preciso
            if due_month in [4, 6, 9, 11]:
                last_day_of_month = 30
            elif due_month == 2:
                # Verificar se é ano bissexto
                if due_year % 4 == 0 and (due_year % 100 != 0 or due_year % 400 == 0):
                    last_day_of_month = 29
                else:
                    last_day_of_month = 28
            
            due_day = min(card.due_day, last_day_of_month)
            due_date = datetime(due_year, due_month, due_day).date()
            
            # Calcular mês de fechamento (mês anterior ao vencimento)
            if due_month == 1:
                closing_month = 12
                closing_year = due_year - 1
            else:
                closing_month = due_month - 1
                closing_year = due_year
            
            closing_day = min(card.closing_day, last_day_of_month)
            closing_date = datetime(closing_year, closing_month, closing_day).date()
            
            # Calcular próxima data de fechamento
            if due_month == 12:
                next_closing_month = 1
                next_closing_year = due_year + 1
            else:
                next_closing_month = due_month + 1
                next_closing_year = due_year
            
            next_closing_day = min(card.closing_day, last_day_of_month)
            next_closing_date = datetime(next_closing_year, next_closing_month, next_closing_day).date()
            
            # Buscar transações no período da fatura
            invoice_transactions = Transaction.query.filter(
                Transaction.credit_card_id == card.id,
                Transaction.trans_type == 'saida',
                Transaction.date > closing_date,
                Transaction.date <= next_closing_date
            ).all()
            
            # Calcular valor total da fatura
            # Para transações recorrentes, considerar apenas se o mês/ano da transação corresponde ao mês/ano da fatura
            # Para transações não recorrentes, considerar todas dentro do período de fechamento
            invoice_amount = 0
            filtered_transactions = []
            for txn in invoice_transactions:
                if txn.is_recurring:
                    # Se for recorrente, só incluir se o mês/ano da transação corresponder ao mês/ano do vencimento
                    if txn.date.month == due_month and txn.date.year == due_year:
                        invoice_amount += txn.value
                        filtered_transactions.append(txn)
                else:
                    # Se não for recorrente, incluir se estiver dentro do período de fechamento
                    invoice_amount += txn.value
                    filtered_transactions.append(txn)
            
            # Atualizar a lista de transações para exibição
            invoice_transactions = filtered_transactions
            
            # Verificar se a fatura já foi paga (simplificação)
            is_paid = due_date < today
            
            # Adicionar à lista de faturas pendentes se não estiver paga e tiver valor
            if not is_paid and invoice_amount > 0:
                # Formatar transações para exibição
                formatted_transactions = []
                for txn in invoice_transactions:
                    formatted_transactions.append({
                        'date': txn.date.strftime("%d-%b-%Y"),
                        'description': txn.description,
                        'value': txn.value,
                        'category': txn.category
                    })
                
                pending_invoices.append({
                    'card_id': card.id,
                    'card_name': card.name,
                    'due_date': due_date.strftime("%d-%b-%Y"),
                    'amount': invoice_amount,
                    'transactions': formatted_transactions
                })
    
    return render_template('pending_invoices.html', 
                           pending_invoices=pending_invoices,
                           current_balance=current_balance)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas se não existirem.
    app.run(host='0.0.0.0', port=26603, debug=True)