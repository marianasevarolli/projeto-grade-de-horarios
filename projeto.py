import pandas as pd
import os

# =============================================================================
# MÓDULO 1 — INGESTÃO DE DADOS (Sprint S3)
# Responsável por carregar e normalizar os três arquivos CSV de entrada.
# =============================================================================

def carregar_dados() -> dict:
    """
    Lê os três arquivos CSV da pasta 'csv/' e retorna um dicionário
    com DataFrames prontos para uso.
    Já realiza a conversão de tipos numéricos para evitar erros nas validações.
    """
    arquivos = {
        'professores': 'csv/professores.csv',
        'turmas':      'csv/turmas.csv',
        'salas':       'csv/salas.csv'
    }

    data = {}
    for chave, caminho in arquivos.items():
        if os.path.exists(caminho):
            data[chave] = pd.read_csv(caminho)
            if chave == 'salas':
                data[chave]['capacidade'] = pd.to_numeric(
                    data[chave]['capacidade'], errors='coerce'
                )
            if chave == 'turmas':
                data[chave]['alunos'] = pd.to_numeric(
                    data[chave]['alunos'], errors='coerce'
                )
        else:
            print(f"Erro: Arquivo '{caminho}' não encontrado.")

    return data


# =============================================================================
# MÓDULO 2 — VALIDAÇÕES / REGRAS DE NEGÓCIO (Sprints S4 e S5)
# Cada função representa uma regra isolada e reutilizável.
# Princípio SOLID: Single Responsibility — uma função, uma regra.
# =============================================================================

def validar_capacidade(turma: pd.Series, sala: pd.Series) -> bool:
    """
    RN_6 — A sala deve comportar a quantidade de alunos da turma.
    Retorna True se a sala tiver vagas suficientes.
    """
    return turma['alunos'] <= sala['capacidade']


def validar_tipo_sala(turma: pd.Series, sala: pd.Series) -> bool:
    """
    RN_7 — Correspondência exata de ambiente.
    Disciplinas de laboratório SÓ em laboratórios.
    Disciplinas teóricas SÓ em salas teóricas.
    Retorna True se os tipos forem compatíveis.
    """
    return turma['tipo'].lower() == sala['tipo'].lower()


def validar_habilitacao(professor: pd.Series, turma: pd.Series) -> bool:
    """
    RN_1 — O professor só pode lecionar disciplinas para as quais está habilitado.
    Retorna True se a disciplina do professor coincidir com a da turma.
    """
    return professor['disciplina'] == turma['disciplina']


def validar_disponibilidade(professor: pd.Series, dia: str, horario: str) -> bool:
    """
    RN_2 — O professor só pode ser alocado em seus horários disponíveis.
    Retorna True se o dia e horário solicitados baterem com os do professor no CSV.
    """
    return (professor['dia'] == dia) and (professor['horario'] == horario)


def verificar_todas_regras(
    professor: pd.Series,
    turma: pd.Series,
    sala: pd.Series,
    dia: str,
    horario: str
) -> bool:
    """
    Checklist completo de regras de negócio para uma combinação de alocação.
    Retorna True somente se TODAS as quatro regras forem satisfeitas.
    """
    return (
        validar_habilitacao(professor, turma)           and  # RN_1
        validar_capacidade(turma, sala)                 and  # RN_6
        validar_tipo_sala(turma, sala)                  and  # RN_7
        validar_disponibilidade(professor, dia, horario)     # RN_2
    )


# =============================================================================
# MÓDULO 3 — ALOCAÇÃO I / ESTRUTURA DA GRADE  (Sprint S6 — ALOC_01)
#
# Introduz a grade horária global e a trava de conflito de docente.
# Analogia: a grade é a "agenda coletiva da instituição". Antes de marcar
# qualquer aula, o sistema consulta essa agenda para checar disponibilidade.
# =============================================================================

def criar_grade_vazia() -> pd.DataFrame:
    """
    ALOC_01 — Cria a estrutura base da grade horária unificada.

    Retorna um DataFrame vazio com as colunas do arquivo de saída (grade_final.csv).
    Cada linha futura representa uma aula confirmada.

    Colunas:
        turma       → identificador da turma (ex: 'SI1')
        disciplina  → nome da disciplina
        professor   → nome do docente alocado
        sala        → identificador da sala
        dia         → dia da semana (ex: 'Segunda')
        horario     → horário no formato HH:MM (ex: '19:00')
    """
    colunas = ['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']
    return pd.DataFrame(columns=colunas)


