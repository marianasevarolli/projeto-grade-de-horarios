"""
Testes para gerar_relatorio_falhas() — REL_01
Sprint S9 | Faculdade Impacta — Engenharia de Software | SI NOITE 2A

Cobertura:
    Estrutura do DataFrame retornado
    Turmas sem falhas → DataFrame vazio
    Identificação correta das turmas não alocadas
    Motivos inferidos para cada cenário de falha
    Salvamento em disco e UTF-8
    Parâmetros opcionais (sem professores / sem salas)
"""

import sys
import os
import tempfile

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from projeto import gerar_relatorio_falhas, criar_grade_vazia, alocar_aula


# =============================================================================
# AUXILIARES
# =============================================================================

COLUNAS_ESPERADAS = ['turma', 'disciplina', 'alunos', 'tipo', 'motivo_provavel']


def _turmas(*linhas):
    """Cria DataFrame de turmas a partir de tuplas (turma, alunos, disc, tipo)."""
    return pd.DataFrame(
        linhas, columns=['turma', 'alunos', 'disciplina', 'tipo']
    )


def _profs(*linhas):
    """Cria DataFrame de professores a partir de tuplas (matricula, nome, disc, dia, hora)."""
    return pd.DataFrame(
        linhas, columns=['matricula', 'nome', 'disciplina', 'dia', 'horario']
    )


def _salas(*linhas):
    """Cria DataFrame de salas a partir de tuplas (sala, capacidade, tipo)."""
    return pd.DataFrame(
        linhas, columns=['sala', 'capacidade', 'tipo']
    )


def _grade_com(*alocacoes):
    """
    Monta uma grade com alocações explícitas.
    Cada alocação é tupla: (turma, disc, prof, sala, dia, hora).
    """
    grade = criar_grade_vazia()
    for turma, disc, prof, sala, dia, hora in alocacoes:
        grade = alocar_aula(grade, turma, disc, prof, sala, dia, hora)
    return grade


# =============================================================================
# TESTES DE ESTRUTURA E TIPO DE RETORNO
# =============================================================================

class TestEstrutura:
    """O DataFrame retornado deve ter exatamente as colunas definidas."""

    def test_retorna_dataframe(self):
        turmas = _turmas(('T1', 20, 'Math', 'Teorica'))
        grade  = _grade_com(('T1', 'Math', 'Prof', 'S1', 'Segunda', '08:00'))
        rel = gerar_relatorio_falhas(turmas, grade)
        assert isinstance(rel, pd.DataFrame)

    def test_colunas_corretas_quando_ha_falhas(self):
        turmas = _turmas(('T1', 20, 'Math', 'Teorica'))
        grade  = criar_grade_vazia()   # nada alocado
        rel = gerar_relatorio_falhas(turmas, grade)
        assert list(rel.columns) == COLUNAS_ESPERADAS

    def test_colunas_corretas_quando_sem_falhas(self):
        turmas = _turmas(('T1', 20, 'Math', 'Teorica'))
        grade  = _grade_com(('T1', 'Math', 'Prof', 'S1', 'Segunda', '08:00'))
        rel = gerar_relatorio_falhas(turmas, grade)
        assert list(rel.columns) == COLUNAS_ESPERADAS


# =============================================================================
# TESTES DE IDENTIFICAÇÃO DAS TURMAS NÃO ALOCADAS
# =============================================================================

class TestIdentificacaoFalhas:
    """Verifica se as turmas corretas aparecem no relatório."""

    def test_todas_alocadas_retorna_vazio(self):
        turmas = _turmas(('T1', 20, 'Math', 'Teorica'))
        grade  = _grade_com(('T1', 'Math', 'Prof', 'S1', 'Segunda', '08:00'))
        rel = gerar_relatorio_falhas(turmas, grade)
        assert rel.empty

    def test_nenhuma_alocada_retorna_todas(self):
        turmas = _turmas(
            ('T1', 20, 'Math',  'Teorica'),
            ('T2', 15, 'Fisic', 'Teorica'),
        )
        rel = gerar_relatorio_falhas(turmas, criar_grade_vazia())
        assert set(rel['turma']) == {'T1', 'T2'}

    def test_apenas_turma_nao_alocada_aparece(self):
        turmas = _turmas(
            ('T1', 20, 'Math', 'Teorica'),
            ('T2', 15, 'Math', 'Teorica'),
        )
        grade = _grade_com(('T1', 'Math', 'Prof', 'S1', 'Segunda', '08:00'))
        rel = gerar_relatorio_falhas(turmas, grade)
        assert list(rel['turma']) == ['T2']

    def test_relatorio_preserva_dados_originais(self):
        """alunos e tipo devem vir do DataFrame original de turmas."""
        turmas = _turmas(('T1', 35, 'Bio', 'Laboratorio'))
        rel = gerar_relatorio_falhas(turmas, criar_grade_vazia())
        assert int(rel.iloc[0]['alunos']) == 35
        assert rel.iloc[0]['tipo'] == 'Laboratorio'


# =============================================================================
# TESTES DOS MOTIVOS INFERIDOS
# =============================================================================

