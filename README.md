# Eletriom Finance - Sistema de Gerenciamento Financeiro

![Eletriom Finance](https://img.shields.io/badge/Eletriom-Finance-blue)
![Versão](https://img.shields.io/badge/Versão-1.0-green)
![Licença](https://img.shields.io/badge/Licença-MIT-yellow)

## 📋 Sobre o Projeto

Eletriom Finance é um sistema completo de gerenciamento financeiro pessoal desenvolvido com Flask. Ele permite o controle detalhado de transações financeiras, cartões de crédito, faturas pendentes e oferece uma visão clara do saldo diário, ajudando você a manter suas finanças organizadas e sob controle.

## ✨ Principais Funcionalidades

### 📊 Dashboard Financeiro
- Visualização do saldo atual
- Resumo de entradas e saídas do mês
- Gráficos de distribuição de gastos por categoria
- Análise de tendências financeiras

### 💰 Gerenciamento de Transações
- Registro de entradas e saídas
- Categorização de transações
- Transações recorrentes
- Importação de extratos em CSV

### 💳 Cartões de Crédito
- Cadastro e gerenciamento de múltiplos cartões
- Controle de limite disponível
- Acompanhamento de datas de fechamento e vencimento
- Visualização de faturas por período

### 📅 Saldo Diário
- Acompanhamento da evolução do saldo
- Histórico detalhado de transações por dia
- Filtros por mês e ano
- Exportação de relatórios

### 📑 Faturas Pendentes
- Visualização de faturas a vencer
- Alertas de vencimento
- Histórico de pagamentos

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.6 ou superior
- Pip (gerenciador de pacotes Python)

### Passos para Instalação

1. Clone o repositório ou baixe os arquivos do projeto

2. Instale as dependências necessárias:
   ```
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente (opcional):
   - Crie um arquivo `.env` na raiz do projeto
   - Defina as variáveis necessárias (MAIL_USERNAME, MAIL_PASSWORD, etc.)

4. Inicialize o banco de dados (na primeira execução):
   ```
   python app.py init-db
   ```

5. Execute a aplicação:
   ```
   python app.py
   ```

6. Acesse a aplicação no navegador:
   ```
   http://localhost:5000
   ```

## 📱 Como Usar

### Primeiros Passos
1. Registre-se no sistema com seu e-mail e senha
2. Faça login para acessar o dashboard principal
3. Comece adicionando suas transações e cartões de crédito

### Adicionando Transações
1. Clique no botão "Nova Transação" no dashboard
2. Preencha os dados da transação (data, valor, descrição, tipo)
3. Selecione uma categoria para melhor organização
4. Salve a transação

### Importando Extratos
1. Acesse a opção "Importar Extrato"
2. Faça o upload do arquivo CSV seguindo o modelo disponível
3. Revise as transações importadas
4. Confirme a importação

### Gerenciando Cartões de Crédito
1. Acesse a seção "Cartões de Crédito"
2. Clique em "Novo Cartão" para adicionar um cartão
3. Preencha os dados do cartão (nome, limite, dia de vencimento, dia de fechamento)
4. Acompanhe o limite disponível e as faturas

## 🔧 Tecnologias Utilizadas

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Banco de Dados**: SQLite
- **Gráficos**: Chart.js

## 🤝 Contribuição

Contribuições são bem-vindas! Se você deseja melhorar o Eletriom Finance, siga estes passos:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das suas alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## 📞 Contato

Para sugestões, dúvidas ou suporte, entre em contato através do e-mail: contato@eletriomfinance.com

---

Desenvolvido com ❤️ pela equipe Eletriom