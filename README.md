# 🐄 Sistema de Gestão de Fazenda (Python + Oracle)

## 📌 Descrição do Projeto

Este projeto consiste em um sistema completo de gestão de fazenda desenvolvido em Python, com persistência de dados em banco Oracle.
O sistema funciona via terminal (CLI) e permite o controle detalhado de animais, vacinas, agendamentos e relatórios.

O objetivo principal é aplicar conceitos de programação, manipulação de banco de dados e organização de software, garantindo regras de negócio consistentes e segurança no uso de dados sensíveis.

---

## 🎯 Objetivos

* Desenvolver um sistema funcional de CRUD completo
* Aplicar integração com banco Oracle
* Implementar regras de negócio reais
* Trabalhar com exportação de dados (TXT e JSON)
* Garantir boas práticas de segurança (sem expor credenciais)

---

## 🧠 Funcionalidades do Sistema

### 🐄 Módulo de Animais

* Cadastro de animais (nascimento ou compra)
* Registro de mãe (relacionamento entre animais)
* Listagem de animais vivos
* Edição de dados
* Registro de falecimento
* Exclusão com validação de integridade

---

### 💉 Módulo de Vacinas

* Cadastro de vacinas
* Listagem completa
* Edição de registros
* Exclusão com verificação de uso

---

### 📅 Módulo de Agendamentos

* Agendamento de vacinação
* Listagem de todos os agendamentos
* Marcar vacina como aplicada
* Cancelamento de agendamento
* Reagendamento (alteração de data)
* Exclusão de registros

#### ✔ Regras aplicadas:

* Não permite agendar vacina para animal morto
* Não permite datas no passado
* Atualiza automaticamente agendamentos atrasados

---

### 📊 Módulo de Relatórios

O sistema oferece diversos relatórios para análise:

* Vacinas atrasadas por período
* Vacinas aplicadas por período
* Vacinas agendadas por período
* Animais cadastrados em determinado período
* Relatório de animais mortos (detalhado)
* Total de vacinas aplicadas por tipo
* Histórico de vacinação por animal
* Animais sem vacina aplicada ou agendada
* Resumo geral do sistema

---

### 📁 Exportação de Dados

* 📄 Geração de relatório completo em `.txt`
* 🧾 Exportação de dados em `.json`

Arquivos gerados automaticamente na pasta:

```
arquivos/
```

---

## 🛠 Tecnologias Utilizadas

* Python 3.x
* oracledb
* pandas
* configparser
* JSON
* Oracle Database

---

## ⚙️ Configuração do Projeto

### 🔹 1. Instalar dependências

```bash
pip install oracledb pandas
```

---

### 🔹 2. Configurar conexão com banco

⚠️ **IMPORTANTE (Muito importante mesmo):**
As credenciais do banco NÃO estão no repositório por segurança.

Crie um arquivo chamado:

```
config.ini
```

Na raiz do projeto, com o seguinte conteúdo:

```ini
[database]
user = SEU_USUARIO
password = SUA_SENHA
dsn = SEU_DSN
```

#### ✔ Exemplo:

```ini
[database]
user = system
password = 123456
dsn = localhost/XEPDB1
```

---

### 🔹 3. Criar pasta de saída

O sistema gera arquivos automaticamente, então execute:

```bash
mkdir arquivos
```

---

## ▶️ Execução do Sistema

```bash
python nome_do_arquivo.py
```

---

## 🧱 Estrutura Esperada do Projeto

```
📦 projeto
 ┣ 📂 arquivos
 ┣ 🛢 db
 ┣ 📄 config.ini
 ┣ 📄 main.py
 ┣ 📄 README.md
 ┗ 📄 .gitignore
```

---

## 🔒 Segurança e Boas Práticas

* ❌ Não subir `config.ini` no GitHub
* ❌ Não expor senha do banco
* ✔ Separação de configuração e código
* ✔ Uso de validações para evitar erros de dados
* ✔ Controle de integridade antes de exclusões

---

## ⚠️ Regras de Negócio Importantes

O sistema implementa validações essenciais:

* Datas devem estar no formato: `DD/MM/YYYY`
* Não é permitido:

  * Agendar vacina para datas passadas
  * Vacinar animais mortos
  * Excluir registros com dependências
* Agendamentos atrasados são atualizados automaticamente

---

## 📊 Banco de Dados (Resumo)

O sistema trabalha com as seguintes entidades principais:

* `animal`
* `vacina`
* `agendamento`

Relacionamentos:

* Animal pode ter mãe (auto-relacionamento)
* Agendamento liga animal + vacina

---

## 🧪 Possíveis Melhorias Futuras

* Interface gráfica (GUI)
* API com Flask ou FastAPI
* Autenticação de usuários
* Dashboard com gráficos
* Deploy em nuvem

---

## 👨‍💻 Autor

Projeto desenvolvido para fins acadêmicos (FIAP), aplicando conceitos de:

* Programação em Python
* Banco de Dados Oracle
* Estruturação de sistemas
* Boas práticas de desenvolvimento

---

## 📌 Observação Final

Este projeto segue boas práticas de segurança ao não expor dados sensíveis no repositório, sendo necessário configurar o ambiente localmente para execução.

---