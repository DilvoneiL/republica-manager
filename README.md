# 📋 República Manager

**Sistema de Gerenciamento de Tarefas e Escalas para Repúblicas**

Desenvolvido por **Dilvonei Lacerda**

---

## 📌 Introdução

O **República Manager** é um sistema web para gerenciamento de tarefas e escalas semanais em repúblicas, com controle de usuários, histórico preservado e rotação automática de responsáveis.

O sistema contempla:

- Arquitetura completa do sistema
- Geração automática de escala semanal
- Regras de rotação configuráveis
- Controle de usuários e permissões
- Tarefas recorrentes e avulsas
- Histórico imutável
- Manual completo de uso

---

## 🏗️ Arquitetura Geral do Sistema

Tecnologias utilizadas:

- **Flask** (backend)
- **Flask-Login** (autenticação)
- **SQLite** (banco de dados)
- **Jinja2** (templates)
- **Bootstrap 5** (UI/UX)

### Principais Módulos

- **models.py** – Define tabelas (Usuários, Tarefas, Escala Semanal)
- **escala.py** – Lógica de rotação, geração da escala e histórico
- **admin.py** – Gerenciamento de usuários e permissões
- **templates/** – Interfaces do sistema

---

## 🗄️ Banco de Dados

### Tabela: User

- id  
- username  
- password_hash  
- cargo (admin / gerenciador / usuario)  
- ordem_original  
- ordem_invertido  

### Tabela: Tarefa (Recorrente)

Define as tarefas fixas semanais da república.

### Tabela: EscalaSemanal

Registra:

- tarefa
- responsável
- semana
- status

---

## 🔄 Fluxo da Escala Semanal

A escala é gerada automaticamente quando:

- Um usuário acessa `/escala` pela primeira vez na semana
- O administrador altera tarefas base
- Uma semana ainda não possui registros

### Regras de Geração

1. Buscar tarefas recorrentes
2. Calcular responsáveis pela rotação
3. Criar apenas tarefas inexistentes

### Preservação do Histórico

- Alterações afetam apenas semanas atuais e futuras
- Semanas passadas permanecem inalteradas

---

## 🔁 Sistema de Rotação

### Modo `10_step2_inverte`

- Avança 2 pessoas por semana
- A cada 5 semanas inverte a ordem
- Ideal para 10 moradores

### Modo `flex_step1_sem_inversao`

- Avança 1 pessoa por semana
- Sem inversão
- Funciona para qualquer quantidade de usuários

### Seleção do Modo

<img width="1309" height="637" alt="Image" src="https://github.com/user-attachments/assets/003360ff-9f5e-450e-a1f2-b6fe5d333152" />

---

## 🧹 Tarefas Recorrentes

### Criar Tarefa Recorrente

<img width="1318" height="642" alt="Image" src="https://github.com/user-attachments/assets/0660c3bb-24c7-4ce1-b65e-f987dd486c7a" />


### Editar Tarefa Recorrente

- Altera descrição
- Afeta apenas semanas atuais/futuras
- Histórico permanece intacto

### Excluir Tarefa Recorrente

Remove a tarefa base e suas ocorrências futuras.

---

## ➕ Tarefas Avulsas

- Criadas apenas para uma semana específica
- Apenas admin/gerenciador
- Não interferem na rotação

<img width="1322" height="647" alt="Image" src="https://github.com/user-attachments/assets/2d156e00-d915-44dd-9ad4-ffd3338dfb66" />

---

## 📜 Histórico da Escala

O histórico exibe:

- Todas as semanas
- Responsáveis da época
- Tarefas específicas da semana

⚠️ **O histórico não é alterado após criado**

<img width="1292" height="625" alt="Image" src="https://github.com/user-attachments/assets/94175c55-14fd-4609-b258-a8103c11de1f" />

---

## 👥 Gerenciamento de Usuários

### Cargos

- **Administrador** – Controle total
- **Gerenciador** – Escalas, tarefas e usuários comuns
- **Usuário** – Apenas marca tarefas

### Criar Usuário

<img width="1312" height="638" alt="Image" src="https://github.com/user-attachments/assets/6b8b4eda-9497-4ff6-85f1-87f7538f5702" />
---

## 👤 Manual de Uso (Usuários)

- Marcar tarefa como feita
- Marcar tarefa como pendente
- Visualizar semanas anteriores

---

## 🛠️ Manual de Uso (Administradores e Gerenciadores)

- Criar tarefas recorrentes
- Ajustar ordem de rotação
- Alterar responsáveis
- Adicionar/remover tarefas avulsas
- Gerenciar usuários e cargos

---

- Administração de tarefas e usuários
- Manutenção e evolução do sistema
