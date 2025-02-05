import os
import json
import csv

def json_to_csv(json_file, csv_file):
    # Abre o arquivo JSON e carrega os dados
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Verifica se os dados são uma lista
    if isinstance(data, list):
        # Abre o arquivo CSV para escrita
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        print(f"O arquivo {json_file} não contém uma lista de objetos JSON.")

def convert_folder_json_to_csv(folder_path):
    # Lista todos os arquivos na pasta
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            # Cria o caminho completo para o arquivo JSON
            json_file_path = os.path.join(folder_path, filename)
            # Cria o nome do arquivo CSV
            csv_file_path = os.path.join(folder_path, filename.replace('.json', '.csv'))
            # Converte o JSON para CSV
            json_to_csv(json_file_path, csv_file_path)
            print(f"Convertido: {json_file_path} -> {csv_file_path}")

# Caminho da pasta contendo os arquivos JSON
folder_path = 'data'

# Converte todos os arquivos JSON na pasta para CSV
convert_folder_json_to_csv(folder_path)