"""
Teste 03 — Trava de Conflito de Agenda do Professor (ALOC_01)
Referência de Teste: Teste 02 do documento de especificação
                     (Conflito de professor — RN_3)

Cobertura:
  - criar_grade_vazia()         → estrutura inicial correta
  - professor_ja_alocado()      → trava detecta conflito
  - alocar_aula()               → inserção correta na grade
  - gerar_grade()               → motor não aloca professor em dois lugares
"""

import sys
import os

# Adiciona a raiz do projeto ao path para importar projeto.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from projeto import (
    criar_grade_vazia,
    professor_ja_alocado,
    alocar_aula,
    gerar_grade,
    carregar_dados,
)


# ─── Teste 1 ──────────────────────────────────────────────────────────────────
def testar_grade_vazia():
    """Verifica se a grade é criada com as colunas corretas e sem linhas."""
    print("Testando criação da grade vazia...")

    grade = criar_grade_vazia()

    colunas_esperadas = ['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']
    assert list(grade.columns) == colunas_esperadas, \
        "❌ Colunas da grade não correspondem ao esperado."
    assert grade.empty, \
        "❌ Grade recém-criada deveria estar vazia."

    print("✅ Grade vazia criada corretamente com as colunas certas.")


# ─── Teste 2 ──────────────────────────────────────────────────────────────────
def testar_trava_professor_livre():
    """Verifica que a trava libera professor quando a grade está vazia."""
    print("Testando trava com professor livre (grade vazia)...")

    grade = criar_grade_vazia()

    resultado = professor_ja_alocado(grade, 'Ana Souza', 'Segunda', '19:00')
    assert resultado == False, \
        "❌ Professor deveria estar LIVRE em grade vazia."

    print("✅ Trava liberou corretamente: professor livre na grade vazia.")


# ─── Teste 3 ──────────────────────────────────────────────────────────────────
def testar_trava_professor_ocupado():
    """
    Verifica que a trava BLOQUEIA um professor já alocado no mesmo slot.
    Cenário: Ana Souza já está em 'Segunda 19:00' → trava deve detectar conflito.
    """
    print("Testando trava com professor OCUPADO no mesmo dia e horário...")

    grade = criar_grade_vazia()

    # Registra a primeira aula da Ana Souza
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    # Tenta alocar a mesma professora no mesmo slot → deve ser bloqueado
    resultado = professor_ja_alocado(grade, 'Ana Souza', 'Segunda', '19:00')
    assert resultado == True, \
        "❌ Trava deveria BLOQUEAR Ana Souza: ela já está alocada neste horário."

    print("✅ Trava funcionou: conflito detectado e professor bloqueado.")


# ─── Teste 4 ──────────────────────────────────────────────────────────────────
def testar_trava_horarios_diferentes():
    """
    Verifica que a trava NÃO bloqueia o professor quando o horário é diferente.
    Cenário: Ana Souza está em 'Segunda 19:00', mas é solicitada para 'Quarta 19:00'.
    """
    print("Testando trava com horários diferentes (não deve bloquear)...")

    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    # Horário diferente → professor deve estar LIVRE
    resultado = professor_ja_alocado(grade, 'Ana Souza', 'Quarta', '19:00')
    assert resultado == False, \
        "❌ Trava não deveria bloquear: horário é diferente."

    print("✅ Trava correta: professor livre em horário diferente.")


# ─── Teste 5 ──────────────────────────────────────────────────────────────────
def testar_motor_sem_conflito_de_professor():
    """
    Teste de integração: garante que o motor gerar_grade() nunca coloca
    o mesmo professor em dois lugares no mesmo dia e horário.
    Usa os CSVs reais da pasta csv/.
    """
    print("Testando motor gerar_grade() — sem conflito de professor...")

    data = carregar_dados()
    if not data:
        print("⚠️  Arquivos CSV não encontrados. Pulando teste de integração.")
        return

    grade = gerar_grade(data)

    if grade.empty:
        print("⚠️  Grade gerada está vazia. Verifique os dados dos CSVs.")
        return

    # Agrupa por professor + dia + horário e verifica duplicatas
    duplicatas = grade.groupby(['professor', 'dia', 'horario']).size()
    conflitos  = duplicatas[duplicatas > 1]

    assert conflitos.empty, (
        f"❌ Conflito de professor detectado na grade gerada:\n{conflitos}"
    )

    print(f"✅ Motor validado: {len(grade)} aula(s) alocada(s) sem conflito de professor.")
    print(grade.to_string(index=False))


# ─── Execução ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        testar_grade_vazia()
        testar_trava_professor_livre()
        testar_trava_professor_ocupado()
        testar_trava_horarios_diferentes()
        testar_motor_sem_conflito_de_professor()

        print("\n🚀 Sucesso: Todos os testes de ALOC_01 passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de ALOC_01 não passaram.")