# app/admin.py (CORRIGIDO E ATUALIZADO)

from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
# --- REMOVIDO: ValorAluguel ---
from .models import db, User
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from .models import CaixinhaMovimentacao # Adicione esta importação no topo do arquivo se ainda não tiver
# --- DECORATORS PARA SEGURANÇA (Mantidos) ---
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
    
    # --- REMOVIDO 'tipos_quarto_map' ---
    # O seu template 'usuarios.html' agora deve ser alterado para
    # simplesmente exibir a string 'usuario.tipo_quarto'
    
    return render_template('usuarios.html', usuarios=usuarios)

@admin_bp.route('/usuarios/criar', methods=['GET', 'POST'])
@login_required
@manager_required
def criar_usuario():
    # --- ATUALIZADO: Tipos de quarto agora são fixos (hardcoded) ---
    # Estes são os valores que a sua lógica em 'routes_aluguel.py' espera
    tipos_quarto_disponiveis = ['individual', 'compartilhado']

    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password')
        cargo = request.form.get('cargo')
        tipo_quarto = request.form.get('tipo_quarto')

        if not username or not password or not cargo or not tipo_quarto:
            flash('Todos os campos (Nome, Senha, Cargo, Tipo Quarto) são obrigatórios.', 'warning')
            return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis, username=username, cargo=cargo, tipo_quarto=tipo_quarto)

        if User.query.filter_by(username=username).first():
            flash('Este nome de utilizador já existe.', 'danger')
            return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis, username=username, cargo=cargo, tipo_quarto=tipo_quarto)

        if cargo == 'admin' and not current_user.is_admin():
            flash('Apenas administradores podem criar outros administradores.', 'danger')
            return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis, username=username, cargo='gerenciador', tipo_quarto=tipo_quarto)

        # --- ATUALIZADO: Valida se tipo_quarto é válido ---
        if tipo_quarto not in tipos_quarto_disponiveis:
              flash(f'Tipo de quarto inválido. Use um dos: {", ".join(tipos_quarto_disponiveis)}', 'danger')
              return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis, username=username, cargo=cargo, tipo_quarto=tipo_quarto)

        try: 
            novo_usuario = User(username=username, cargo=cargo, tipo_quarto=tipo_quarto)
            novo_usuario.set_password(password)
            db.session.add(novo_usuario)
            db.session.commit()

            flash(f'Utilizador "{username}" criado com sucesso!', 'success')
            return redirect(url_for('admin.lista_usuarios'))
        except Exception as e: 
            db.session.rollback()
            flash(f'Erro ao criar usuário: {e}', 'danger')
            return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis, username=username, cargo=cargo, tipo_quarto=tipo_quarto)

    # Método GET
    return render_template('criar_usuario.html', tipos_quarto=tipos_quarto_disponiveis)

@admin_bp.route('/usuarios/editar/<int:user_id>', methods=['GET', 'POST'])
@login_required
@manager_required
def edit_usuario(user_id):
    user_alvo = User.query.get_or_404(user_id)
    if user_alvo.is_admin() and not current_user.is_admin():
        flash('Acesso negado: você não pode editar um administrador.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))

    # --- ATUALIZADO: Tipos de quarto agora são fixos (hardcoded) ---
    tipos_quarto_disponiveis = ['individual', 'compartilhado']

    if request.method == 'POST':
        novo_username = request.form.get('username', '').strip().lower()
        password = request.form.get('password')
        cargo = request.form.get('cargo')
        tipo_quarto = request.form.get('tipo_quarto')

        if not novo_username or not cargo or not tipo_quarto:
              flash('Nome de usuário, cargo e tipo de quarto são obrigatórios.', 'warning')
              return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)

        existing_user = User.query.filter(User.username == novo_username, User.id != user_id).first()
        if existing_user:
            flash('Este nome de utilizador já está em uso por outro usuário.', 'danger')
            return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)

        if cargo == 'admin' and not current_user.is_admin():
            flash('Apenas administradores podem definir o cargo de administrador.', 'danger')
            return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)

        # --- ATUALIZADO: Valida se tipo_quarto é válido ---
        if tipo_quarto not in tipos_quarto_disponiveis:
              flash(f'Tipo de quarto inválido. Use um dos: {", ".join(tipos_quarto_disponiveis)}', 'danger')
              return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)

        try: 
            user_alvo.username = novo_username
            user_alvo.cargo = cargo
            user_alvo.tipo_quarto = tipo_quarto
            if password:
                user_alvo.set_password(password)

            db.session.commit()
            flash(f'Utilizador "{user_alvo.username}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin.lista_usuarios'))
        except Exception as e: 
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {e}', 'danger')
            return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)

    # Método GET
    return render_template('criar_usuario.html', user_alvo=user_alvo, tipos_quarto=tipos_quarto_disponiveis)


