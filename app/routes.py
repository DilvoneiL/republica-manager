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
        # CORREÇÃO AQUI: .strip() remove espaços do início e do fim
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        
        username_lower = form.username.data.lower()
        user = User.query.filter_by(username= username_lower).first()

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

