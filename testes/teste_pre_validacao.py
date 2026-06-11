"""
Testes para validar_consistencia_dados() — PRE_01
Sprint S9 | Faculdade Impacta — Engenharia de Software | SI NOITE 2A

Cobertura:
    PRE_01-A → Turma Laboratorio sem sala Laboratorio
    PRE_01-B → Disciplina sem professor habilitado
    PRE_01-C → Capacidade/alunos zero ou negativo
    PRE_01-D → Professor com dia ou horário NaN
    Cenários de dados consistentes (lista vazia esperada)
    Cenários com DataFrames vazios (não deve travar)
"""

import sys
import os
import pandas as pd
import pytest

# Garante que a raiz do projeto está no path, independente de onde o pytest
# é invocado.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from projeto import validar_consistencia_dados


# =============================================================================
# AUXILIARES — construtores de DataFrames mínimos para os testes
# =============================================================================

def _prof(nome='Ana', disciplina='Matematica', dia='Segunda', horario='08:00'):
    return pd.DataFrame([{
        'matricula': '001', 'nome': nome,
        'disciplina': disciplina, 'dia': dia, 'horario': horario
    }])


def _turma(turma='SI1', alunos=20, disciplina='Matematica', tipo='Teorica'):
    return pd.DataFrame([{
        'turma': turma, 'alunos': alunos,
        'disciplina': disciplina, 'tipo': tipo
    }])


def _sala(sala='S101', capacidade=40, tipo='Sala'):
    return pd.DataFrame([{
        'sala': sala, 'capacidade': capacidade, 'tipo': tipo
    }])


def _montar(prof_df, turma_df, sala_df):
    return {'professores': prof_df, 'turmas': turma_df, 'salas': sala_df}


# =============================================================================
# TESTES PRE_01-A — Laboratorio sem sala compatível
# =============================================================================

class TestPreA:
    """Turma do tipo Laboratorio sem sala do mesmo tipo."""

    def test_turma_lab_sem_sala_lab_gera_aviso(self):
        """Turma Lab + apenas sala teórica → aviso PRE_01-A."""
        data = _montar(
            _prof(),
            _turma(tipo='Laboratorio'),
            _sala(tipo='Sala')          # nenhuma sala de lab
        )
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-A' in a for a in avisos), (
            "Esperava aviso PRE_01-A, mas nenhum foi gerado."
        )

    def test_turma_lab_com_sala_lab_sem_aviso(self):
        """Turma Lab + sala Lab → sem aviso A."""
        data = _montar(
            _prof(),
            _turma(tipo='Laboratorio'),
            _sala(tipo='Laboratorio')
        )
        avisos = validar_consistencia_dados(data)
        assert not any('PRE_01-A' in a for a in avisos)

    def test_turma_teorica_sem_sala_lab_sem_aviso_a(self):
        """Turma Teórica não dispara PRE_01-A mesmo sem sala de lab."""
        data = _montar(
            _prof(),
            _turma(tipo='Teorica'),
            _sala(tipo='Sala')
        )
        avisos = validar_consistencia_dados(data)
        assert not any('PRE_01-A' in a for a in avisos)

    def test_aviso_lista_nomes_das_turmas(self):
        """O aviso PRE_01-A deve mencionar o identificador da turma."""
        data = _montar(
            _prof(),
            _turma(turma='LAB99', tipo='Laboratorio'),
            _sala(tipo='Sala')
        )
        avisos = validar_consistencia_dados(data)
        aviso_a = next(a for a in avisos if 'PRE_01-A' in a)
        assert 'LAB99' in aviso_a


# =============================================================================
# TESTES PRE_01-B — Disciplina sem professor habilitado
# =============================================================================

class TestPreB:
    """Disciplina em turmas.csv sem correspondente em professores.csv."""

    def test_disciplina_sem_professor_gera_aviso(self):
        """Disciplina 'Fisica' nas turmas mas nenhum prof de Fisica → aviso B."""
        data = _montar(
            _prof(disciplina='Matematica'),
            _turma(disciplina='Fisica'),
            _sala()
        )
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-B' in a for a in avisos)

    def test_disciplina_com_professor_sem_aviso(self):
        """Disciplina presente em ambos os CSVs → sem aviso B."""
        data = _montar(
            _prof(disciplina='Matematica'),
            _turma(disciplina='Matematica'),
            _sala()
        )
        avisos = validar_consistencia_dados(data)
        assert not any('PRE_01-B' in a for a in avisos)

    def test_aviso_menciona_nome_disciplina(self):
        """O aviso PRE_01-B deve mencionar o nome da disciplina ausente."""
        data = _montar(
            _prof(disciplina='Quimica'),
            _turma(disciplina='Biologia'),
            _sala()
        )
        avisos = validar_consistencia_dados(data)
        aviso_b = next(a for a in avisos if 'PRE_01-B' in a)
        assert 'Biologia' in aviso_b

    def test_multiplas_disciplinas_sem_prof(self):
        """Duas disciplinas sem professor → dois avisos PRE_01-B."""
        turmas = pd.DataFrame([
            {'turma': 'T1', 'alunos': 20, 'disciplina': 'Alpha', 'tipo': 'Teorica'},
            {'turma': 'T2', 'alunos': 20, 'disciplina': 'Beta',  'tipo': 'Teorica'},
        ])
        data = _montar(_prof(disciplina='Outro'), turmas, _sala())
        avisos = validar_consistencia_dados(data)
        avisos_b = [a for a in avisos if 'PRE_01-B' in a]
        assert len(avisos_b) == 2


