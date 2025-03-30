// Função para obter dados de gastos por categoria
function getDadosGastosPorCategoria(transactions, mes) {
    // Depurar transações recebidas
    console.log("Todas as transações:", transactions);
    
    // Obter mapeamento de meses em diferentes formatos
    const monthMap = {
        'jan': 'jan', 'january': 'jan', 'enero': 'jan', '01': 'jan', '1': 'jan', 'janeiro': 'jan',
        'feb': 'fev', 'february': 'fev', 'febrero': 'fev', '02': 'fev', '2': 'fev', 'fevereiro': 'fev',
        'mar': 'mar', 'march': 'mar', 'marzo': 'mar', '03': 'mar', '3': 'mar', 'março': 'mar',
        'apr': 'abr', 'april': 'abr', 'abril': 'abr', '04': 'abr', '4': 'abr',
        'may': 'mai', 'mayo': 'mai', '05': 'mai', '5': 'mai', 'maio': 'mai',
        'jun': 'jun', 'june': 'jun', 'junio': 'jun', '06': 'jun', '6': 'jun', 'junho': 'jun',
        'jul': 'jul', 'july': 'jul', 'julio': 'jul', '07': 'jul', '7': 'jul', 'julho': 'jul',
        'aug': 'ago', 'august': 'ago', 'agosto': 'ago', '08': 'ago', '8': 'ago',
        'sep': 'set', 'september': 'set', 'septiembre': 'set', '09': 'set', '9': 'set', 'setembro': 'set',
        'oct': 'out', 'october': 'out', 'octubre': 'out', '10': 'out', 'outubro': 'out',
        'nov': 'nov', 'november': 'nov', 'noviembre': 'nov', '11': 'nov', 'novembro': 'nov',
        'dec': 'dez', 'december': 'dez', 'diciembre': 'dez', '12': 'dez', 'dezembro': 'dez'
    };
    
    // Mapa para controlar transações recorrentes já processadas
    const processedRecurringIds = new Set();
    
    // Filtrar transações por mês e tipo 'saida'
    const transacoesFiltradas = transactions.filter(txn => {
        if (!txn || !txn.date || !txn.trans_type) return false;
        
        // Verificar se é uma transação de saída
        if (txn.trans_type !== 'saida') return false;
        
        // Extrair e normalizar mês da data
        const dataParts = txn.date.split('-');
        if (dataParts.length < 3) return false;
        
        // Se for "todos os meses", incluir todas as saídas (mas evitando duplicatas de recorrências)
        if (mes === 'todos') {
            // Para transações recorrentes, evitar contar várias vezes
            if (txn.is_recurring && txn.parent_id) {
                if (processedRecurringIds.has(txn.parent_id)) {
                    return false; // Já processamos outra ocorrência desta série
                }
                processedRecurringIds.add(txn.parent_id);
            }
            return true;
        }
        
        // Detalhes da análise da data
        console.log(`Analisando transação: ${txn.description}, data: ${txn.date}`);
        
        // Normalizar o mês da transação para comparação
        const mesTxn = dataParts[1].toLowerCase();
        let mesComparar = monthMap[mesTxn] || mesTxn;
        
        // Verificar se o mês da transação é igual ao mês selecionado
        const isMatchingMonth = mesComparar === mes.toLowerCase();
        
        console.log(`Mês da transação: ${mesTxn}, Mês normalizado: ${mesComparar}, Mês selecionado: ${mes}, Match: ${isMatchingMonth}`);
        
        if (isMatchingMonth) {
            // Para transações recorrentes, verificar se já processamos outra do mesmo grupo
            if (txn.is_recurring && txn.parent_id) {
                if (processedRecurringIds.has(txn.parent_id)) {
                    console.log(`Transação recorrente já processada: ${txn.description}`);
                    return false; // Já processamos outra ocorrência desta série
                }
                processedRecurringIds.add(txn.parent_id);
            }
        }
        
        return isMatchingMonth;
    });
    
    // Depurar transações filtradas
    console.log(`Transações filtradas para o mês ${mes}:`, transacoesFiltradas);
    
    // Agrupar por categoria
    const gastosPorCategoria = {};
    
    transacoesFiltradas.forEach(txn => {
        const categoria = txn.category || 'Sem categoria';
        if (!gastosPorCategoria[categoria]) {
            gastosPorCategoria[categoria] = 0;
        }
        
        // Garantir que o valor seja um número antes de somar
        const valor = parseFloat(txn.value);
        if (!isNaN(valor)) {
            console.log(`Adicionando ${valor} à categoria ${categoria} para ${txn.description}`);
            gastosPorCategoria[categoria] += valor;
        }
    });
    
    // Depurar categorias e valores
    console.log(`Gastos por categoria para o mês ${mes}:`, gastosPorCategoria);
    
    // Converter para arrays para Chart.js
    const categorias = Object.keys(gastosPorCategoria);
    const valores = categorias.map(cat => gastosPorCategoria[cat]);
    
    return {
        categorias: categorias,
        valores: valores
    };
}

