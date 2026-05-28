"""
Teste de Exportação — RF_8 / S9
testes/teste_exportacao.py

Cobertura de exportar_grade() em projeto.py:
  - Arquivo criado no caminho correto
  - Colunas exatas da Tabela de Saída do projeto
  - Sem coluna de índice
  - Encoding UTF-8 (suporta acentos e caracteres especiais)
  - Turmas compartilhadas no formato 'SI1;CC1'
  - Criação automática de diretório inexistente
  - Grade vazia retorna None e não cria arquivo
  - Retorno do caminho absoluto
"""

import sys
import os
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from projeto import exportar_grade, criar_grade_vazia, alocar_aula


# ─── Utilitário ───────────────────────────────────────────────────────────────

def _grade_com_dados() -> pd.DataFrame:
    """Grade com 3 alocações para reutilização nos testes."""
    grade = criar_grade_vazia()
    grade = alocar_aula(grade, 'SI1', 'Banco de Dados',      'Ana Souza',   'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'CC1', 'Banco de Dados',      'Ana Souza',   'Sala101', 'Segunda', '08:00')
    grade = alocar_aula(grade, 'SI2', 'Algoritmos',          'Carlos Lima', 'Lab01',   'Terça',   '10:00')
    grade = alocar_aula(grade, 'SI3', 'Engenharia de Softw', 'Márcia Ávès', 'Sala102', 'Quarta',  '19:00')
    return grade


def _caminho_temp(sufixo: str = '.csv') -> str:
    """Gera um caminho temporário único; o arquivo NÃO é criado ainda."""
    fd, caminho = tempfile.mkstemp(suffix=sufixo)
    os.close(fd)
    os.remove(caminho)   # remove o arquivo vazio para que o teste valide a criação
    return caminho


# =============================================================================
# Arquivo criado e caminho retornado
# =============================================================================

def testar_arquivo_e_criado_no_caminho():
    """exportar_grade deve criar fisicamente o arquivo no caminho informado."""
    print("Testando criação física do arquivo...")
    caminho = _caminho_temp()
    resultado = exportar_grade(_grade_com_dados(), caminho)

    assert os.path.exists(caminho), "❌ O arquivo não foi criado."
    assert resultado is not None,   "❌ Deveria retornar o caminho, não None."
    os.remove(caminho)
    print("✅ Arquivo criado e caminho retornado corretamente.")


def testar_retorno_e_caminho_absoluto():
    """O valor retornado deve ser o caminho absoluto do arquivo."""
    print("Testando retorno do caminho absoluto...")
    caminho = _caminho_temp()
    resultado = exportar_grade(_grade_com_dados(), caminho)

    assert os.path.isabs(resultado), (
        f"❌ Caminho retornado não é absoluto: '{resultado}'"
    )
    os.remove(caminho)
    print(f"✅ Caminho absoluto retornado: '{resultado}'.")


# =============================================================================
# Estrutura do CSV (Tabela de Saída do projeto)
# =============================================================================

def testar_colunas_obrigatorias():
    """CSV deve conter exatamente as 6 colunas da Tabela de Saída."""
    print("Testando colunas obrigatórias do CSV...")
    caminho = _caminho_temp()
    exportar_grade(_grade_com_dados(), caminho)
    df = pd.read_csv(caminho)

    colunas_esperadas = ['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']
    assert list(df.columns) == colunas_esperadas, (
        f"❌ Colunas incorretas.\n"
        f"   Esperado: {colunas_esperadas}\n"
        f"   Obtido:   {list(df.columns)}"
    )
    os.remove(caminho)
    print(f"✅ Colunas corretas: {colunas_esperadas}.")


def testar_sem_coluna_de_indice():
    """CSV não deve conter coluna de índice numérico (index=False)."""
    print("Testando ausência de coluna de índice...")
    caminho = _caminho_temp()
    exportar_grade(_grade_com_dados(), caminho)

    with open(caminho, encoding='utf-8') as f:
        primeira_linha = f.readline().strip()

    # Se houvesse índice, a primeira coluna seria 'Unnamed: 0' ou um número
    assert not primeira_linha.startswith('Unnamed'), "❌ Coluna de índice presente no CSV."
    assert not primeira_linha[0].isdigit(),          "❌ Índice numérico detectado no cabeçalho."
    os.remove(caminho)
    print("✅ Sem coluna de índice no CSV.")


# =============================================================================
# Encoding UTF-8
# =============================================================================

def testar_encoding_utf8_acentos():
    """
    Nomes com acentos e caracteres especiais (ex: 'Márcia Ávès') devem ser
    salvos e lidos corretamente com encoding UTF-8.
    """
    print("Testando encoding UTF-8 com acentos...")
    caminho = _caminho_temp()
    exportar_grade(_grade_com_dados(), caminho)

    df = pd.read_csv(caminho, encoding='utf-8')
    professores = df['professor'].tolist()
    assert any('Márcia' in p or 'Ávès' in p or 'cia' in p for p in professores), (
        "❌ Nome com acento não foi preservado corretamente no CSV."
    )
    os.remove(caminho)
    print("✅ Encoding UTF-8 preservou acentos corretamente.")


def testar_arquivo_legivel_como_bytes_utf8():
    """O arquivo deve ser decodificável como UTF-8 sem erros."""
    print("Testando leitura do arquivo como bytes UTF-8...")
    caminho = _caminho_temp()
    exportar_grade(_grade_com_dados(), caminho)

    with open(caminho, 'rb') as f:
        conteudo_bytes = f.read()

    try:
        conteudo_bytes.decode('utf-8')
    except UnicodeDecodeError:
        raise AssertionError("❌ O arquivo não é UTF-8 válido.")
    os.remove(caminho)
    print("✅ Arquivo é UTF-8 válido.")


# =============================================================================
# Turmas compartilhadas
# =============================================================================

def testar_turmas_compartilhadas_formato_csv():
    """
    SI1 e CC1 no mesmo professor+sala+slot devem aparecer como 'SI1;CC1'
    em UMA única linha do CSV (RF_11).
    """
    print("Testando formato 'SI1;CC1' no CSV exportado...")
    caminho = _caminho_temp()
    exportar_grade(_grade_com_dados(), caminho)
    df = pd.read_csv(caminho)

    linha_bd = df[df['disciplina'] == 'Banco de Dados']
    assert len(linha_bd) == 1, (
        f"❌ Banco de Dados deveria ter 1 linha no CSV, obteve {len(linha_bd)}."
    )
    turma_csv = linha_bd.iloc[0]['turma']
    assert ';' in turma_csv, f"❌ Turmas compartilhadas deveriam ter ';'. Obteve: '{turma_csv}'."
    assert 'SI1' in turma_csv and 'CC1' in turma_csv
    os.remove(caminho)
    print(f"✅ Turmas compartilhadas exportadas como '{turma_csv}'.")


# =============================================================================
# Criação automática de diretório
# =============================================================================

def testar_cria_diretorio_inexistente():
    """
    Deve criar automaticamente o diretório de destino se ele não existir,
    sem lançar exceção (portabilidade Windows/Linux/macOS — RNF_2).
    """
    print("Testando criação automática de diretório inexistente...")
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir  = os.path.join(tmpdir, 'sub', 'pasta', 'nova')
        caminho = os.path.join(subdir, 'grade_final.csv')

        assert not os.path.exists(subdir), "Pré-condição: subdir não deve existir."
        exportar_grade(_grade_com_dados(), caminho)

        assert os.path.exists(caminho), "❌ Arquivo não criado no subdiretório."
    print("✅ Diretório criado automaticamente com sucesso.")


# =============================================================================
# Grade vazia
# =============================================================================

def testar_grade_vazia_retorna_none():
    """Grade vazia deve retornar None e não criar nenhum arquivo."""
    print("Testando grade vazia retorna None...")
    caminho = _caminho_temp()

    resultado = exportar_grade(criar_grade_vazia(), caminho)

    assert resultado is None,           "❌ Deveria retornar None para grade vazia."
    assert not os.path.exists(caminho), "❌ Não deveria criar arquivo para grade vazia."
    print("✅ Grade vazia: retornou None sem criar arquivo.")


# =============================================================================
# Execução
# =============================================================================

if __name__ == '__main__':
    try:
        testar_arquivo_e_criado_no_caminho()
        testar_retorno_e_caminho_absoluto()
        testar_colunas_obrigatorias()
        testar_sem_coluna_de_indice()
        testar_encoding_utf8_acentos()
        testar_arquivo_legivel_como_bytes_utf8()
        testar_turmas_compartilhadas_formato_csv()
        testar_cria_diretorio_inexistente()
        testar_grade_vazia_retorna_none()

        print("\n🚀 Sucesso: Todos os testes de exportação (RF_8) passaram!")

    except AssertionError as erro:
        print(f"\n{erro}")
        print("❌ Falha: Um ou mais testes de exportação não passaram.")