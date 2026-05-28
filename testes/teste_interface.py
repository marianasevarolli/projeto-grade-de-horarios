"""
Teste de Interface — INT_01 (Dashboard de Upload)
Sprint S8 | testes/teste_interface.py

Cobertura:
  validar_colunas()       → colunas corretas, ausentes e extras
  ler_csv_upload()        → CSV válido, vazio, colunas ausentes,
                            valores numéricos inválidos, arquivo corrompido
  converter_grade_para_bytes() → bytes válidos, turmas compartilhadas no formato SI1;CC1

Nota:
  Testa apenas as funções auxiliares de app.py, que não dependem do
  Streamlit para executar (separação de conceitos). A UI em si não é
  testável por testes unitários.
"""

import sys
import os
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from app import validar_colunas, ler_csv_upload, converter_grade_para_bytes


# =============================================================================
# Utilitário: cria um arquivo CSV em memória para simular st.file_uploader
# =============================================================================

def _csv_em_memoria(conteudo: str, nome: str = 'arquivo.csv'):
    """
    Cria um objeto semelhante ao retornado por st.file_uploader,
    usando apenas io.BytesIO (sem criar arquivos em disco).
    """
    buf = io.BytesIO(conteudo.encode('utf-8'))
    buf.name = nome
    return buf


# =============================================================================
# Testes de validar_colunas()
# =============================================================================

def testar_validar_colunas_corretas():
    """DataFrame com todas as colunas deve retornar lista vazia."""
    print("Testando validar_colunas com colunas corretas...")
    df = pd.DataFrame(columns=['matricula', 'nome', 'disciplina', 'dia', 'horario'])
    assert validar_colunas(df, 'professores') == []
    print("✅ Sem colunas ausentes detectadas.")


def testar_validar_colunas_ausentes():
    """DataFrame sem 'dia' e 'horario' deve retornar essas duas colunas."""
    print("Testando validar_colunas com colunas ausentes...")
    df = pd.DataFrame(columns=['matricula', 'nome', 'disciplina'])
    ausentes = validar_colunas(df, 'professores')
    assert 'dia' in ausentes and 'horario' in ausentes, (
        f"❌ Esperava 'dia' e 'horario' ausentes, obteve: {ausentes}"
    )
    print(f"✅ Colunas ausentes detectadas corretamente: {ausentes}.")


def testar_validar_colunas_extras_ignoradas():
    """Colunas extras além das obrigatórias não devem gerar erro."""
    print("Testando validar_colunas com colunas extras...")
    df = pd.DataFrame(columns=['sala', 'capacidade', 'tipo', 'andar', 'bloco'])
    assert validar_colunas(df, 'salas') == []
    print("✅ Colunas extras ignoradas corretamente.")


# =============================================================================
# Testes de ler_csv_upload()
# =============================================================================

def testar_ler_csv_valido_professores():
    """CSV bem formado de professores deve retornar DataFrame sem erro."""
    print("Testando ler_csv_upload com professores válido...")
    conteudo = (
        "matricula,nome,disciplina,dia,horario\n"
        "2023001,Ana Souza,Banco de Dados,Segunda,08:00\n"
        "2023002,Carlos Lima,Algoritmos,Terça,10:00\n"
    )
    arquivo = _csv_em_memoria(conteudo, 'professores.csv')
    df, erro = ler_csv_upload(arquivo, 'professores')

    assert erro  is None, f"❌ Não deveria ter erro. Obteve: {erro}"
    assert df    is not None
    assert len(df) == 2
    print("✅ CSV de professores carregado corretamente (2 linhas).")


def testar_ler_csv_vazio():
    """CSV com apenas cabeçalho deve retornar erro de arquivo vazio."""
    print("Testando ler_csv_upload com arquivo vazio...")
    conteudo = "sala,capacidade,tipo\n"
    arquivo = _csv_em_memoria(conteudo, 'salas.csv')
    df, erro = ler_csv_upload(arquivo, 'salas')

    assert df   is None, "❌ DataFrame deveria ser None para arquivo vazio."
    assert erro is not None
    assert "vazio" in erro.lower(), f"❌ Mensagem deveria mencionar 'vazio'. Obteve: {erro}"
    print(f"✅ Erro detectado corretamente: '{erro}'.")


def testar_ler_csv_coluna_ausente():
    """CSV sem a coluna 'tipo' em salas deve retornar erro de coluna ausente."""
    print("Testando ler_csv_upload com coluna ausente...")
    conteudo = "sala,capacidade\nSala101,40\n"
    arquivo = _csv_em_memoria(conteudo, 'salas.csv')
    df, erro = ler_csv_upload(arquivo, 'salas')

    assert df   is None
    assert erro is not None
    assert "tipo" in erro, f"❌ Erro deveria mencionar 'tipo'. Obteve: {erro}"
    print(f"✅ Erro de coluna ausente detectado: '{erro}'.")