// Função para criar/atualizar o gráfico
function atualizarGrafico(transactions) {
    let mesSelecionado = document.getElementById('seletor-mes').value;
    
    // Se nenhum mês foi selecionado, usar o mês atual
    if (!mesSelecionado) {
        const hoje = new Date();
        const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
        mesSelecionado = meses[hoje.getMonth()];
    }
    
    console.log("Mês selecionado:", mesSelecionado);
    
    const dados = getDadosGastosPorCategoria(transactions, mesSelecionado);
    
    // Verificar se há dados
    if (dados.categorias.length === 0) {
        console.log(`Nenhum gasto encontrado para o mês ${mesSelecionado}`);
        if (window.graficoGastos) {
            window.graficoGastos.destroy();
        }
        
        // Criar gráfico vazio ou mostrar mensagem
        const ctx = document.getElementById('grafico-gastos').getContext('2d');
        const config = {
            type: 'pie',
            data: {
                labels: ['Sem dados'],
                datasets: [{
                    data: [1],
                    backgroundColor: ['#f0f0f0'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                legend: {
                    display: false
                },
                tooltips: {
                    enabled: false
                },
                title: {
                    display: true,
                    text: `Distribuição de Gastos por Categoria - Sem gastos no mês de ${mesSelecionado}`,
                    fontSize: 16
                }
            }
        };
        
        window.graficoGastos = new Chart(ctx, config);
        return;
    }
    
    // Cores para o gráfico
    const cores = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
        '#FF9F40', '#8AC249', '#EA526F', '#25CCF7', '#FD7272',
        '#58B19F', '#182C61', '#6D214F', '#82589F', '#3B3B98'
    ];
    
    // Configuração do gráfico
    const config = {
        type: 'pie',
        data: {
            labels: dados.categorias,
            datasets: [{
                data: dados.valores,
                backgroundColor: cores.slice(0, dados.categorias.length),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            legend: {
                position: 'right',
                labels: {
                    padding: 20,
                    boxWidth: 15
                }
            },
            tooltips: {
                callbacks: {
                    label: function(tooltipItem, data) {
                        const dataset = data.datasets[tooltipItem.datasetIndex];
                        const valor = dataset.data[tooltipItem.index];
                        const categoria = data.labels[tooltipItem.index];
                        const total = dataset.data.reduce((a, b) => a + b, 0);
                        const porcentagem = Math.round((valor / total) * 100);
                        return `${categoria}: R$ ${valor.toFixed(2)} (${porcentagem}%)`;
                    }
                }
            },
            title: {
                display: true,
                text: 'Distribuição de Gastos por Categoria',
                fontSize: 16
            }
        }
    };
    
    // Destruir gráfico anterior se existir
    if (window.graficoGastos) {
        window.graficoGastos.destroy();
    }
    
    // Criar novo gráfico
    const ctx = document.getElementById('grafico-gastos').getContext('2d');
    window.graficoGastos = new Chart(ctx, config);
}

// Função para obter o mês atual em formato abreviado (3 letras)
function getMesAtual() {
    const meses = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
    const dataAtual = new Date();
    return meses[dataAtual.getMonth()];
}

// Função para formatar valores monetários
function formatCurrency(value) {
    return 'R$ ' + value.toFixed(2).replace('.', ',');
}

// Função para carregar a projeção de saldo futuro
function loadFutureBalance() {
    fetch('/future_balance')
        .then(response => response.json())
        .then(data => {
            // Atualizar o saldo atual
            document.getElementById('current-balance').textContent = formatCurrency(data.current_balance);
            
            // Limpar a tabela de projeção
            const tableBody = document.getElementById('projection-table-body');
            tableBody.innerHTML = '';
            
            // Preencher a tabela com os dados de projeção
            data.projection.forEach(item => {
                const row = document.createElement('tr');
                
                // Adicionar classe de destaque se houver transações no mês
                if (item.transactions > 0) {
                    row.classList.add('table-info');
                }
                
                row.innerHTML = `
                    <td>${item.date}</td>
                    <td class="font-weight-bold ${item.balance < 0 ? 'text-danger' : 'text-success'}">${formatCurrency(item.balance)}</td>
                    <td>${item.transactions > 0 ? `<span class="badge badge-primary">${item.transactions} transação(ões)</span>` : '-'}</td>
                `;
                
                tableBody.appendChild(row);
            });
            
            // Exibir o modal
            $('#futureBalanceModal').modal('show');
        })
        .catch(error => {
            console.error('Erro ao carregar projeção de saldo:', error);
            alert('Erro ao carregar projeção de saldo. Por favor, tente novamente.');
        });
}

// Função para carregar os dados de uma transação para edição
function loadTransactionForEdit(transactionIndex) {
    // Obter os dados das transações
    const transactionsData = document.getElementById('transactions-data');
    if (!transactionsData) return;
    
    const transactions = JSON.parse(transactionsData.textContent);
    const transaction = transactions[transactionIndex];
    
    if (!transaction) return;
    
    // Preencher o formulário de edição
    document.getElementById('edit-transaction-id').value = transactionIndex;
    document.getElementById('edit-date').value = transaction.date;
    document.getElementById('edit-value').value = transaction.value;
    document.getElementById('edit-description').value = transaction.description;
    document.getElementById('edit-trans_type').value = transaction.trans_type;
    document.getElementById('edit-category').value = transaction.category || '';
    
    // Exibir o modal de edição
    $('#editTransactionModal').modal('show');
}

// Função para salvar as alterações de uma transação
function saveTransactionEdit() {
    const transactionIndex = document.getElementById('edit-transaction-id').value;
    const transactionsData = document.getElementById('transactions-data');
    if (!transactionsData) return;
    
    const transactions = JSON.parse(transactionsData.textContent);
    const transaction = transactions[transactionIndex];
    
    if (!transaction) return;
    
    // Obter os valores do formulário
    const formData = new FormData();
    formData.append('date', document.getElementById('edit-date').value);
    formData.append('value', document.getElementById('edit-value').value);
    formData.append('description', document.getElementById('edit-description').value);
    formData.append('trans_type', document.getElementById('edit-trans_type').value);
    formData.append('category', document.getElementById('edit-category').value);
    
    // Enviar a requisição para o servidor
    fetch(`/edit/${transaction.id}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Fechar o modal
            $('#editTransactionModal').modal('hide');
            
            // Recarregar a página para atualizar os dados
            window.location.reload();
        } else {
            alert(data.message || 'Erro ao salvar as alterações.');
        }
    })
    .catch(error => {
        console.error('Erro ao salvar as alterações:', error);
        alert('Erro ao salvar as alterações. Por favor, tente novamente.');
    });
}

// Função para confirmar a exclusão de uma transação
function confirmDeleteTransaction(transactionIndex) {
    const transactionsData = document.getElementById('transactions-data');
    if (!transactionsData) return;
    
    const transactions = JSON.parse(transactionsData.textContent);
    const transaction = transactions[transactionIndex];
    
    if (!transaction) return;
    
    // Definir o ID da transação a ser excluída
    document.getElementById('delete-transaction-id').value = transactionIndex;
    
    // Exibir o modal de confirmação
    $('#deleteConfirmModal').modal('show');
}

// Função para excluir uma transação
function deleteTransaction() {
    const transactionIndex = document.getElementById('delete-transaction-id').value;
    const transactionsData = document.getElementById('transactions-data');
    if (!transactionsData) return;
    
    const transactions = JSON.parse(transactionsData.textContent);
    const transaction = transactions[transactionIndex];
    
    if (!transaction) return;
    
    // Enviar a requisição para o servidor
    fetch(`/delete/${transaction.id}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Fechar o modal
            $('#deleteConfirmModal').modal('hide');
            
            // Recarregar a página para atualizar os dados
            window.location.reload();
        } else {
            alert(data.message || 'Erro ao excluir a transação.');
        }
    })
    .catch(error => {
        console.error('Erro ao excluir a transação:', error);
        alert('Erro ao excluir a transação. Por favor, tente novamente.');
    });
}

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se o elemento do gráfico existe
    if (document.getElementById('grafico-gastos')) {
        // Obter dados das transações do elemento data
        const transactionsData = document.getElementById('transactions-data');
        if (transactionsData) {
            try {
                // Depurar o conteúdo do JSON
                const content = transactionsData.textContent;
                if (!content || content.trim() === '') {
                    console.error('Conteúdo de transactions-data está vazio');
                    return;
                }
                
                // Tentar analisar o JSON
                const transactions = JSON.parse(content);
                
                // Definir o mês atual como padrão no seletor
                const mesAtual = getMesAtual();
                const seletorMes = document.getElementById('seletor-mes');
                seletorMes.value = mesAtual;
                
                // Inicializar o gráfico com o mês atual
                atualizarGrafico(transactions);
                
                // Adicionar evento de mudança ao seletor de mês
                seletorMes.addEventListener('change', function() {
                    atualizarGrafico(transactions);
                });
                
                // Adicionar eventos para os botões de edição
                document.querySelectorAll('.btn-edit').forEach(button => {
                    button.addEventListener('click', function() {
                        const transactionIndex = this.getAttribute('data-id');
                        loadTransactionForEdit(transactionIndex);
                    });
                });
                
                // Adicionar eventos para os botões de exclusão
                document.querySelectorAll('.btn-delete').forEach(button => {
                    button.addEventListener('click', function() {
                        const transactionIndex = this.getAttribute('data-id');
                        confirmDeleteTransaction(transactionIndex);
                    });
                });
                
                // Adicionar evento para o botão de salvar edição
                document.getElementById('btn-save-edit').addEventListener('click', saveTransactionEdit);
                
                // Adicionar evento para o botão de confirmar exclusão
                document.getElementById('btn-confirm-delete').addEventListener('click', deleteTransaction);
                
                // Adicionar evento para o botão de projeção de saldo futuro
                document.getElementById('btn-future-balance').addEventListener('click', loadFutureBalance);
            } catch (error) {
                console.error('Erro ao processar dados de transações:', error);
                console.log('Conteúdo que causou erro:', transactionsData.textContent);
            }
        }
    }
});