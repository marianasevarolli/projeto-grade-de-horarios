"""
Teste 04 — Controle de Conflitos Avançado (ALOC_02)
Referências do documento de testes:
  Teste 03 → Conflito de sala   (RN_5)
  Teste 04 → Capacidade da sala (RN_6, já garantida no laço)

Cobertura desta suite:
  - sala_ja_ocupada()             → trava RN_5
  - turma_ja_alocada_no_horario() → trava RN_4
  - gerar_grade()                 → laço completo com todas as travas
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from projeto import (
    criar_grade_vazia,
    alocar_aula,
    sala_ja_ocupada,
    turma_ja_alocada_no_horario,
    gerar_grade,
    carregar_dados,
)


# ─── Teste 1 ──────────────────────────────────────────────────────────────────
def testar_sala_livre():
    """Sala deve estar livre em grade vazia."""
    print("Testando sala livre em grade vazia...")
    grade = criar_grade_vazia()

    resultado = sala_ja_ocupada(grade, 'Sala101', 'Segunda', '19:00')
    assert resultado == False, "❌ Sala deveria estar LIVRE em grade vazia."

    print("✅ Sala corretamente livre em grade vazia.")


# ─── Teste 2 ──────────────────────────────────────────────────────────────────
def testar_sala_ocupada():
    """
    Trava RN_5: sala já em uso deve bloquear nova alocação
    no mesmo dia e horário.
    """
    print("Testando trava de sala OCUPADA no mesmo slot...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    resultado = sala_ja_ocupada(grade, 'Sala101', 'Segunda', '19:00')
    assert resultado == True, "❌ Trava deveria BLOQUEAR Sala101: já está em uso neste slot."

    print("✅ Trava de sala funcionou: conflito detectado corretamente.")


# ─── Teste 3 ──────────────────────────────────────────────────────────────────
def testar_sala_livre_em_horario_diferente():
    """
    Trava RN_5: a mesma sala deve estar disponível em horário diferente.
    """
    print("Testando sala livre em horário diferente...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    resultado = sala_ja_ocupada(grade, 'Sala101', 'Quarta', '19:00')
    assert resultado == False, "❌ Sala deveria estar LIVRE em horário diferente."

    print("✅ Sala corretamente disponível em outro horário.")


# ─── Teste 4 ──────────────────────────────────────────────────────────────────
def testar_turma_livre():
    """Turma deve estar livre em grade vazia."""
    print("Testando turma livre em grade vazia...")
    grade = criar_grade_vazia()

    resultado = turma_ja_alocada_no_horario(grade, 'T1A', 'Segunda', '19:00')
    assert resultado == False, "❌ Turma deveria estar LIVRE em grade vazia."

    print("✅ Turma corretamente livre em grade vazia.")


# ─── Teste 5 ──────────────────────────────────────────────────────────────────
def testar_turma_ja_alocada():
    """
    Trava RN_4: turma com aula registrada não pode receber
    uma segunda disciplina no mesmo slot.
    """
    print("Testando trava de turma JÁ ALOCADA no mesmo slot...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    resultado = turma_ja_alocada_no_horario(grade, 'T1A', 'Segunda', '19:00')
    assert resultado == True, "❌ Trava deveria BLOQUEAR T1A: já tem aula neste slot."

    print("✅ Trava de turma funcionou: conflito de agenda detectado.")


# ─── Teste 6 ──────────────────────────────────────────────────────────────────
def testar_turma_livre_em_horario_diferente():
    """
    Trava RN_4: a mesma turma deve poder ter aula em horário diferente.
    """
    print("Testando turma livre em horário diferente...")
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'T1A', 'Matemática', 'Ana Souza', 'Sala101', 'Segunda', '19:00')

    resultado = turma_ja_alocada_no_horario(grade, 'T1A', 'Quarta', '19:00')
    assert resultado == False, "❌ Turma deveria estar LIVRE em horário diferente."

    print("✅ Turma corretamente disponível em outro horário.")


# ─── Teste 7 ──────────────────────────────────────────────────────────────────
def testar_motor_sem_conflito_de_sala():
    """
    Teste de integração (Teste 03 do doc):
    O motor não pode colocar duas turmas na mesma sala no mesmo slot.
    """
    print("Testando motor — sem conflito de sala (RN_5)...")
    data = carregar_dados()
    if not data:
        print("⚠️  CSVs não encontrados. Pulando teste de integração.")
        return

    grade = gerar_grade(data)
    if grade.empty:
        print("⚠️  Grade vazia. Verifique os CSVs.")
        return

    duplicatas = grade.groupby(['sala', 'dia', 'horario']).size()
    conflitos  = duplicatas[duplicatas > 1]

    assert conflitos.empty, (
        f"❌ Conflito de sala detectado:\n{conflitos}"
    )
    print(f"✅ Motor validado: nenhuma sala usada duas vezes no mesmo slot.")


# ─── Teste 8 ──────────────────────────────────────────────────────────────────
def testar_motor_sem_conflito_de_turma():
    """
    Teste de integração:
    O motor não pode alocar a mesma turma em duas disciplinas no mesmo slot.
    """
    print("Testando motor — sem conflito de turma (RN_4)...")
    data = carregar_dados()
    if not data:
        print("⚠️  CSVs não encontrados. Pulando teste de integração.")
        return

    grade = gerar_grade(data)
    if grade.empty:
        print("⚠️  Grade vazia. Verifique os CSVs.")
        return

    duplicatas = grade.groupby(['turma', 'dia', 'horario']).size()
    conflitos  = duplicatas[duplicatas > 1]

    assert conflitos.empty, (
        f"❌ Conflito de turma detectado:\n{conflitos}"
    )
    print(f"✅ Motor validado: nenhuma turma com duas aulas no mesmo slot.")


# ─── Teste 9 ──────────────────────────────────────────────────────────────────
def testar_motor_completo_sem_nenhum_conflito():
    """
    Teste de integração completo (Teste 01 do doc — Alocação básica):
    Verifica todas as travas ao mesmo tempo na grade gerada.
    """
    print("Testando motor completo — todas as travas simultaneamente...")
    data = carregar_dados()
    if not data:
        print("⚠️  CSVs não encontrados. Pulando teste de integração.")
        return

    grade = gerar_grade(data)
    if grade.empty:
        print("⚠️  Grade vazia. Verifique os CSVs.")
        return

    for coluna, label in [
        (['professor', 'dia', 'horario'], 'professor'),
        (['sala',      'dia', 'horario'], 'sala'),
        (['turma',     'dia', 'horario'], 'turma'),
    ]:
        dup = grade.groupby(coluna).size()
        con = dup[dup > 1]
        assert con.empty, f"❌ Conflito de {label} detectado:\n{con}"

    total = len(grade)
    print(f"✅ Motor totalmente validado: {total} aula(s) sem nenhum conflito.")
    print(grade.to_string(index=False))


# ─── Execução ─────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        testar_sala_livre()
        testar_sala_ocupada()
        testar_sala_livre_em_horario_diferente()
        testar_turma_livre()
        testar_turma_ja_alocada()
        testar_turma_livre_em_horario_diferente()
        testar_motor_sem_conflito_de_sala()
        testar_motor_sem_conflito_de_turma()
        testar_motor_completo_sem_nenhum_conflito()

        print("\n🚀 Sucesso: Todos os testes de ALOC_02 passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de ALOC_02 não passaram.")