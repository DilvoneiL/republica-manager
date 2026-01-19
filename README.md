# 📋 República Manager

**Sistema Full Stack para Gerenciamento de Tarefas e Escalas em Repúblicas**

Projeto desenvolvido por **Dilvonei Lacerda**

---

## 🚀 Visão Geral

O **República Manager** é uma aplicação web **Full Stack** criada para resolver um problema real de organização e divisão de tarefas em repúblicas, garantindo **justiça na rotação**, **transparência** e **preservação do histórico**.

O sistema permite gerenciar usuários, tarefas recorrentes e avulsas, além de gerar automaticamente escalas semanais com regras configuráveis.

🔹 Projeto com foco em **regras de negócio**, **organização de código** e **modelagem relacional**
🔹 Pensado para uso real, não apenas como demonstração acadêmica

---

## 🛠️ Tecnologias Utilizadas

* **Python / Flask** — Back-end
* **Flask-Login** — Autenticação e autorização
* **SQLite** — Banco de dados (desenvolvimento)
* **PostgreSQL** — Compatível para produção
* **Jinja2** — Templates
* **Bootstrap 5** — Interface responsiva

---

## ✨ Principais Funcionalidades

* Autenticação de usuários e controle de permissões
* Geração automática de escala semanal
* Tarefas recorrentes e tarefas avulsas
* Regras flexíveis de rotação de responsáveis
* Histórico imutável de escalas passadas
* Interface web simples e intuitiva
* Controle administrativo completo

---

## 🧠 Arquitetura do Sistema

A aplicação foi estruturada de forma modular, separando regras de negócio, persistência de dados e interface.

### Principais Módulos

* **models.py**
  Define as entidades do sistema (Usuários, Tarefas, Escalas)

* **escala.py**
  Contém a lógica de geração automática da escala, rotação de responsáveis e preservação do histórico

* **admin.py**
  Gerenciamento de usuários, permissões e configurações administrativas

* **templates/**
  Camada de apresentação utilizando Jinja2 e Bootstrap

---

## 🗄️ Modelagem do Banco de Dados

### User

* id
* username
* password_hash
* cargo (admin / gerenciador / usuario)
* ordem_original
* ordem_invertido

### Tarefa (Recorrente)

Define tarefas fixas que se repetem semanalmente.

### EscalaSemanal

Registra:

* tarefa
* responsável
* semana
* status

---

## 🔄 Geração da Escala Semanal

A escala é criada automaticamente quando:

* Um usuário acessa a rota `/escala` pela primeira vez na semana
* O administrador altera as tarefas base
* A semana atual ainda não possui registros

### Regras de Geração

1. Buscar tarefas recorrentes
2. Calcular responsáveis conforme a regra de rotação
3. Criar apenas registros inexistentes

### Preservação do Histórico

* Alterações afetam apenas semanas atuais e futuras
* Semanas passadas permanecem inalteradas

---

## 🔁 Sistema de Rotação

O sistema permite diferentes estratégias de rotação de responsáveis.

### 🔹 Modo `10_step2_inverte`

* Avança 2 pessoas por semana
* Inverte a ordem a cada 5 semanas
* Ideal para repúblicas com 10 moradores

### 🔹 Modo `flex_step1_sem_inversao`

* Avança 1 pessoa por semana
* Sem inversão
* Funciona para qualquer quantidade de usuários

<img width="1309" height="637" alt="Seleção de modo de rotação" src="https://github.com/user-attachments/assets/003360ff-9f5e-450e-a1f2-b6fe5d333152" />

---

## 🧹 Tarefas Recorrentes

Criação, edição e exclusão de tarefas semanais fixas.

### Criar Tarefa Recorrente

<img width="1318" height="642" alt="Criar tarefa recorrente" src="https://github.com/user-attachments/assets/0660c3bb-24c7-4ce1-b65e-f987dd486c7a" />

### Editar Tarefa Recorrente

* Altera descrição da tarefa
* Afeta apenas semanas atuais e futuras
* Histórico permanece intacto

### Excluir Tarefa Recorrente

* Remove a tarefa base
* Exclui apenas ocorrências futuras

---

## ➕ Tarefas Avulsas

* Criadas para semanas específicas
* Disponível apenas para administradores e gerenciadores
* Não interferem na rotação automática

<img width="1322" height="647" alt="Tarefas avulsas" src="https://github.com/user-attachments/assets/2d156e00-d915-44dd-9ad4-ffd3338dfb66" />

---

## 📜 Histórico da Escala

O histórico permite visualizar:

* Todas as semanas já geradas
* Responsáveis da época
* Tarefas específicas de cada semana

⚠️ O histórico **não é alterado após criado**, garantindo rastreabilidade.

<img width="1292" height="625" alt="Histórico da escala" src="https://github.com/user-attachments/assets/94175c55-14fd-4609-b258-a8103c11de1f" />

---

## 👥 Gerenciamento de Usuários

### Cargos Disponíveis

* **Administrador** — Controle total do sistema
* **Gerenciador** — Gerencia escalas, tarefas e usuários comuns
* **Usuário** — Apenas visualiza e marca tarefas

### Criação de Usuários

<img width="1312" height="638" alt="Gerenciamento de usuários" src="https://github.com/user-attachments/assets/6b8b4eda-9497-4ff6-85f1-87f7538f5702" />

---

## 👤 Manual de Uso (Usuários)

* Marcar tarefa como concluída
* Marcar tarefa como pendente
* Visualizar semanas anteriores

---

## 🛠️ Manual de Uso (Administradores e Gerenciadores)

* Criar e editar tarefas recorrentes
* Ajustar regras de rotação
* Alterar responsáveis
* Criar tarefas avulsas
* Gerenciar usuários e permissões
* Administrar e evoluir o sistema

---

## 📚 Aprendizados

Durante o desenvolvimento deste projeto, foram trabalhados:

* Modelagem de dados relacionais
* Autenticação e autorização de usuários
* Implementação de regras de negócio complexas
* Organização modular de aplicações Flask
* Preservação de histórico e integridade dos dados
* Desenvolvimento de aplicações web completas (Full Stack)

---

## 🔗 Deploy

Aplicação disponível em:
👉 **[https://republica-manager-one.vercel.app]([https://republica-manager-one.vercel.app](https://aldeia.pythonanywhere.com/)**

---

## 🧑‍💻 Autor

**Dilvonei Lacerda**
Desenvolvedor Full Stack Júnior

---