@admin_bp.route('/usuarios/deletar/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(user_id):
    user_alvo = User.query.get_or_404(user_id)
    if user_alvo.id == current_user.id:
        flash('Você não pode remover o seu próprio perfil.', 'danger')
        return redirect(url_for('admin.lista_usuarios'))

    if user_alvo.is_admin():
        admin_count = User.query.filter_by(cargo='admin').count()
        if admin_count <= 1:
            flash('Não é possível remover o único administrador.', 'danger')
            return redirect(url_for('admin.lista_usuarios'))

    try: 
        username_alvo = user_alvo.username
        db.session.delete(user_alvo)
        db.session.commit()
        flash(f'Utilizador "{username_alvo}" removido com sucesso.', 'success')
    except Exception as e: 
        db.session.rollback()
        flash(f'Erro ao remover usuário "{username_alvo}": {e}. Verifique dependências.', 'danger')

    return redirect(url_for('admin.lista_usuarios'))


# --- ROTA PARA GERENCIAR VALORES DE ALUGUEL (REMOVIDA) ---
# A rota @admin_bp.route('/gerenciar_alugueis', ...) foi completamente removida.
# A funcionalidade agora pertence ao blueprint 'financas'
# na rota 'financas.gerenciar_aluguel'.

# (No final do arquivo app/admin.py)

# --- NOVA ROTA: Adicionar Saldo Manualmente ao Caixinha (Admin Only) ---


@admin_bp.route('/caixinha/adicionar_saldo', methods=['GET', 'POST'])
@login_required
@admin_required # Garante que só o admin pode acessar
def adicionar_saldo_caixinha_manual():
    if request.method == 'POST':
        descricao = request.form.get('descricao')
        valor_str = request.form.get('valor')

        # Validações
        if not descricao or not valor_str:
            flash('Descrição e Valor são obrigatórios.', 'danger')
            return render_template('admin/adicionar_saldo_caixinha.html') # Re-renderiza o form

        try:
            valor = float(valor_str.replace(',', '.'))
            if valor <= 0:
                flash('O valor a ser adicionado deve ser positivo.', 'danger')
                return render_template('admin/adicionar_saldo_caixinha.html', descricao=descricao, valor=valor_str)
        except ValueError:
            flash('Valor inválido.', 'danger')
            return render_template('admin/adicionar_saldo_caixinha.html', descricao=descricao, valor=valor_str)

        # Cria a movimentação
        try:
            nova_entrada = CaixinhaMovimentacao(
                descricao=f"Ajuste manual ADM: {descricao}", # Adiciona prefixo para clareza
                valor=valor, # Valor positivo é entrada
                user_id=current_user.id # Registra qual admin fez
            )
            db.session.add(nova_entrada)
            db.session.commit()
            flash(f'Valor R$ {valor:.2f} adicionado ao caixinha com sucesso!', 'success')
            # Redireciona de volta para o form ou para o dashboard do tesoureiro para ver o resultado
            return redirect(url_for('financas.dashboard_tesoureiro')) 
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao adicionar saldo: {e}', 'danger')

    # Método GET: Apenas mostra o formulário
    return render_template('admin/adicionar_saldo_caixinha.html')