def professor_ja_alocado(
    grade: pd.DataFrame,
    nome_professor: str,
    dia: str,
    horario: str
) -> bool:
    """
    ALOC_01 — Trava de conflito de agenda do professor (RN_3).

    Verifica se o professor já possui uma aula registrada na grade
    para o mesmo dia e horário solicitados.

    Retorna True  → professor OCUPADO  (alocação deve ser BLOQUEADA)
    Retorna False → professor LIVRE    (alocação pode prosseguir)
    """
    if grade.empty:
        return False

    conflito = grade[
        (grade['professor'] == nome_professor) &
        (grade['dia']       == dia)            &
        (grade['horario']   == horario)
    ]
    return not conflito.empty


def alocar_aula(
    grade: pd.DataFrame,
    turma: str,
    disciplina: str,
    nome_professor: str,
    sala: str,
    dia: str,
    horario: str
) -> pd.DataFrame:
    """
    ALOC_01 — Registra uma alocação validada na grade horária.

    Utiliza pd.concat para evitar o uso do método depreciado DataFrame.append.
    Retorna sempre um novo DataFrame com a linha adicionada.
    """
    nova_linha = pd.DataFrame([{
        'turma':      turma,
        'disciplina': disciplina,
        'professor':  nome_professor,
        'sala':       sala,
        'dia':        dia,
        'horario':    horario
    }])
    return pd.concat([grade, nova_linha], ignore_index=True)


# =============================================================================
# MÓDULO 4 — ALOCAÇÃO II / CONTROLE DE CONFLITOS AVANÇADO  (Sprint S7 — ALOC_02)
#
# Amplia o motor com duas novas travas e refatora o laço principal para que
# todas as restrições sejam verificadas de forma combinatória e exaustiva.
#
# Novas travas adicionadas nesta sprint:
#   sala_ja_ocupada()             → RN_5 (conflito de sala)
#   turma_ja_alocada_no_horario() → RN_4 (conflito de turma)
#
# O laço gerar_grade() foi expandido para:
#   1. Varrer TODOS os slots disponíveis de um professor (não apenas o primeiro)
#   2. Checar as três travas antes de qualquer alocação
#   3. Maximizar o número de turmas alocadas (RN_8)
# =============================================================================

def sala_ja_ocupada(
    grade: pd.DataFrame,
    id_sala: str,
    dia: str,
    horario: str
) -> bool:
    """
    ALOC_02 — Trava de conflito de sala física (RN_5).

    Verifica se a sala já está sendo usada por outra aula no mesmo
    dia e horário solicitados.

    Mecânica da trava:
        1. Filtra a grade pelas linhas onde 'sala' == id_sala
        2. Dentro desse filtro, procura 'dia' == dia  E  'horario' == horario
        3. Resultado não vazio → sala ocupada → retorna True
        4. Resultado vazio     → sala livre   → retorna False

    Retorna True  → sala OCUPADA  (alocação deve ser BLOQUEADA)
    Retorna False → sala LIVRE    (alocação pode prosseguir)
    """
    if grade.empty:
        return False

    conflito = grade[
        (grade['sala']    == id_sala) &
        (grade['dia']     == dia)     &
        (grade['horario'] == horario)
    ]
    return not conflito.empty


def turma_ja_alocada_no_horario(
    grade: pd.DataFrame,
    id_turma: str,
    dia: str,
    horario: str
) -> bool:
    """
    ALOC_02 — Trava de conflito de agenda da turma (RN_4).

    Verifica se a turma já possui uma aula alocada no mesmo dia e horário.
    Garante que nenhuma turma esteja em dois lugares ao mesmo tempo.

    Mecânica da trava:
        1. Filtra a grade pelas linhas onde 'turma' == id_turma
        2. Verifica se existe 'dia' == dia  E  'horario' == horario
        3. Resultado não vazio → turma ocupada → retorna True
        4. Resultado vazio     → turma livre   → retorna False

    Retorna True  → turma OCUPADA  (alocação deve ser BLOQUEADA)
    Retorna False → turma LIVRE    (alocação pode prosseguir)
    """
    if grade.empty:
        return False

    conflito = grade[
        (grade['turma']   == id_turma) &
        (grade['dia']     == dia)      &
        (grade['horario'] == horario)
    ]
    return not conflito.empty


