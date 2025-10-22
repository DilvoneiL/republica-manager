from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User

bp = Blueprint('routes', __name__)

@bp.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Pega o username do formulário, remove espaços e converte
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        # --- CORREÇÃO AQUI ---
        # Use a variável 'username' que você acabou de criar
        username_lower = username.lower()
        user = User.query.filter_by(username=username_lower).first()
        # --- FIM DA CORREÇÃO ---

        if not user or not user.check_password(password):
            flash('Usuário ou senha inválidos.')
            return redirect(url_for('routes.login'))
        
        login_user(user)
        return redirect(url_for('routes.index'))

    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

