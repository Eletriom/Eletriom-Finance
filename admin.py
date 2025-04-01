# Módulo para funcionalidades administrativas
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
import os
import sqlite3
import logging
from datetime import datetime, timedelta, date
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='admin.log',
    filemode='a'
)

logger = logging.getLogger('admin')

# Criar blueprint para rotas administrativas
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Variáveis globais que serão configuradas durante a inicialização
db = None
User = None
Transaction = None
CreditCard = None

# Função para inicializar o módulo admin com as dependências necessárias
def init_admin(app_db, app_User, app_Transaction, app_CreditCard):
    global db, User, Transaction, CreditCard
    db = app_db
    User = app_User
    Transaction = app_Transaction
    CreditCard = app_CreditCard

# Decorador para verificar se o usuário é administrador
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Acesso negado. Você precisa ser um administrador para acessar esta página.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Função para registrar ações administrativas
def log_admin_action(action, details=None):
    logger.info(f"Admin action: {action} | User: {current_user.email} | Details: {details}")

# Rota principal do painel administrativo
@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    # Usar os modelos já importados no início do arquivo
    
    # Contagem de usuários
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    inactive_users = User.query.filter_by(active=False).count()
    
    # Contagem de transações
    total_transactions = Transaction.query.count()
    
    # Estatísticas de cartões de crédito
    total_credit_cards = CreditCard.query.count()
    
    # Usuários recentes
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Transações recentes
    recent_transactions = Transaction.query.order_by(Transaction.date.desc()).limit(5).all()
    
    # Tamanho do banco de dados
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    db_size_mb = db_size / (1024 * 1024)  # Converter para MB
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           active_users=active_users,
                           inactive_users=inactive_users,
                           total_transactions=total_transactions,
                           total_credit_cards=total_credit_cards,
                           recent_users=recent_users,
                           recent_transactions=recent_transactions,
                           db_size_mb=db_size_mb)

# Rota para gerenciar usuários
@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    # Usar os modelos já importados no início do arquivo
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Rota para editar usuário
@admin_bp.route('/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    # Usar os modelos já importados no início do arquivo
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.active = 'active' in request.form
        user.is_admin = 'is_admin' in request.form
        
        # Se uma nova senha foi fornecida
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        log_admin_action(f"Usuário editado", f"ID: {user.id}, Email: {user.email}")
        flash(f'Usuário {user.name} atualizado com sucesso!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', user=user)

# Rota para excluir usuário
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Usar os modelos já importados no início do arquivo
    
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Você não pode excluir sua própria conta!', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    # Registrar informações antes de excluir
    user_info = f"ID: {user.id}, Nome: {user.name}, Email: {user.email}"
    
    # Excluir transações e cartões de crédito associados
    Transaction.query.filter_by(user_id=user.id).delete()
    CreditCard.query.filter_by(user_id=user.id).delete()
    
    db.session.delete(user)
    db.session.commit()
    
    log_admin_action("Usuário excluído", user_info)
    flash(f'Usuário {user.name} excluído com sucesso!', 'success')
    return redirect(url_for('admin.manage_users'))

# Rota para visualizar logs do sistema
@admin_bp.route('/logs')
@login_required
@admin_required
def view_logs():
    log_file = 'admin.log'
    logs = []
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            logs = f.readlines()
    
    # Inverter a ordem para mostrar os logs mais recentes primeiro
    logs.reverse()
    
    return render_template('admin/logs.html', logs=logs)

# Rota para gerenciar banco de dados
@admin_bp.route('/database')
@login_required
@admin_required
def manage_database():
    # Usar current_app do Flask
    from flask import current_app
    
    # Obter estatísticas do banco de dados
    db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    db_size_mb = db_size / (1024 * 1024)  # Converter para MB
    
    # Obter informações sobre as tabelas
    tables_info = []
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            # Contar registros na tabela
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            tables_info.append({'name': table_name, 'count': count})
            
        conn.close()
    except Exception as e:
        flash(f'Erro ao acessar o banco de dados: {str(e)}', 'danger')
    
    return render_template('admin/database.html', 
                           db_size_mb=db_size_mb,
                           tables_info=tables_info)

# Rota para backup do banco de dados
@admin_bp.route('/database/backup', methods=['POST'])
@login_required
@admin_required
def backup_database():
    # Usar current_app do Flask
    from flask import current_app
    
    try:
        # Caminho do banco de dados original
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Criar nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"backup_{timestamp}.db"
        
        # Copiar o banco de dados
        import shutil
        shutil.copy2(db_path, backup_path)
        
        log_admin_action("Backup do banco de dados", f"Arquivo: {backup_path}")
        flash(f'Backup do banco de dados criado com sucesso: {backup_path}', 'success')
    except Exception as e:
        flash(f'Erro ao criar backup: {str(e)}', 'danger')
    
    return redirect(url_for('admin.manage_database'))

# Rota para estatísticas do sistema
@admin_bp.route('/stats')
@login_required
@admin_required
def system_stats():
    # Usar os modelos já importados no início do arquivo
    
    # Estatísticas de usuários
    total_users = User.query.count()
    users_last_30_days = User.query.filter(User.created_at >= datetime.now() - timedelta(days=30)).count()
    
    # Estatísticas de transações
    total_transactions = Transaction.query.count()
    transactions_last_30_days = Transaction.query.filter(
        Transaction.date >= date.today() - timedelta(days=30)
    ).count()
    
    # Valor total de transações
    income_query = db.session.query(db.func.sum(Transaction.value)).filter(Transaction.trans_type == 'entrada')
    expense_query = db.session.query(db.func.sum(Transaction.value)).filter(Transaction.trans_type == 'saida')
    
    total_income = income_query.scalar() or 0
    total_expense = expense_query.scalar() or 0
    
    # Estatísticas por mês (últimos 6 meses)
    months_data = []
    for i in range(5, -1, -1):
        month_date = datetime.now() - timedelta(days=30*i)
        month_start = datetime(month_date.year, month_date.month, 1).date()
        if month_date.month == 12:
            month_end = datetime(month_date.year + 1, 1, 1).date() - timedelta(days=1)
        else:
            month_end = datetime(month_date.year, month_date.month + 1, 1).date() - timedelta(days=1)
        
        # Contar transações do mês
        month_transactions = Transaction.query.filter(
            Transaction.date >= month_start,
            Transaction.date <= month_end
        ).count()
        
        # Somar valores do mês
        month_income = db.session.query(db.func.sum(Transaction.value)).filter(
            Transaction.date >= month_start,
            Transaction.date <= month_end,
            Transaction.trans_type == 'entrada'
        ).scalar() or 0
        
        month_expense = db.session.query(db.func.sum(Transaction.value)).filter(
            Transaction.date >= month_start,
            Transaction.date <= month_end,
            Transaction.trans_type == 'saida'
        ).scalar() or 0
        
        months_data.append({
            'month': month_date.strftime('%b/%Y'),
            'transactions': month_transactions,
            'income': month_income,
            'expense': month_expense
        })
    
    # Converter para JSON para uso em gráficos
    months_json = json.dumps(months_data)
    
    return render_template('admin/stats.html',
                           total_users=total_users,
                           users_last_30_days=users_last_30_days,
                           total_transactions=total_transactions,
                           transactions_last_30_days=transactions_last_30_days,
                           total_income=total_income,
                           total_expense=total_expense,
                           months_data=months_data,
                           months_json=months_json)