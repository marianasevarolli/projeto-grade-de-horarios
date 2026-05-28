"""
Teste 05 — Turmas Compartilhadas, Capacidade Somada e Desempate (ALOC_03)
Referências do documento:
  Teste 06 → Aula compartilhada       (RF_11, RN_9, RN_10)
  Teste 07 → Critério de desempate    (RN_12)
  Teste 08 → Múltiplas disciplinas    (RF_9)
  Teste 09 → Múltiplas turmas (prof)  (RF_10)

Cobertura:
  contar_aulas_professor()        → RN_12
  agrupar_turmas_por_disciplina() → RN_9, RN_13
  calcular_total_alunos()         → RN_10
  validar_capacidade_grupo()      → RN_10
  gerar_grade() com grupos        → RF_11, RN_9, RN_10, RN_12, RN_13
  exportar_grade() com turmas     → RF_8, RF_11
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from projeto import (
    criar_grade_vazia,
    alocar_aula,
    contar_aulas_professor,
    agrupar_turmas_por_disciplina,
    calcular_total_alunos,
    validar_capacidade_grupo,
    gerar_grade,
    exportar_grade,
)


# ─── Teste 1 ──────────────────────────────────────────────────────────────────
def testar_contar_aulas_professor_zero():
    """Professor sem nenhuma aula deve retornar 0."""
    print("Testando contagem de aulas: professor sem aulas...")
    grade = criar_grade_vazia()
    assert contar_aulas_professor(grade, 'Ana Souza') == 0
    print("✅ Retornou 0 para professor sem aulas.")


# ─── Teste 2 ──────────────────────────────────────────────────────────────────
def testar_contar_aulas_professor_com_aulas():
    """Professor com 2 aulas alocadas deve retornar 2."""
    print("Testando contagem de aulas: professor com 2 aulas...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza',   'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'T2A', 'Matemática', 'Ana Souza',   'Sala101', 'Quarta',  '10:00')
    grade = alocar_aula(grade, 'T1B', 'Física',     'Carlos Lima', 'Sala102', 'Terça',   '10:00')

    assert contar_aulas_professor(grade, 'Ana Souza')   == 2
    assert contar_aulas_professor(grade, 'Carlos Lima') == 1
    print("✅ Contagem de aulas por professor correta.")


# ─── Teste 3 ──────────────────────────────────────────────────────────────────
def testar_agrupamento_por_disciplina():
    """
    RN_9:  turmas com mesma disciplina E mesmo tipo formam um grupo.
    RN_13: 'Banco de Dados - Teorica' e 'Banco de Dados - Lab' são grupos DISTINTOS.
    """
    print("Testando agrupamento por disciplina+tipo (RN_9, RN_13)...")
    turmas = pd.DataFrame([
        {'turma': 'SI1', 'disciplina': 'Banco de Dados', 'alunos': 30, 'tipo': 'Teorica'},
        {'turma': 'CC1', 'disciplina': 'Banco de Dados', 'alunos': 25, 'tipo': 'Teorica'},
        {'turma': 'SI1', 'disciplina': 'Banco de Dados', 'alunos': 20, 'tipo': 'Laboratorio'},
        {'turma': 'T1C', 'disciplina': 'Algoritmos',     'alunos': 15, 'tipo': 'Teorica'},
    ])

    grupos = agrupar_turmas_por_disciplina(turmas)
    assert len(grupos) == 3, f"❌ Esperava 3 grupos, obteve {len(grupos)}."

    # RN_13: teórica e lab da mesma disciplina são grupos separados
    for grupo in grupos:
        assert grupo['tipo'].nunique() == 1, "❌ RN_13: teórica e laboratório no mesmo grupo."

    # Grupo Banco de Dados Teorica deve ter 2 turmas
    grupo_bd_teorica = [g for g in grupos if
                        'Banco de Dados' in g['disciplina'].values and
                        'Teorica' in g['tipo'].values]
    assert len(grupo_bd_teorica[0]) == 2, "❌ Grupo BD-Teorica deveria ter 2 turmas."

    print("✅ Agrupamento correto: 3 grupos distintos, RN_13 respeitado.")


# ─── Teste 4 ──────────────────────────────────────────────────────────────────
def testar_calcular_total_alunos():
    """RN_10: soma de alunos deve ser calculada corretamente para o grupo."""
    print("Testando cálculo de total de alunos do grupo (RN_10)...")
    grupo = pd.DataFrame([
        {'turma': 'SI1', 'alunos': 30, 'disciplina': 'BD', 'tipo': 'Teorica'},
        {'turma': 'CC1', 'alunos': 25, 'disciplina': 'BD', 'tipo': 'Teorica'},
    ])
    assert calcular_total_alunos(grupo) == 55
    print("✅ Total de alunos calculado corretamente: 55.")


# ─── Teste 5 ──────────────────────────────────────────────────────────────────
def testar_validar_capacidade_grupo_aprovado():
    """Sala de 60 deve comportar grupo com 55 alunos combinados."""
    print("Testando capacidade de grupo aprovada (RN_10)...")
    grupo = pd.DataFrame([
        {'turma': 'SI1', 'alunos': 30, 'disciplina': 'BD', 'tipo': 'Teorica'},
        {'turma': 'CC1', 'alunos': 25, 'disciplina': 'BD', 'tipo': 'Teorica'},
    ])
    sala = pd.Series({'sala': 'Sala101', 'capacidade': 60, 'tipo': 'Teorica'})
    assert validar_capacidade_grupo(grupo, sala) == True
    print("✅ Capacidade aprovada: sala comporta a soma de alunos.")


# ─── Teste 6 ──────────────────────────────────────────────────────────────────
def testar_validar_capacidade_grupo_reprovado():
    """Sala de 40 NÃO deve comportar grupo com 55 alunos combinados."""
    print("Testando capacidade de grupo reprovada (RN_10)...")
    grupo = pd.DataFrame([
        {'turma': 'SI1', 'alunos': 30, 'disciplina': 'BD', 'tipo': 'Teorica'},
        {'turma': 'CC1', 'alunos': 25, 'disciplina': 'BD', 'tipo': 'Teorica'},
    ])
    sala = pd.Series({'sala': 'Sala102', 'capacidade': 40, 'tipo': 'Teorica'})
    assert validar_capacidade_grupo(grupo, sala) == False
    print("✅ Capacidade reprovada: sala insuficiente para o grupo.")


# ─── Teste 7 ──────────────────────────────────────────────────────────────────
def testar_desempate_professor_menor_carga():
    """
    RN_12: quando dois professores são válidos para a mesma disciplina,
    o com menor carga horária já alocada é priorizado.

    Cenário:
      - Carlos Lima leciona Física (Terça 10h) e Algoritmos (Quarta 14h).
      - Ana Souza leciona apenas Algoritmos (Quarta 14h).
      - O motor aloca Carlos para Física primeiro (1 aula).
      - Para Algoritmos: Carlos (1 aula) vs Ana (0 aulas) → Ana vence pelo RN_12.
    """
    print("Testando desempate por menor carga horária (RN_12)...")
    professores = pd.DataFrame([
        {'nome': 'Carlos Lima', 'disciplina': 'Física',     'dia': 'Terça',  'horario': '10:00'},
        {'nome': 'Carlos Lima', 'disciplina': 'Algoritmos', 'dia': 'Quarta', 'horario': '14:00'},
        {'nome': 'Ana Souza',   'disciplina': 'Algoritmos', 'dia': 'Quarta', 'horario': '14:00'},
    ])
    turmas = pd.DataFrame([
        {'turma': 'T1A', 'disciplina': 'Física',     'alunos': 20, 'tipo': 'Teorica'},
        {'turma': 'T2A', 'disciplina': 'Algoritmos', 'alunos': 20, 'tipo': 'Teorica'},
    ])
    salas = pd.DataFrame([
        {'sala': 'Sala101', 'capacidade': 40, 'tipo': 'Teorica'},
    ])

    grade = gerar_grade({'professores': professores, 'turmas': turmas, 'salas': salas})

    alg_row = grade[grade['turma'] == 'T2A']
    assert not alg_row.empty, "❌ T2A (Algoritmos) não foi alocada."

    professor_escolhido = alg_row.iloc[0]['professor']
    assert professor_escolhido == 'Ana Souza', (
        f"❌ RN_12: deveria escolher Ana Souza (0 aulas), escolheu '{professor_escolhido}'."
    )
    print(f"✅ Desempate correto: Ana Souza (0 aulas) preferida a Carlos Lima (1 aula).")


# ─── Teste 8 ──────────────────────────────────────────────────────────────────
def testar_alocacao_compartilhada_no_motor():
    """
    RF_11, RN_9, RN_10: motor aloca SI1 e CC1 na mesma aula quando
    têm a mesma disciplina+tipo e a sala comporta a soma de alunos.
    """
    print("Testando alocação compartilhada no motor (RF_11, RN_9, RN_10)...")
    professores = pd.DataFrame([
        {'nome': 'Ana Souza', 'disciplina': 'Banco de Dados', 'dia': 'Segunda', 'horario': '08:00'},
    ])
    turmas = pd.DataFrame([
        {'turma': 'SI1', 'disciplina': 'Banco de Dados', 'alunos': 30, 'tipo': 'Teorica'},
        {'turma': 'CC1', 'disciplina': 'Banco de Dados', 'alunos': 25, 'tipo': 'Teorica'},
    ])
    salas = pd.DataFrame([
        {'sala': 'Sala101', 'capacidade': 60, 'tipo': 'Teorica'},
    ])

    grade = gerar_grade({'professores': professores, 'turmas': turmas, 'salas': salas})

    # Grade interna: 2 linhas, uma por turma
    assert len(grade) == 2, f"❌ Esperava 2 linhas na grade, obteve {len(grade)}."

    # Ambas no mesmo professor, sala, dia e horário
    assert grade['professor'].nunique() == 1, "❌ Turmas compartilhadas devem ter o mesmo professor."
    assert grade['sala'].nunique()      == 1, "❌ Turmas compartilhadas devem estar na mesma sala."
    assert grade['horario'].nunique()   == 1, "❌ Turmas compartilhadas devem ter o mesmo horário."

    print("✅ Aula compartilhada alocada: SI1 e CC1 no mesmo slot.")


# ─── Teste 9 ──────────────────────────────────────────────────────────────────
def testar_rn13_grupos_independentes():
    """
    RN_13: componentes teórico e laboratorial da mesma disciplina
    devem ser alocados como grupos independentes (nunca no mesmo slot).
    """
    print("Testando RN_13: teórica e lab como alocações independentes...")
    professores = pd.DataFrame([
        {'nome': 'Ana Souza', 'disciplina': 'Banco de Dados', 'dia': 'Segunda', 'horario': '08:00'},
    ])
    turmas = pd.DataFrame([
        {'turma': 'SI1-T', 'disciplina': 'Banco de Dados', 'alunos': 20, 'tipo': 'Teorica'},
        {'turma': 'SI1-L', 'disciplina': 'Banco de Dados', 'alunos': 20, 'tipo': 'Laboratorio'},
    ])
    salas = pd.DataFrame([
        {'sala': 'Sala101', 'capacidade': 40, 'tipo': 'Teorica'},
        {'sala': 'Lab01',   'capacidade': 30, 'tipo': 'Laboratorio'},
    ])

    grupos = agrupar_turmas_por_disciplina(turmas)

    # Deve gerar 2 grupos separados, não 1
    assert len(grupos) == 2, f"❌ RN_13: esperava 2 grupos independentes, obteve {len(grupos)}."
    assert grupos[0]['tipo'].iloc[0] != grupos[1]['tipo'].iloc[0], \
        "❌ RN_13: os dois grupos devem ter tipos diferentes."

    print("✅ RN_13 respeitado: teórica e laboratório em grupos independentes.")


# ─── Teste 10 ─────────────────────────────────────────────────────────────────
def testar_exportacao_turmas_compartilhadas():
    """
    RF_11: exportar_grade deve gerar 'SI1;CC1' quando duas turmas
    compartilham o mesmo slot na grade.
    """
    print("Testando formato de saída de turmas compartilhadas (RF_11)...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados', 'Ana Souza', 'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'CC1', 'Banco de Dados', 'Ana Souza', 'Sala101', 'Segunda', '08:00')

    # tempfile.mkstemp garante um caminho temporário válido em qualquer SO
    # (Windows, Linux, macOS) sem depender da existência de '/tmp'.
    import tempfile
    fd, caminho_temp = tempfile.mkstemp(suffix='.csv', prefix='grade_teste_05_')
    os.close(fd)  # fecha o file descriptor; exportar_grade abrirá o arquivo

    exportar_grade(grade, caminho_temp)

    grade_csv = pd.read_csv(caminho_temp)
    os.remove(caminho_temp)  # limpeza: remove o arquivo temporário após o teste
    assert len(grade_csv) == 1, (
        f"❌ Turmas compartilhadas devem gerar 1 linha no CSV, obteve {len(grade_csv)}."
    )

    turma_exportada = grade_csv.iloc[0]['turma']
    assert 'SI1' in turma_exportada and 'CC1' in turma_exportada, (
        f"❌ CSV deve conter 'SI1' e 'CC1', obteve: '{turma_exportada}'."
    )
    assert ';' in turma_exportada, (
        f"❌ Turmas devem ser separadas por ';', obteve: '{turma_exportada}'."
    )

    print(f"✅ Exportação correta: turmas agrupadas como '{turma_exportada}'.")


# ─── Execução ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        testar_contar_aulas_professor_zero()
        testar_contar_aulas_professor_com_aulas()
        testar_agrupamento_por_disciplina()
        testar_calcular_total_alunos()
        testar_validar_capacidade_grupo_aprovado()
        testar_validar_capacidade_grupo_reprovado()
        testar_desempate_professor_menor_carga()
        testar_alocacao_compartilhada_no_motor()
        testar_rn13_grupos_independentes()
        testar_exportacao_turmas_compartilhadas()

        print("\n🚀 Sucesso: Todos os testes de ALOC_03 passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de ALOC_03 não passaram.")