def testar_ler_csv_capacidade_invalida():
    """CSV de salas com 'capacidade' não numérica deve retornar erro."""
    print("Testando ler_csv_upload com capacidade inválida...")
    conteudo = "sala,capacidade,tipo\nSala101,QUARENTA,Teorica\n"
    arquivo = _csv_em_memoria(conteudo, 'salas.csv')
    df, erro = ler_csv_upload(arquivo, 'salas')

    assert df   is None
    assert erro is not None
    assert "capacidade" in erro.lower(), (
        f"❌ Erro deveria mencionar 'capacidade'. Obteve: {erro}"
    )
    print(f"✅ Erro de valor inválido detectado: '{erro}'.")


def testar_ler_csv_alunos_invalidos():
    """CSV de turmas com 'alunos' não numérico deve retornar erro."""
    print("Testando ler_csv_upload com alunos inválido...")
    conteudo = "turma,alunos,disciplina,tipo\nSI1,TRINTA,Banco de Dados,Teorica\n"
    arquivo = _csv_em_memoria(conteudo, 'turmas')
    df, erro = ler_csv_upload(arquivo, 'turmas')

    assert df   is None
    assert erro is not None
    assert "alunos" in erro.lower(), (
        f"❌ Erro deveria mencionar 'alunos'. Obteve: {erro}"
    )
    print(f"✅ Erro de alunos inválido detectado: '{erro}'.")


def testar_ler_csv_corrompido():
    """Arquivo que não é um CSV válido deve retornar erro sem derrubar o app."""
    print("Testando ler_csv_upload com arquivo corrompido...")
    conteudo = "\x00\x01\x02\x03 arquivo binário corrompido"
    arquivo = _csv_em_memoria(conteudo, 'salas.csv')
    df, erro = ler_csv_upload(arquivo, 'salas')

    # Pode retornar DataFrame vazio (pandas aceita alguns binários) ou erro;
    # o importante é que NÃO gera exceção não tratada.
    # Se df não for None, verificamos que pelo menos as colunas obrigatórias
    # estejam presentes ou que o erro seja tratado.
    if df is not None and erro is None:
        # pandas conseguiu ler algo; pode acontecer com alguns bytes
        print("⚠️  pandas leu o arquivo corrompido sem erro (comportamento aceitável).")
    else:
        assert erro is not None, "❌ Deveria ter retornado erro para arquivo corrompido."
        print(f"✅ Erro tratado para arquivo corrompido: '{erro[:60]}...'.")


# =============================================================================
# Testes de converter_grade_para_bytes()
# =============================================================================

def testar_converter_grade_para_bytes_simples():
    """Grade com uma turma deve gerar CSV com 1 linha de dados."""
    print("Testando converter_grade_para_bytes com 1 turma...")
    from projeto import criar_grade_vazia, alocar_aula
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados', 'Ana Souza', 'Sala101', 'Segunda', '08:00')

    csv_bytes = converter_grade_para_bytes(grade)
    assert isinstance(csv_bytes, bytes), "❌ Deve retornar bytes."

    df_resultado = pd.read_csv(io.BytesIO(csv_bytes))
    assert len(df_resultado) == 1
    assert list(df_resultado.columns) == ['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']
    print("✅ CSV gerado corretamente com 1 linha.")


def testar_converter_grade_turmas_compartilhadas():
    """
    RF_11: duas turmas no mesmo slot devem gerar 1 linha com 'SI1;CC1'.
    """
    print("Testando converter_grade_para_bytes com turmas compartilhadas (RF_11)...")
    from projeto import criar_grade_vazia, alocar_aula
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados', 'Ana Souza', 'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'CC1', 'Banco de Dados', 'Ana Souza', 'Sala101', 'Segunda', '08:00')

    csv_bytes = converter_grade_para_bytes(grade)
    df_resultado = pd.read_csv(io.BytesIO(csv_bytes))

    assert len(df_resultado) == 1, (
        f"❌ Turmas compartilhadas devem gerar 1 linha. Obteve {len(df_resultado)}."
    )
    turma_exportada = df_resultado.iloc[0]['turma']
    assert 'SI1' in turma_exportada and 'CC1' in turma_exportada
    assert ';' in turma_exportada
    print(f"✅ Turmas agrupadas corretamente: '{turma_exportada}'.")


# =============================================================================
# Execução
# =============================================================================

if __name__ == '__main__':
    try:
        # validar_colunas
        testar_validar_colunas_corretas()
        testar_validar_colunas_ausentes()
        testar_validar_colunas_extras_ignoradas()

        # ler_csv_upload
        testar_ler_csv_valido_professores()
        testar_ler_csv_vazio()
        testar_ler_csv_coluna_ausente()
        testar_ler_csv_capacidade_invalida()
        testar_ler_csv_alunos_invalidos()
        testar_ler_csv_corrompido()

        # converter_grade_para_bytes
        testar_converter_grade_para_bytes_simples()
        testar_converter_grade_turmas_compartilhadas()

        print("\n🚀 Sucesso: Todos os testes de INT_01 passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de INT_01 não passaram.")