import pandas as pd
import os

# 1. Configuração de Ambiente e Leitura (Sprint 1)
def carregar_dados():
    # Caminhos dos arquivos de entrada
    files = {
        'professores': 'professores.csv',
        'turmas': 'turmas.csv',
        'salas': 'salas.csv'
    }
    
    data = {}
    for key, path in files.items():
        if os.path.exists(path):
            data[key] = pd.read_csv(path)
            # Limpeza e Conversão de Tipos
            if key == 'salas':
                data[key]['capacidade'] = pd.to_numeric(data[key]['capacidade'], errors='coerce')
            if key == 'turmas':
                data[key]['alunos'] = pd.to_numeric(data[key]['alunos'], errors='coerce')
        else:
            print(f"Erro: Arquivo {path} não encontrado.")
    return data