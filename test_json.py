import json

# Simular uma lista de transações semelhante à do app
txn_list = [
    {
        'id': 1,
        'date': '01-Jan-2023',
        'value': 100.0,
        'description': 'Teste',
        'trans_type': 'entrada',
        'category': 'Salário',
        'balance': 100.0
    }
]

# Tentativa 1: JSON normal
json_str = json.dumps(txn_list)
print("JSON normal:")
print(json_str)
print("\n")

# Tentativa 2: Verificar se o HTML está afetando a formatação
html_json = """
  {}
""".format(json_str)
print("HTML com formatação:")
print(html_json)
print("\n")

# Tentativa 3: Remover espaços em branco
html_json_stripped = html_json.strip()
print("HTML com formatação (espaços removidos):")
print(html_json_stripped)
print("\n")

# Tentativa 4: Verificar se é possível analisar o JSON formatado
try:
    parsed_json = json.loads(html_json_stripped)
    print("Análise bem-sucedida!")
except json.JSONDecodeError as e:
    print(f"Erro ao analisar JSON: {e}") 