class TestMotivos:
    """Verifica se o motivo_provavel é coerente com os dados fornecidos."""

    def test_sem_professor_motivo_correto(self):
        """Sem professor para a disciplina → motivo menciona 'professor'."""
        turmas = _turmas(('T1', 20, 'Quimica', 'Teorica'))
        profs  = _profs(('001', 'Ana', 'Matematica', 'Segunda', '08:00'))
        salas  = _salas(('S1', 40, 'Sala'))
        rel = gerar_relatorio_falhas(
            turmas, criar_grade_vazia(), professores=profs, salas=salas
        )
        motivo = rel.iloc[0]['motivo_provavel'].lower()
        assert 'professor' in motivo

    def test_sem_sala_tipo_correto_motivo(self):
        """Sem sala de Lab → motivo menciona 'laboratorio'."""
        turmas = _turmas(('T1', 20, 'Lab1', 'Laboratorio'))
        profs  = _profs(('001', 'Ana', 'Lab1', 'Segunda', '08:00'))
        salas  = _salas(('S1', 40, 'Sala'))      # só sala teórica
        rel = gerar_relatorio_falhas(
            turmas, criar_grade_vazia(), professores=profs, salas=salas
        )
        motivo = rel.iloc[0]['motivo_provavel'].lower()
        assert 'laboratorio' in motivo or 'laboratório' in motivo

    def test_sem_capacidade_suficiente_motivo(self):
        """Sala do tipo correto mas pequena demais → motivo menciona capacidade.
        Nota: turma com tipo 'Teorica' casa com sala tipo 'Teorica' no motor.
        """
        turmas = _turmas(('T1', 50, 'Mat', 'Teorica'))
        profs  = _profs(('001', 'Ana', 'Mat', 'Segunda', '08:00'))
        salas  = _salas(('S1', 10, 'Teorica'))   # tipo correto, capacidade insuficiente
        rel = gerar_relatorio_falhas(
            turmas, criar_grade_vazia(), professores=profs, salas=salas
        )
        motivo = rel.iloc[0]['motivo_provavel'].lower()
        assert 'capacidade' in motivo or 'aluno' in motivo

    def test_conflito_horario_motivo(self):
        """Recursos existem mas conflito de horário → motivo menciona conflito."""
        turmas = _turmas(('T1', 20, 'Mat', 'Teorica'))
        profs  = _profs(('001', 'Ana', 'Mat', 'Segunda', '08:00'))
        salas  = _salas(('S1', 40, 'Teorica'))   # tipo correto, capacidade ok
        # Simula grade já ocupada (mas T1 não está nela)
        grade = _grade_com(('T2', 'Mat', 'Ana', 'S1', 'Segunda', '08:00'))
        rel = gerar_relatorio_falhas(
            turmas, grade, professores=profs, salas=salas
        )
        motivo = rel.iloc[0]['motivo_provavel'].lower()
        assert 'conflito' in motivo or 'slot' in motivo or 'ocupado' in motivo

    def test_motivo_sem_profs_sem_salas_nao_trava(self):
        """Sem DataFrames opcionais → deve retornar motivo genérico, não travar."""
        turmas = _turmas(('T1', 20, 'X', 'Teorica'))
        rel = gerar_relatorio_falhas(turmas, criar_grade_vazia())
        assert rel.iloc[0]['motivo_provavel'] != ''


# =============================================================================
# TESTES DE PERSISTÊNCIA EM DISCO
# =============================================================================

class TestPersistencia:
    """Verifica salvamento correto do arquivo CSV."""

    def test_salva_arquivo_csv(self, tmp_path):
        """Com falhas, o arquivo deve ser criado no caminho indicado."""
        turmas = _turmas(('T1', 20, 'X', 'Teorica'))
        caminho = str(tmp_path / 'falhas.csv')
        gerar_relatorio_falhas(turmas, criar_grade_vazia(), caminho=caminho)
        assert os.path.exists(caminho)

    def test_arquivo_csv_legivel(self, tmp_path):
        """O CSV salvo deve ser lido de volta sem erros."""
        turmas = _turmas(('T1', 20, 'X', 'Teorica'))
        caminho = str(tmp_path / 'falhas.csv')
        gerar_relatorio_falhas(turmas, criar_grade_vazia(), caminho=caminho)
        df = pd.read_csv(caminho, encoding='utf-8')
        assert list(df.columns) == COLUNAS_ESPERADAS
        assert len(df) == 1

    def test_cria_diretorio_automaticamente(self, tmp_path):
        """makedirs deve criar subdiretório inexistente sem erros."""
        turmas = _turmas(('T1', 20, 'X', 'Teorica'))
        caminho = str(tmp_path / 'subdir' / 'falhas.csv')
        gerar_relatorio_falhas(turmas, criar_grade_vazia(), caminho=caminho)
        assert os.path.exists(caminho)

    def test_sem_falhas_nao_chama_to_csv(self, tmp_path):
        """Se todas as turmas foram alocadas, nenhum arquivo é criado."""
        turmas = _turmas(('T1', 20, 'Math', 'Teorica'))
        grade  = _grade_com(('T1', 'Math', 'Prof', 'S1', 'Segunda', '08:00'))
        caminho = str(tmp_path / 'falhas.csv')
        gerar_relatorio_falhas(turmas, grade, caminho=caminho)
        # Com todas alocadas, o arquivo NÃO deve ser criado
        # (a função retorna early com DataFrame vazio antes do to_csv)
        assert not os.path.exists(caminho)