from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from .models import db, User
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- DECORATORS PARA SEGURANÇA ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403) # Proibido
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_gerenciador():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE GESTÃO DE UTILIZADORES ---
@admin_bp.route('/usuarios')
@login_required
@manager_required
def lista_usuarios():
    if current_user.is_admin():
        usuarios = User.query.order_by(User.username).all()
    else:
        usuarios = User.query.filter(User.cargo != 'admin').order_by(User.username).all()
    return render_template('usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/criar', methods=['GET', 'POST'])
@login_required
@manager_required
def criar_usuario():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        cargo = request.form.get('cargo')

        if not username or not password or not cargo:
            flash('Todos os campos são obrigatórios.', 'warning')
            return redirect(url_for('admin.criar_usuario'))
        
        if User.query.filter_by(username=username).first():
            flash('Este nome de utilizador já existe.', 'danger')
            return redirect(url_for('admin.criar_usuario'))
        
        if cargo == 'admin' and not current_user.is_admin():
            flash('Apenas administradores podem criar outros administradores.', 'danger')
            return redirect(url_for('admin.criar_usuario'))

        novo_usuario = User(username=username, cargo=cargo)
        novo_usuario.set_password(password)
        db.session.add(novo_usuario)
        db.session.commit()
        
        flash(f'Utilizador "{username}" criado com sucesso!', 'success')
        return redirect(url_for('admin.lista_usuarios'))

    return render_template('criar_usuario.html')

@admin_bp.route('/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_usuario(user_id):
    user_alvo = User.query.get_or_404(user_id)
    if user_alvo.is_admin() and not current_user.is_admin():
        flash('Acesso negado: você não pode editar um administrador.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))

    if request.method == 'POST':
        novo_username = request.form.get('username', '').strip()
        password = request.form.get('password')
        cargo = request.form.get('cargo')

        existing_user = User.query.filter_by(username=novo_username).first()
        if existing_user and existing_user.id != user_alvo.id:
            flash('Este nome de utilizador já está em uso.', 'danger')
            return render_template('criar_usuario.html', user_alvo=user_alvo)

        if cargo == 'admin' and not current_user.is_admin():
            flash('Apenas administradores podem definir o cargo de administrador.', 'danger')
            return render_template('criar_usuario.html', user_alvo=user_alvo)

        user_alvo.username = novo_username
        user_alvo.cargo = cargo
        if password:
            user_alvo.set_password(password)
        
        db.session.commit()
        flash(f'Utilizador "{user_alvo.username}" atualizado com sucesso!', 'success')
        return redirect(url_for('admin.lista_usuarios'))

    return render_template('criar_usuario.html', user_alvo=user_alvo)


@admin_bp.route('/usuarios/deletar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(user_id):
    user_alvo = User.query.get_or_404(user_id)
    if user_alvo.id == current_user.id:
        flash('Você não pode remover o seu próprio perfil.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))
    
    if user_alvo.is_admin():
        flash('Não é possível remover um administrador.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))

    username_alvo = user_alvo.username
    db.session.delete(user_alvo)
    db.session.commit()

    flash(f'Utilizador "{username_alvo}" removido com sucesso.', 'success')
    return redirect(url_for('admin.lista_usuarios'))

