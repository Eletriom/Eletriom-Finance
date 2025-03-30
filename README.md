# Eletriom Finance - Sistema de Gerenciamento Financeiro

![Eletriom Finance](https://img.shields.io/badge/Eletriom-Finance-blue)
![Versão](https://img.shields.io/badge/Versão-1.2-green)
![Licença](https://img.shields.io/badge/Licença-MIT-yellow)

## 📋 Sobre o Projeto

Eletriom Finance é um sistema completo de gerenciamento financeiro pessoal desenvolvido com Flask. Ele permite o controle detalhado de transações financeiras, cartões de crédito, faturas pendentes e oferece uma visão clara do saldo diário, ajudando você a manter suas finanças organizadas e sob controle.

## 🆕 Novidades da Versão 1.2

- **Filtro de Anos no Gráfico**: Agora é possível visualizar gastos por categoria de qualquer ano com a nova opção "Mostrar transações de todos os anos"
- **Melhor Visualização de Meses**: Títulos dos gráficos mostram o mês por extenso e o ano claramente
- **Correção de Bug**: Corrigido problema que mostrava transações futuras no gráfico de distribuição de gastos por categoria
- **Logs Detalhados**: Adicionados logs para facilitar a depuração e análise de transações

## ✨ Principais Funcionalidades

### 📊 Dashboard Financeiro
- Visualização do saldo atual em tempo real
- Resumo de entradas e saídas do mês com gráficos interativos
- Gráficos de distribuição de gastos por categoria
- Análise de tendências financeiras com comparativos mensais
- Previsão de gastos baseada no histórico
- **NOVO**: Filtro por ano nas visualizações de gastos

### 💰 Gerenciamento de Transações
- Registro rápido de entradas e saídas
- Categorização inteligente de transações
- Sistema de transações recorrentes automatizado
- Importação de extratos em CSV com reconhecimento automático
- Tags personalizáveis para melhor organização

### 💳 Cartões de Crédito
- Cadastro e gerenciamento de múltiplos cartões
- Controle de limite disponível em tempo real
- Acompanhamento de datas de fechamento e vencimento
- Visualização de faturas por período com filtros avançados
- Alertas personalizáveis de limite

### 📅 Saldo Diário
- Acompanhamento da evolução do saldo com gráficos interativos
- Histórico detalhado de transações por dia
- Filtros avançados por período, categoria e tipo
- Exportação de relatórios em múltiplos formatos (PDF, CSV, Excel)
- Projeção de saldo futuro

### 📑 Faturas Pendentes
- Visualização clara de faturas a vencer
- Sistema de alertas personalizáveis
- Histórico completo de pagamentos
- Categorização automática de despesas recorrentes
- Priorização inteligente de pagamentos

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8 ou superior
- Pip (gerenciador de pacotes Python)
- Navegador web moderno

### Passos para Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/eletriom/finance.git
   cd finance
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   - Crie um arquivo `.env` na raiz do projeto
   - Copie o conteúdo de `.env.example` e ajuste conforme necessário

5. Inicialize o banco de dados:
   ```bash
   python app.py init-db
   ```

6. Execute a aplicação:
   ```bash
   python app.py
   ```

7. Acesse no navegador:
   ```
   http://localhost:5000
   ```

## 📱 Como Usar

### Primeiros Passos
1. Crie sua conta com e-mail e senha
2. Complete seu perfil financeiro
3. Configure suas preferências de notificação
4. Comece adicionando suas transações e cartões

### Gerenciando Finanças
- Use o dashboard para uma visão geral
- Cadastre suas transações diárias
- Configure transações recorrentes
- Acompanhe seus cartões de crédito
- Monitore faturas pendentes

### Visualizando Gráficos de Gastos
- Selecione o mês desejado no seletor de mês
- Por padrão, os gráficos mostram apenas as transações do ano atual
- Para ver transações de outros anos, marque a opção "Mostrar transações de todos os anos"
- O título do gráfico indica claramente qual período está sendo visualizado

### Dicas de Uso
- Mantenha suas transações em dia
- Use as tags para melhor organização
- Configure alertas importantes
- Exporte relatórios regularmente
- Revise suas metas financeiras mensalmente

## 🔧 Tecnologias Utilizadas

- **Backend**: Python 3.8+, Flask 2.0+, SQLAlchemy 1.4+
- **Frontend**: HTML5, CSS3, JavaScript ES6+, Bootstrap 5
- **Banco de Dados**: SQLite 3
- **Gráficos**: Chart.js 3.7+
- **Autenticação**: Flask-Login
- **Processamento de Dados**: Pandas

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Faça commit das alterações (`git commit -m 'Adiciona nova funcionalidade'`)
4. Faça push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

Para sugestões, dúvidas ou suporte:
- Email: contato@eletriom.com.br
- Twitter: [@Eletriom](https://twitter.com/iameletriom)
- LinkedIn: [Eletriom](https://www.linkedin.com/in/rodrigo-martins-4640821b0/)

---

Desenvolvido com ❤️ pela equipe Eletriom