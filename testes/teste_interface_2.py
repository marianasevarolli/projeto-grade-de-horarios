"""
Teste do Visualizador Dinâmico — INT_02
Sprint S8 | testes/teste_visualizador.py

Cobertura:
  mapear_cores_professores()       → tamanho, ciclagem, chaves corretas
  agregar_turmas_compartilhadas()  → formato 'SI1;CC1', grade vazia
  obter_turmas_nao_alocadas()      → detecção correta, grade vazia, todas alocadas
  construir_html_grade()           → estrutura HTML, filtros, grade vazia
  construir_html_legenda()         → chips por professor, dict vazio
  construir_html_alertas()         → cartões por turma, DataFrame vazio
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from app import (
    mapear_cores_professores,
    agregar_turmas_compartilhadas,
    obter_turmas_nao_alocadas,
    construir_html_grade,
    construir_html_legenda,
    construir_html_alertas,
    PALETA_CORES,
)
from projeto import criar_grade_vazia, alocar_aula


# ─── Utilitário ───────────────────────────────────────────────────────────────

def _grade_exemplo() -> pd.DataFrame:
    """Cria uma grade de 3 aulas para reutilização nos testes."""
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados', 'Ana Souza',  'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'CC1', 'Banco de Dados', 'Ana Souza',  'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'SI2', 'Algoritmos',    'Carlos Lima', 'Sala102', 'Terça',   '10:00')
    return grade


# =============================================================================
# mapear_cores_professores()
# =============================================================================

def testar_mapeamento_retorna_todos_professores():
    """Todos os professores únicos da grade devem receber uma cor."""
    print("Testando mapear_cores_professores: cobertura total...")
    grade = _grade_exemplo()
    cores = mapear_cores_professores(grade)
    profs_grade = set(grade['professor'].unique())
    assert set(cores.keys()) == profs_grade, (
        f"❌ Professores sem cor: {profs_grade - set(cores.keys())}"
    )
    print(f"✅ {len(cores)} professores mapeados corretamente.")


def testar_mapeamento_valor_e_par_de_strings():
    """Cada entrada deve ser uma tupla de duas strings (fundo, borda)."""
    print("Testando mapear_cores_professores: formato dos valores...")
    grade = _grade_exemplo()
    cores = mapear_cores_professores(grade)
    for prof, (fundo, borda) in cores.items():
        assert isinstance(fundo, str) and fundo.startswith('#'), \
            f"❌ Cor de fundo inválida para '{prof}': {fundo}"
        assert isinstance(borda, str) and borda.startswith('#'), \
            f"❌ Cor de borda inválida para '{prof}': {borda}"
    print("✅ Todos os pares de cores são strings hexadecimais válidas.")


def testar_mapeamento_ciclagem_paleta():
    """Com mais professores que cores na paleta, deve ciclar sem erro."""
    print("Testando mapear_cores_professores: ciclagem da paleta...")
    grade = criar_grade_vazia()
    for i in range(len(PALETA_CORES) + 3):
        grade = alocar_aula(
            grade, f'T{i}', 'Disc', f'Prof{i}', 'Sala', 'Segunda', '08:00'
        )
    cores = mapear_cores_professores(grade)
    assert len(cores) == len(PALETA_CORES) + 3
    print(f"✅ Ciclagem OK: {len(cores)} professores com {len(PALETA_CORES)} cores disponíveis.")


# =============================================================================
# agregar_turmas_compartilhadas()
# =============================================================================

def testar_agregacao_turmas_compartilhadas():
    """SI1 e CC1 no mesmo slot devem gerar uma linha com 'SI1;CC1'."""
    print("Testando agregar_turmas_compartilhadas: formato 'SI1;CC1'...")
    grade = _grade_exemplo()
    agg = agregar_turmas_compartilhadas(grade)

    linha_bd = agg[(agg['disciplina'] == 'Banco de Dados')]
    assert len(linha_bd) == 1, f"❌ Esperava 1 linha para BD, obteve {len(linha_bd)}."
    turma_agg = linha_bd.iloc[0]['turma']
    assert 'SI1' in turma_agg and 'CC1' in turma_agg and ';' in turma_agg
    print(f"✅ Turmas agregadas como '{turma_agg}'.")


def testar_agregacao_grade_vazia():
    """Grade vazia deve retornar DataFrame vazio sem erros."""
    print("Testando agregar_turmas_compartilhadas com grade vazia...")
    grade = criar_grade_vazia()
    agg = agregar_turmas_compartilhadas(grade)
    assert agg.empty
    print("✅ Retornou DataFrame vazio para grade vazia.")


# =============================================================================
# obter_turmas_nao_alocadas()
# =============================================================================

def testar_detecta_turma_nao_alocada():
    """Turma presente no CSV mas ausente na grade deve aparecer no resultado."""
    print("Testando obter_turmas_nao_alocadas: detecção de ausente...")
    turmas_df = pd.DataFrame([
        {'turma': 'SI1', 'disciplina': 'Banco de Dados', 'alunos': 30, 'tipo': 'Teorica'},
        {'turma': 'SI2', 'disciplina': 'Algoritmos',     'alunos': 20, 'tipo': 'Teorica'},
        {'turma': 'CC1', 'disciplina': 'Redes',          'alunos': 25, 'tipo': 'Teorica'},
    ])
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados', 'Ana',   'S101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'SI2', 'Algoritmos',     'Carlos','S102', 'Terça',   '10:00')

    nao_aloc = obter_turmas_nao_alocadas(turmas_df, grade)
    assert len(nao_aloc) == 1
    assert nao_aloc.iloc[0]['turma'] == 'CC1'
    print("✅ CC1 detectada corretamente como não alocada.")


def testar_todas_alocadas_retorna_vazio():
    """Quando todas as turmas estão na grade, deve retornar DataFrame vazio."""
    print("Testando obter_turmas_nao_alocadas: todas alocadas...")
    turmas_df = pd.DataFrame([
        {'turma': 'SI1', 'disciplina': 'BD', 'alunos': 30, 'tipo': 'Teorica'},
    ])
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'BD', 'Ana', 'S101', 'Segunda', '08:00')

    nao_aloc = obter_turmas_nao_alocadas(turmas_df, grade)
    assert nao_aloc.empty
    print("✅ Retornou vazio quando todas as turmas estão alocadas.")


def testar_grade_vazia_todas_nao_alocadas():
    """Com grade vazia, todas as turmas do CSV devem aparecer como não alocadas."""
    print("Testando obter_turmas_nao_alocadas: grade vazia...")
    turmas_df = pd.DataFrame([
        {'turma': 'SI1', 'disciplina': 'BD', 'alunos': 30, 'tipo': 'Teorica'},
        {'turma': 'SI2', 'disciplina': 'AL', 'alunos': 20, 'tipo': 'Teorica'},
    ])
    grade = criar_grade_vazia()
    nao_aloc = obter_turmas_nao_alocadas(turmas_df, grade)
    assert len(nao_aloc) == 2
    print("✅ Todas as turmas retornadas como não alocadas para grade vazia.")


# =============================================================================
# construir_html_grade()
# =============================================================================

def testar_html_grade_contem_estrutura_basica():
    """HTML gerado deve conter tags de tabela e conteúdo das aulas."""
    print("Testando construir_html_grade: estrutura básica do HTML...")
    grade = _grade_exemplo()
    cores = mapear_cores_professores(grade)
    html = construir_html_grade(grade, cores)

    assert '<table' in html,       "❌ HTML deve conter tag <table>."
    assert '<th>'   in html,       "❌ HTML deve conter cabeçalhos <th>."
    assert 'Ana Souza' in html,    "❌ Nome do professor deve aparecer no HTML."
    assert 'Banco de Dados' in html, "❌ Disciplina deve aparecer no HTML."
    assert 'Sala101' in html,      "❌ Sala deve aparecer no HTML."
    print("✅ HTML contém estrutura de tabela e dados das aulas.")


def testar_html_grade_filtro_professor():
    """Com filtro por professor, apenas as aulas desse professor aparecem."""
    print("Testando construir_html_grade: filtro por professor...")
    grade = _grade_exemplo()
    cores = mapear_cores_professores(grade)
    html = construir_html_grade(grade, cores, 'professor', 'Ana Souza')

    assert 'Ana Souza'  in html, "❌ Ana Souza deve aparecer no HTML filtrado."
    assert 'Carlos Lima' not in html, "❌ Carlos Lima não deve aparecer no filtro de Ana Souza."
    print("✅ Filtro por professor funcionou corretamente.")


def testar_html_grade_vazia_retorna_mensagem():
    """Grade vazia deve retornar HTML com mensagem informativa, não tabela vazia."""
    print("Testando construir_html_grade: grade vazia...")
    grade = criar_grade_vazia()
    html = construir_html_grade(grade, {})

    assert '<table' not in html, "❌ Grade vazia não deve gerar tabela."
    assert len(html) > 0,        "❌ Deve retornar pelo menos uma mensagem."
    print("✅ Grade vazia retornou mensagem informativa sem tabela.")


# =============================================================================
# construir_html_legenda()
# =============================================================================

def testar_legenda_contem_todos_professores():
    """Legenda deve conter um chip para cada professor mapeado."""
    print("Testando construir_html_legenda: chips por professor...")
    grade = _grade_exemplo()
    cores = mapear_cores_professores(grade)
    html = construir_html_legenda(cores)

    for prof in cores:
        assert prof in html, f"❌ Professor '{prof}' ausente na legenda."
    print(f"✅ Legenda contém chips para {len(cores)} professor(es).")


def testar_legenda_dict_vazio():
    """Dicionário vazio deve retornar string vazia sem erro."""
    print("Testando construir_html_legenda: dict vazio...")
    html = construir_html_legenda({})
    assert html == ''
    print("✅ Legenda vazia retornada corretamente.")


# =============================================================================
# construir_html_alertas()
# =============================================================================

def testar_alertas_contem_turmas_nao_alocadas():
    """HTML de alertas deve mencionar cada turma não alocada."""
    print("Testando construir_html_alertas: cards por turma...")
    nao_aloc = pd.DataFrame([
        {'turma': 'CC1', 'disciplina': 'Redes',       'alunos': 30, 'tipo': 'Laboratorio'},
        {'turma': 'SI3', 'disciplina': 'Segurança',   'alunos': 25, 'tipo': 'Teorica'},
    ])
    html = construir_html_alertas(nao_aloc)

    assert 'CC1'       in html, "❌ Turma CC1 deve aparecer nos alertas."
    assert 'SI3'       in html, "❌ Turma SI3 deve aparecer nos alertas."
    assert 'Redes'     in html, "❌ Disciplina Redes deve aparecer nos alertas."
    assert 'laboratório' in html.lower() or 'laboratorio' in html.lower() or \
           'Laboratorio' in html, "❌ Dica sobre laboratório deve aparecer."
    print("✅ Alertas contêm cards para CC1 e SI3 com informações corretas.")


def testar_alertas_dataframe_vazio():
    """DataFrame vazio deve retornar string vazia sem erro."""
    print("Testando construir_html_alertas: DataFrame vazio...")
    html = construir_html_alertas(pd.DataFrame())
    assert html == ''
    print("✅ Retornou string vazia para DataFrame vazio.")


# =============================================================================
# Execução
# =============================================================================

if __name__ == '__main__':
    try:
        # mapear_cores_professores
        testar_mapeamento_retorna_todos_professores()
        testar_mapeamento_valor_e_par_de_strings()
        testar_mapeamento_ciclagem_paleta()

        # agregar_turmas_compartilhadas
        testar_agregacao_turmas_compartilhadas()
        testar_agregacao_grade_vazia()

        # obter_turmas_nao_alocadas
        testar_detecta_turma_nao_alocada()
        testar_todas_alocadas_retorna_vazio()
        testar_grade_vazia_todas_nao_alocadas()

        # construir_html_grade
        testar_html_grade_contem_estrutura_basica()
        testar_html_grade_filtro_professor()
        testar_html_grade_vazia_retorna_mensagem()

        # construir_html_legenda
        testar_legenda_contem_todos_professores()
        testar_legenda_dict_vazio()

        # construir_html_alertas
        testar_alertas_contem_turmas_nao_alocadas()
        testar_alertas_dataframe_vazio()

        print("\n🚀 Sucesso: Todos os testes de INT_02 passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de INT_02 não passaram.")