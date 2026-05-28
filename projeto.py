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
            # Conversão de tipos numéricos para evitar comparações incorretas
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
        validar_habilitacao(professor, turma)      and  # RN_1
        validar_capacidade(turma, sala)            and  # RN_6
        validar_tipo_sala(turma, sala)             and  # RN_7
        validar_disponibilidade(professor, dia, horario)  # RN_2
    )


# =============================================================================
# MÓDULO 3 — ALOCAÇÃO I / MOTOR DE GRADE  (Sprint S6 — ALOC_01)
#
# Este módulo introduz a estrutura da grade horária global e a trava lógica
# que impede um professor de ser alocado em dois lugares ao mesmo tempo.
#
# Analogia: pense na grade como uma "agenda coletiva da instituição".
# Antes de marcar qualquer aula, o sistema consulta a agenda para ver se
# o professor já está ocupado naquele slot de dia+horário.
# =============================================================================

def criar_grade_vazia() -> pd.DataFrame:
    """
    ALOC_01 — Cria a estrutura base da grade horária unificada.

    A grade é um DataFrame vazio com as colunas definidas na documentação
    (Tabela de Saída). Cada linha futura representará uma aula alocada,
    com professor, turma, sala, dia e horário confirmados.

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
    ALOC_01 — TRAVA DE CONFLITO DE AGENDA DO PROFESSOR (RN_3).

    Verifica se o professor já possui uma aula registrada na grade
    para o mesmo dia e horário solicitados.

    Mecânica da trava:
        1. Filtra a grade pelas linhas onde 'professor' == nome_professor
        2. Dentro desse filtro, verifica se existe alguma linha com
           'dia' == dia  E  'horario' == horario
        3. Se o resultado NÃO estiver vazio → conflito detectado → retorna True
        4. Se o resultado estiver vazio     → professor livre    → retorna False

    Retorna True  → professor OCUPADO  (alocação deve ser BLOQUEADA)
    Retorna False → professor LIVRE    (alocação pode prosseguir)
    """
    if grade.empty:
        return False  # Grade vazia: nenhum conflito possível

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

    Recebe a grade atual e retorna uma nova grade com a linha adicionada.
    Utiliza pd.concat para preservar o índice e evitar o uso do método
    depreciado DataFrame.append.
    """
    nova_linha = pd.DataFrame([{
        'turma':       turma,
        'disciplina':  disciplina,
        'professor':   nome_professor,
        'sala':        sala,
        'dia':         dia,
        'horario':     horario
    }])
    return pd.concat([grade, nova_linha], ignore_index=True)


def gerar_grade(data: dict) -> pd.DataFrame:
    """
    ALOC_01 — Motor principal de geração da grade (Algoritmo Greedy).

    Estratégia Greedy: para cada turma, aceita a PRIMEIRA combinação válida
    encontrada de (professor → sala → dia/horário), sem tentar otimizar
    globalmente. É simples, rápido e suficiente para o escopo atual.

    Fluxo por turma:
        Para cada turma:
          └─ Para cada professor:
               ├─ Verifica habilitação           (RN_1)
               ├─ Verifica disponibilidade       (RN_2)
               ├─ [TRAVA] Verifica conflito na grade (RN_3 / ALOC_01)
               └─ Para cada sala:
                    ├─ Verifica capacidade       (RN_6)
                    ├─ Verifica tipo de sala      (RN_7)
                    └─ ✅ Aloca e passa para próxima turma

    Retorna o DataFrame da grade preenchida.
    """
    grade = criar_grade_vazia()

    professores = data['professores']
    turmas      = data['turmas']
    salas       = data['salas']

    for _, turma in turmas.iterrows():
        alocado = False

        for _, professor in professores.iterrows():
            if alocado:
                break

            # RN_1: professor habilitado para esta disciplina?
            if not validar_habilitacao(professor, turma):
                continue

            dia     = professor['dia']
            horario = professor['horario']

            # RN_2: este é o horário disponível do professor?
            if not validar_disponibilidade(professor, dia, horario):
                continue

            # ── TRAVA ALOC_01 ─────────────────────────────────────────────
            # RN_3: professor já está alocado em outro lugar neste slot?
            if professor_ja_alocado(grade, professor['nome'], dia, horario):
                continue  # bloqueia e tenta o próximo professor
            # ──────────────────────────────────────────────────────────────

            for _, sala in salas.iterrows():
                # RN_6: sala comporta a turma?
                if not validar_capacidade(turma, sala):
                    continue

                # RN_7: tipo de sala compatível com a disciplina?
                if not validar_tipo_sala(turma, sala):
                    continue

                # Todas as regras passaram → registra na grade
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
                break  # sala encontrada, sai do loop de salas

        if not alocado:
            print(
                f"⚠️  Turma '{turma['turma']}' ({turma['disciplina']}) "
                f"não pôde ser alocada — verifique professores, salas e horários disponíveis."
            )

    return grade


def exportar_grade(grade: pd.DataFrame, caminho: str = 'csv/grade_final.csv') -> None:
    """
    RF_8 — Exporta a grade gerada para um arquivo CSV.
    Salva no caminho informado (padrão: 'csv/grade_final.csv').
    """
    grade.to_csv(caminho, index=False)
    print(f"✅ Grade exportada com sucesso em '{caminho}'.")