def gerar_grade(data: dict) -> pd.DataFrame:
    """
    ALOC_02 — Motor principal de geração da grade (Algoritmo Greedy Expandido).

    Evolução em relação ao ALOC_01:
      - Itera sobre TODOS os slots disponíveis de cada professor, não só o
        primeiro encontrado, maximizando alocações (RN_8, RN_11).
      - Inclui as três travas de conflito antes de confirmar qualquer alocação:
            [TRAVA 1] professor_ja_alocado()       → RN_3
            [TRAVA 2] sala_ja_ocupada()             → RN_5  (ALOC_02)
            [TRAVA 3] turma_ja_alocada_no_horario() → RN_4  (ALOC_02)

    Critério de interrupção do laço:
        O laço interno (professor × sala) para assim que encontra a PRIMEIRA
        combinação válida para a turma corrente (comportamento Greedy).
        O laço externo (turmas) continua até que TODAS as turmas sejam tentadas.

    Fluxo completo por turma:
        Para cada turma:
          └─ Para cada linha do professor (múltiplos slots possíveis — RF_9):
               ├─ [RN_1]  Habilitado para a disciplina?
               ├─ [RN_2]  Disponível neste dia/horário?
               ├─ [TRAVA 1 — RN_3] Professor já alocado neste slot?
               ├─ [TRAVA 3 — RN_4] Turma já tem aula neste slot?   (ALOC_02)
               └─ Para cada sala:
                    ├─ [RN_6]  Sala comporta os alunos?
                    ├─ [RN_7]  Tipo de sala compatível?
                    ├─ [TRAVA 2 — RN_5] Sala já está ocupada?       (ALOC_02)
                    └─ Todas as travas passaram → aloca

    Retorna o DataFrame da grade preenchida.
    """
    grade = criar_grade_vazia()

    professores = data['professores']
    turmas      = data['turmas']
    salas       = data['salas']

    for _, turma in turmas.iterrows():
        alocado = False

        # ── Laço de varredura combinatória ────────────────────────────────
        # Itera sobre TODAS as linhas de professores (cada linha = um slot
        # de disponibilidade). Um mesmo professor pode aparecer várias vezes
        # no CSV com disciplinas e horários diferentes (RF_9).
        for _, professor in professores.iterrows():
            if alocado:
                break  # Critério de interrupção: turma já foi alocada

            # RN_1: professor está habilitado para esta disciplina?
            if not validar_habilitacao(professor, turma):
                continue

            dia     = professor['dia']
            horario = professor['horario']

            # RN_2: este slot (dia + horário) pertence à disponibilidade real?
            if not validar_disponibilidade(professor, dia, horario):
                continue

            # ── TRAVA 1 — Conflito de agenda do professor (RN_3 / ALOC_01) ─
            if professor_ja_alocado(grade, professor['nome'], dia, horario):
                continue
            # ─────────────────────────────────────────────────────────────

            # ── TRAVA 3 — Conflito de agenda da turma (RN_4 / ALOC_02) ────
            # Impede que a turma tenha duas disciplinas no mesmo slot.
            if turma_ja_alocada_no_horario(grade, turma['turma'], dia, horario):
                continue
            # ─────────────────────────────────────────────────────────────

            # ── Laço de busca de sala compatível ─────────────────────────
            for _, sala in salas.iterrows():

                # RN_6: a sala comporta a quantidade de alunos?
                if not validar_capacidade(turma, sala):
                    continue

                # RN_7: o tipo da sala é compatível com o tipo da disciplina?
                if not validar_tipo_sala(turma, sala):
                    continue

                # ── TRAVA 2 — Conflito de sala física (RN_5 / ALOC_02) ───
                # Impede que duas turmas ocupem a mesma sala ao mesmo tempo.
                if sala_ja_ocupada(grade, sala['sala'], dia, horario):
                    continue
                # ─────────────────────────────────────────────────────────

                # Todas as regras e travas passaram → registra na grade
                grade = alocar_aula(
                    grade,
                    turma['turma'],
                    turma['disciplina'],
                    professor['nome'],
                    sala['sala'],
                    dia,
                    horario
                )
                alocado = True
                break  # Sala encontrada: interrompe laço de salas

        if not alocado:
            print(
                f"⚠️  Turma '{turma['turma']}' ({turma['disciplina']}) "
                f"não pôde ser alocada — sem combinação válida de "
                f"professor, sala e horário disponíveis."
            )

    return grade


def exportar_grade(grade: pd.DataFrame, caminho: str = 'csv/grade_final.csv') -> None:
    """
    RF_8 — Exporta a grade gerada para um arquivo CSV.
    Salva no caminho informado (padrão: 'csv/grade_final.csv').
    """
    grade.to_csv(caminho, index=False)
    print(f"✅ Grade exportada com sucesso em '{caminho}'.")