# =============================================================================
# TESTES PRE_01-C — Capacidade ou alunos zero/negativo
# =============================================================================

class TestPreC:
    """Valores numéricos inválidos (zero ou negativos) nas colunas críticas."""

    def test_sala_capacidade_zero_gera_aviso(self):
        """Sala com capacidade 0 → aviso PRE_01-C."""
        data = _montar(_prof(), _turma(), _sala(capacidade=0))
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-C' in a for a in avisos)

    def test_sala_capacidade_negativa_gera_aviso(self):
        """Sala com capacidade -5 → aviso PRE_01-C."""
        data = _montar(_prof(), _turma(), _sala(capacidade=-5))
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-C' in a for a in avisos)

    def test_sala_capacidade_valida_sem_aviso(self):
        """Sala com capacidade 1 (mínimo válido) → sem aviso C."""
        data = _montar(_prof(), _turma(alunos=1), _sala(capacidade=1))
        avisos = validar_consistencia_dados(data)
        assert not any('PRE_01-C' in a for a in avisos)

    def test_turma_alunos_zero_gera_aviso(self):
        """Turma com 0 alunos → aviso PRE_01-C."""
        data = _montar(_prof(), _turma(alunos=0), _sala())
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-C' in a for a in avisos)

    def test_turma_alunos_negativo_gera_aviso(self):
        """Turma com -10 alunos → aviso PRE_01-C."""
        data = _montar(_prof(), _turma(alunos=-10), _sala())
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-C' in a for a in avisos)


# =============================================================================
# TESTES PRE_01-D — Professor com dia ou horário em branco
# =============================================================================

class TestPreD:
    """Professor com NaN em 'dia' ou 'horario'."""

    def test_professor_dia_nan_gera_aviso(self):
        """Professor sem dia preenchido → aviso PRE_01-D."""
        prof = pd.DataFrame([{
            'matricula': '001', 'nome': 'Carlos',
            'disciplina': 'Matematica', 'dia': None, 'horario': '08:00'
        }])
        data = _montar(prof, _turma(), _sala())
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-D' in a for a in avisos)

    def test_professor_horario_nan_gera_aviso(self):
        """Professor sem horário preenchido → aviso PRE_01-D."""
        prof = pd.DataFrame([{
            'matricula': '001', 'nome': 'Maria',
            'disciplina': 'Matematica', 'dia': 'Segunda', 'horario': None
        }])
        data = _montar(prof, _turma(), _sala())
        avisos = validar_consistencia_dados(data)
        assert any('PRE_01-D' in a for a in avisos)

    def test_professor_completo_sem_aviso(self):
        """Professor com dia e horário válidos → sem aviso D."""
        data = _montar(_prof(), _turma(), _sala())
        avisos = validar_consistencia_dados(data)
        assert not any('PRE_01-D' in a for a in avisos)

    def test_aviso_menciona_nome_professor(self):
        """Aviso PRE_01-D deve incluir o nome do professor problemático."""
        prof = pd.DataFrame([{
            'matricula': '001', 'nome': 'ProfBranco',
            'disciplina': 'X', 'dia': float('nan'), 'horario': '10:00'
        }])
        data = _montar(prof, _turma(disciplina='X'), _sala())
        avisos = validar_consistencia_dados(data)
        aviso_d = next(a for a in avisos if 'PRE_01-D' in a)
        assert 'ProfBranco' in aviso_d


# =============================================================================
# TESTES DE DADOS CONSISTENTES E EDGE CASES
# =============================================================================

class TestConsistentes:
    """Casos sem problemas: lista de avisos deve ser vazia."""

    def test_dados_completamente_consistentes(self):
        """Dados válidos → lista vazia."""
        data = _montar(_prof(), _turma(), _sala())
        assert validar_consistencia_dados(data) == []

    def test_retorna_lista(self):
        """Sempre retorna list, nunca None."""
        data = _montar(_prof(), _turma(), _sala())
        resultado = validar_consistencia_dados(data)
        assert isinstance(resultado, list)

    def test_dataframes_vazios_nao_travam(self):
        """DataFrames vazios não devem lançar exceção."""
        data = {
            'professores': pd.DataFrame(
                columns=['matricula', 'nome', 'disciplina', 'dia', 'horario']
            ),
            'turmas': pd.DataFrame(
                columns=['turma', 'alunos', 'disciplina', 'tipo']
            ),
            'salas': pd.DataFrame(
                columns=['sala', 'capacidade', 'tipo']
            ),
        }
        resultado = validar_consistencia_dados(data)
        assert isinstance(resultado, list)

    def test_chaves_ausentes_nao_travam(self):
        """Dicionário sem alguma chave (upload parcial) não deve travar."""
        resultado = validar_consistencia_dados({})
        assert isinstance(resultado, list)

    def test_multiplos_avisos_acumulados(self):
        """Dois problemas diferentes → pelo menos dois avisos."""
        data = _montar(
            _prof(disciplina='X'),          # prof habilitado em X
            _turma(disciplina='Y', tipo='Laboratorio'),  # Y sem prof + lab sem sala
            _sala(tipo='Sala')              # sem lab
        )
        avisos = validar_consistencia_dados(data)
        # Deve ter PRE_01-A (sem lab) + PRE_01-B (disciplina Y sem prof)
        assert len(avisos) >= 2