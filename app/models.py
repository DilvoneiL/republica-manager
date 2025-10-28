# models.py (VERSÃO CORRETA E ATUALIZADA)

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid # Para gerar IDs de parcelamento

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    cargo = db.Column(db.String(20), nullable=False, default='usuario')

    # --- CAMPO PARA TIPO DE QUARTO ---
    # A lógica em financas.py espera 'individual' ou 'compartilhado' (lowercase)
    tipo_quarto = db.Column(db.String(50), nullable=False, default='compartilhado')

    # --- RELACIONAMENTOS FINANCEIROS (ATUALIZADOS) ---
    # Um usuário faz vários lançamentos (quem pagou)
    lancamentos = db.relationship('Lancamento', backref='autor', lazy=True, foreign_keys='Lancamento.user_id')
    
    # (REMOVIDO 'gastos_atribuidos' pois 'atribuido_a_user_id' não é mais usado)

    # Um usuário tem um saldo por mês fechado
    saldos_mensais = db.relationship('SaldoMensal', backref='usuario', lazy=True)
    # Um usuário pode fazer retiradas do caixinha
    retiradas_caixinha = db.relationship('CaixinhaMovimentacao', backref='usuario_retirada', lazy=True)
    # Um usuário tem suas próprias despesas fixas (Aluguel)
    despesas_fixas_individuais = db.relationship('DespesaFixa', backref='morador', lazy=True, foreign_keys='DespesaFixa.morador_id')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.cargo == 'admin'

    def is_gerenciador(self):
        return self.cargo in ['admin', 'gerenciador']

# --- MODELO ConfiguracaoAluguel (REMOVIDO) ---
# --- MODELO ValorAluguel (REMOVIDO) ---


# --- MODELO LANCAMENTO (CORRIGIDO E SIMPLIFICADO) ---
class Lancamento(db.Model):
    __tablename__ = 'lancamentos'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default='Outros')
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    mes_referencia = db.Column(db.Integer, nullable=False)
    ano_referencia = db.Column(db.Integer, nullable=False)
    
    # user_id = Quem pagou (recebe o crédito). Nulo = pago pela "Casa"
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True) 

    # --- PARCELAMENTO ---
    parcelamento_id = db.Column(db.String(36), nullable=True, index=True)
    parcela_atual = db.Column(db.Integer, nullable=True)
    parcela_total = db.Column(db.Integer, nullable=True)
    valor_total_compra = db.Column(db.Float, nullable=True)

    # --- (REMOVIDO 'atribuido_a_user_id') ---

    def is_parcelado(self):
        return self.parcelamento_id is not None

    def is_gasto_da_casa(self):
        # Um gasto é da casa se NINGUÉM pagou por ele (user_id=None)
        return self.user_id is None

# --- MODELO FECHAMENTO MENSAL (Mantido como estava) ---
class FechamentoMensal(db.Model):
    __tablename__ = 'fechamento_mensal'
    id = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    # Total fixo SEM aluguel e SEM caixinha (despesas gerais)
    total_fixo = db.Column(db.Float, nullable=False) 
    # Total variável APENAS DA CASA (todos lançamentos são da casa)
    total_variavel = db.Column(db.Float, nullable=False) 
    # Valor total do aluguel PAGO no mês (soma dos aluguéis individuais)
    total_aluguel_mes = db.Column(db.Float, nullable=False, default=0.0) 
    valor_caixinha_arrecadado = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(20), nullable=False, default='aberto')
    # Relacionamento com cascade (mantido)
    saldos = db.relationship('SaldoMensal', backref='fechamento', lazy=True, cascade="all, delete-orphan")

# --- MODELO SALDO MENSAL (Mantido como estava) ---
class SaldoMensal(db.Model):
    __tablename__ = 'saldo_mensal'
    id = db.Column(db.Integer, primary_key=True)
    fechamento_id = db.Column(db.Integer, db.ForeignKey('fechamento_mensal.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # O que o usuário LANÇOU no mês (crédito)
    total_gasto = db.Column(db.Float, nullable=False)
    # O valor TOTAL que ele efetivamente DEVE pagar (débito)
    valor_devido = db.Column(db.Float, nullable=False)
    
    # Detalhamento do valor devido (para clareza no relatório)
    valor_devido_aluguel = db.Column(db.Float, nullable=True) # Valor fixo do seu aluguel
    valor_devido_outros = db.Column(db.Float, nullable=True)  # Sua cota das despesas gerais
    valor_devido_pessoais = db.Column(db.Float, nullable=True, default=0.0) # (Não usado na lógica atual)
    
    # Saldo final = total_gasto (crédito) - valor_devido (débito)
    saldo_final = db.Column(db.Float, nullable=False)
    status_pagamento = db.Column(db.String(30), nullable=False, default='pendente')

# --- MODELO DESPESA FIXA (MUDANÇA CRÍTICA) ---
class DespesaFixa(db.Model):
    __tablename__ = 'despesas_fixas'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    ativa = db.Column(db.Boolean, default=True)

    # --- NOVAS COLUNAS PARA O CÁLCULO DINÂMICO ---

    # 1. Relaciona a despesa a um morador específico (ex: Aluguel da Ana)
    #    Se for NULO, é uma despesa geral (ex: Internet, Caixinha)
    morador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True, default=None)

    # 2. Campo usado APENAS na despesa "mestre" de Aluguel (a que tem morador_id=None)
    #    para guardar a diferença de valor.
    diferenca_individual = db.Column(db.Float, nullable=True, default=0.0)


# --- Outros Modelos (Mantidos) ---

class CaixinhaMovimentacao(db.Model):
    __tablename__ = 'caixinha_movimentacao'
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    descricao = db.Column(db.String(200), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

class EscalaSemanal(db.Model):
    __tablename__ = 'escala_semanal'
    id = db.Column(db.Integer, primary_key=True)
    semana = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    tarefa = db.Column(db.String(200), nullable=False)
    responsavel = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    tipo = db.Column(db.String(20), nullable=False, default='recorrente')

class Tarefa(db.Model):
    __tablename__ = 'tarefas'
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(200), nullable=False)
    recorrente = db.Column(db.Boolean, default=True)