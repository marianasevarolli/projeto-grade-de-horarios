# 2. Teste 01: Alocação Básica
def teste_01_alocacao_basica(data):
    print("--- Executando Teste 01: Alocação Básica ---")
    
    # Pegamos a primeira turma e buscamos uma sala compatível
    turma = data['turmas'].iloc[0]
    disciplina_tipo = turma['tipo']
    qtd_alunos = turma['alunos']
    
    # Lógica de Filtro (Regras de Negócio: Tipo e Capacidade)
    sala_compativel = data['salas'][
        (data['salas']['tipo'] == disciplina_tipo) & 
        (data['salas']['capacidade'] >= qtd_alunos)
    ]
    
    if not sala_compativel.empty:
        print(f"Sucesso: Turma {turma['turma']} alocada na {sala_compativel.iloc[0]['sala']}")
        return True
    else:
        print("Falha: Nenhuma sala atende aos requisitos de tipo/capacidade.")
        return False

if __name__ == "__main__":
    # Simulação de Ingestão
    db = carregar_dados()
    if db:
        teste_01_alocacao_basica(db)