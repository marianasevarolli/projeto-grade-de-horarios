import pandas as pd
import os

# 1. Configuração de Ambiente e Leitura (Sprint 1)
def carregar_dados():
    # Caminhos apontando para a pasta correta
    files = {
        'professores': 'csv/professores.csv',
        'turmas': 'csv/turmas.csv',
        'salas': 'csv/salas.csv'
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

def validar_capacidade(turma, sala):
    """
    Regra: A sala deve comportar a quantidade de alunos da turma[cite: 30].
    """
    return turma['alunos'] <= sala['capacidade']

def validar_tipo_sala(turma, sala):
    """
    Regra Atualizada: Correspondência exata.
    Disciplinas de laboratório SÓ em laboratórios.
    Disciplinas teóricas SÓ em salas teóricas.
    """
    # Retorna True se forem iguais, ou False se forem diferentes
    return turma['tipo'].lower() == sala['tipo'].lower()

def validar_habilitacao(professor, turma):
    """
    Regra: O professor só pode lecionar disciplinas que está habilitado[cite: 28].
    """
    return professor['disciplina'] == turma['disciplina']

def validar_disponibilidade(professor, dia, horario):
    """
    Regra: Professor só pode ser alocado em seus horários disponíveis[cite: 28].
    """
    # Assume-se que o CSV de professores tem colunas 'dia' e 'horario' de disponibilidade
    return (professor['dia'] == dia) and (professor['horario'] == horario)

# Função principal de validação que une todas as regras
def verificar_todas_regras(professor, turma, sala, dia, horario):
    """
    Executa o checklist completo de regras de negócio para uma alocação.
    """
    valido = (
        validar_habilitacao(professor, turma) and
        validar_capacidade(turma, sala) and
        validar_tipo_sala(turma, sala) and
        validar_disponibilidade(professor, dia, horario) # REGRA ADICIONADA
    )
    return valido