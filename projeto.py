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
# MÓDULO 4 — ALOCAÇÃO II / CONTROLE DE CONFLITOS  (Sprint S7 — ALOC_02)
#
# Travas de conflito de sala (RN_5) e de turma (RN_4).
# =============================================================================

def sala_ja_ocupada(
    grade: pd.DataFrame,
    id_sala: str,
    dia: str,
    horario: str
) -> bool:
    """
    ALOC_02 — Trava de conflito de sala física (RN_5).

    Verifica se a sala já está sendo usada por outra aula no mesmo slot.

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

    Verifica se a turma já possui uma aula alocada no mesmo slot.
    Impede que uma turma esteja em dois lugares ao mesmo tempo.

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


# =============================================================================
# MÓDULO 5 — ALOCAÇÃO III / TURMAS COMPARTILHADAS E DESEMPATE (ALOC_03)
#
# Implementa os requisitos que faltavam na auditoria:
#
#   RF_11 / RN_9  → Aulas compartilhadas: múltiplas turmas na mesma aula
#   RN_10         → Capacidade somada quando turmas compartilham a aula
#   RN_12         → Desempate por menor carga horária do professor
#   RN_13         → Teórica e Laboratório tratados como grupos independentes
#
# Lógica de agrupamento (analogia):
#   Pense como um "pool de caronas": turmas com o mesmo destino
#   (disciplina + tipo) são agrupadas. O sistema tenta colocar todas
#   no mesmo "carro" (sala + professor + horário). Se não couberem
#   juntas, cada uma vai em seu próprio carro (fallback individual).
# =============================================================================

def contar_aulas_professor(grade: pd.DataFrame, nome_professor: str) -> int:
    """
    ALOC_03 — Conta o total de aulas já alocadas para o professor na grade.

    Usado pelo critério de desempate (RN_12): quando dois professores são
    igualmente válidos, o com menor contagem é escolhido primeiro.

    Retorna 0 se a grade estiver vazia ou o professor não tiver aulas.
    """
    if grade.empty:
        return 0
    return len(grade[grade['professor'] == nome_professor])


def agrupar_turmas_por_disciplina(turmas: pd.DataFrame) -> list:
    """
    ALOC_03 — Agrupa turmas com a mesma disciplina E o mesmo tipo (RN_9, RN_13).

    RN_9:  turmas com a mesma disciplina PODEM compartilhar a mesma aula.
    RN_13: componentes teórico e laboratorial da mesma disciplina são
           GRUPOS SEPARADOS — nunca são agrupados entre si.

    Exemplo:
        'Banco de Dados - Teorica' (SI1, CC1) → Grupo 1 (podem compartilhar)
        'Banco de Dados - Lab'     (SI1)      → Grupo 2 (alocação independente)

    Retorna uma lista de DataFrames, um por grupo único de disciplina+tipo.
    """
    grupos = []
    for _, grupo in turmas.groupby(['disciplina', 'tipo'], sort=False):
        grupos.append(grupo.reset_index(drop=True))
    return grupos


def calcular_total_alunos(grupo: pd.DataFrame) -> int:
    """
    ALOC_03 — Calcula a soma total de alunos de todas as turmas do grupo (RN_10).

    Usada para validar se uma sala comporta um grupo de turmas compartilhadas.
    """
    return int(grupo['alunos'].sum())


def validar_capacidade_grupo(grupo: pd.DataFrame, sala: pd.Series) -> bool:
    """
    ALOC_03 — Valida se a sala comporta a SOMA de alunos do grupo (RN_10).

    Substitui validar_capacidade() quando há aula compartilhada:
    a sala precisa acomodar o total combinado, não apenas uma turma.

    Retorna True se capacidade da sala >= total de alunos do grupo.
    """
    return calcular_total_alunos(grupo) <= sala['capacidade']


def _tentar_alocar_grupo(
    grade: pd.DataFrame,
    grupo: pd.DataFrame,
    professores: pd.DataFrame,
    salas: pd.DataFrame
) -> tuple:
    """
    ALOC_03 — Núcleo do motor: tenta alocar um grupo de turmas em um único slot.

    Fluxo:
      1. Ordena professores por carga horária crescente (RN_12 — desempate).
      2. Para cada professor (do menos ocupado ao mais ocupado):
           a. Verifica habilitação (RN_1) e disponibilidade (RN_2).
           b. [TRAVA 1] Professor já alocado neste slot? (RN_3)
           c. [TRAVA 3] Alguma turma do grupo já tem aula neste slot? (RN_4)
           d. Para cada sala:
                i.  Tipo compatível? (RN_7)
                ii. Capacidade suficiente para o grupo inteiro? (RN_10)
                iii.[TRAVA 2] Sala já ocupada neste slot? (RN_5)
                iv. ✅ Aloca todas as turmas do grupo no mesmo slot.

    Funciona para grupos de 1 turma (individual) ou N turmas (compartilhado).

    Retorna: (grade_atualizada, True) em caso de sucesso.
             (grade_original,   False) se nenhuma combinação válida foi encontrada.
    """
    # RN_12: ordena professores pela carga atual (crescente) para desempate.
    # O agrupamento é feito por matrícula — identificador único do professor.
    # Usar nome causaria colisão entre dois professores com o mesmo nome.
    # O nome é extraído depois, apenas para gravar na grade (saída legível).
    matriculas_unicas = professores['matricula'].unique()
    carga_por_matricula = {
        mat: contar_aulas_professor(
            grade,
            professores.loc[professores['matricula'] == mat, 'nome'].iloc[0]
        )
        for mat in matriculas_unicas
    }
    matriculas_ordenadas = sorted(
        matriculas_unicas, key=lambda m: carga_por_matricula[m]
    )

    # Turma de referência: disciplina e tipo são iguais em todo o grupo.
    turma_ref = grupo.iloc[0]

    for matricula in matriculas_ordenadas:

        # Todas as linhas deste professor no CSV, identificadas pela matrícula.
        # Cada linha representa uma disciplina habilitada + um slot disponível.
        linhas_professor = professores[professores['matricula'] == matricula]

        # Nome é extraído uma única vez — usado apenas na gravação da grade.
        nome_professor = linhas_professor.iloc[0]['nome']

        # RN_1: o professor possui ao menos uma linha habilitada para a
        # disciplina do grupo?
        linhas_habilitadas = linhas_professor[
            linhas_professor['disciplina'] == turma_ref['disciplina']
        ]
        if linhas_habilitadas.empty:
            continue  # Professor não habilitado para esta disciplina

        # RN_2: itera sobre TODOS os slots de disponibilidade do professor,
        # independentemente de a qual disciplina cada slot foi associado no CSV.
        # A disponibilidade pertence ao professor (matrícula), não à disciplina.
        for _, slot in linhas_professor.iterrows():

            dia     = slot['dia']
            horario = slot['horario']

            # TRAVA 1 — RN_3: professor já está comprometido neste slot?
            if professor_ja_alocado(grade, nome_professor, dia, horario):
                continue

            # TRAVA 3 — RN_4: ALGUMA turma do grupo já tem aula neste slot?
            conflito_turma = any(
                turma_ja_alocada_no_horario(grade, row['turma'], dia, horario)
                for _, row in grupo.iterrows()
            )
            if conflito_turma:
                continue

            for _, sala in salas.iterrows():

                # RN_7: tipo da sala compatível com o tipo da disciplina?
                if not validar_tipo_sala(turma_ref, sala):
                    continue

                # RN_10: sala comporta a SOMA de alunos de todas as turmas?
                if not validar_capacidade_grupo(grupo, sala):
                    continue

                # TRAVA 2 — RN_5: sala já está em uso neste slot?
                if sala_ja_ocupada(grade, sala['sala'], dia, horario):
                    continue

                # ✅ Todas as regras e travas passaram.
                # Aloca cada turma do grupo no mesmo professor/sala/slot.
                for _, turma_row in grupo.iterrows():
                    grade = alocar_aula(
                        grade,
                        turma_row['turma'],
                        turma_row['disciplina'],
                        nome_professor,
                        sala['sala'],
                        dia,
                        horario
                    )

                return grade, True  # Sucesso: interrompe busca para este grupo

    return grade, False  # Nenhuma combinação válida encontrada


def gerar_grade(data: dict) -> pd.DataFrame:
    """
    ALOC_03 — Motor principal completo (Greedy Expandido com turmas compartilhadas).

    Evolução em relação ao ALOC_02:
      - Agrupa turmas por disciplina+tipo antes de iterar (RN_9, RN_13).
      - Tenta alocar grupos como aula compartilhada primeiro (RF_11, RN_10).
      - Fallback individual: se o grupo não couber junto, cada turma é
        tentada separadamente para maximizar alocações (RN_8).
      - Professores ordenados por carga horária no desempate (RN_12).
      - Todas as travas de ALOC_01 e ALOC_02 continuam ativas.

    Fluxo por grupo de turmas (mesma disciplina + tipo):
        1. Tentativa compartilhada: todas as turmas do grupo juntas.
        2. Se falhar E grupo > 1: fallback individual turma a turma.
        3. Se falhar individual: reporta turma não alocada (RN_8 — melhor esforço).

    Retorna o DataFrame da grade preenchida.
    """
    grade = criar_grade_vazia()

    professores = data['professores']
    turmas      = data['turmas']
    salas       = data['salas']

    # RN_9 + RN_13: forma grupos de turmas com mesma disciplina e mesmo tipo.
    # Disciplinas com componentes teórico e laboratorial ficam em grupos distintos.
    grupos = agrupar_turmas_por_disciplina(turmas)

    for grupo in grupos:
        # ── Tentativa 1: alocação compartilhada (todo o grupo junto) ──────
        grade, alocado = _tentar_alocar_grupo(grade, grupo, professores, salas)

        if alocado:
            continue  # Grupo alocado com sucesso → próximo grupo

        # ── Tentativa 2: fallback individual (apenas para grupos > 1) ─────
        # Se as turmas não couberam juntas (capacidade ou conflito),
        # tenta alocar cada uma individualmente.
        if len(grupo) > 1:
            for _, turma_row in grupo.iterrows():
                turma_individual = pd.DataFrame([turma_row])
                grade, alocado_individual = _tentar_alocar_grupo(
                    grade, turma_individual, professores, salas
                )
                if not alocado_individual:
                    print(
                        f"⚠️  Turma '{turma_row['turma']}' ({turma_row['disciplina']}) "
                        f"não pôde ser alocada — sem combinação válida."
                    )
        else:
            turma_row = grupo.iloc[0]
            print(
                f"⚠️  Turma '{turma_row['turma']}' ({turma_row['disciplina']}) "
                f"não pôde ser alocada — sem combinação válida de "
                f"professor, sala e horário disponíveis."
            )

    return grade


def exportar_grade(
    grade: pd.DataFrame,
    caminho: str = 'csv/grade_final.csv',
) -> str | None:
    """
    RF_8, RF_11 — Exporta a grade gerada para um arquivo CSV físico.

    Comportamento:
      • Agrupa turmas compartilhadas no formato 'SI1;CC1' (RF_11).
      • Salva com encoding UTF-8 e sem a coluna de índice do DataFrame.
      • Cria automaticamente o diretório de destino se ele não existir,
        garantindo portabilidade entre Windows, Linux e macOS (RNF_2).
      • Retorna o caminho absoluto do arquivo salvo, ou None se a grade
        estiver vazia (para uso na interface visual e nos testes).

    Colunas obrigatórias na saída (Tabela de Saída do projeto):
        turma | disciplina | professor | sala | dia | horario

    Parâmetros:
        grade   → DataFrame interno gerado por gerar_grade()
        caminho → caminho relativo ou absoluto do arquivo de destino
                  (padrão: 'csv/grade_final.csv')

    Retorna:
        str  → caminho absoluto do arquivo salvo em caso de sucesso
        None → grade vazia, nenhum arquivo gerado
    """
    if grade.empty:
        print("⚠️  Grade vazia. Nenhum arquivo gerado.")
        return None

    # Cria o diretório de destino se não existir.
    # os.path.dirname retorna '' para caminhos sem barra (ex: 'grade.csv'),
    # portanto makedirs só é chamado quando existe uma pasta explícita.
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    # Agrupamento de turmas compartilhadas para a saída (RF_11).
    # Chave: disciplina + professor + sala + dia + horario.
    # Turmas do mesmo slot são unidas com ';' na coluna 'turma'.
    grade_exportacao = (
        grade
        .groupby(['disciplina', 'professor', 'sala', 'dia', 'horario'], sort=False)
        .agg(turma=('turma', lambda ids: ';'.join(ids)))
        .reset_index()
    )[['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']]

    # Salva sem índice e com encoding UTF-8 explícito para suportar
    # acentos e caracteres especiais nos nomes de professores/disciplinas.
    grade_exportacao.to_csv(caminho, index=False, encoding='utf-8')

    caminho_absoluto = os.path.abspath(caminho)
    print(f"✅ Grade exportada com sucesso em '{caminho_absoluto}'.")
    return caminho_absoluto


# =============================================================================
# MÓDULO 6 — PRÉ-VALIDAÇÃO CRUZADA DOS CSVs (Sprint S9 — PRE_01)
#
# Verifica inconsistências entre os três arquivos ANTES de rodar o motor.
# Analogia: é o "check-up médico" dos dados — melhor descobrir o problema
# antes da cirurgia do que no meio dela.
#
# Regras verificadas:
#   PRE_01-A → Turma do tipo Laboratorio sem sala Laboratorio cadastrada
#   PRE_01-B → Disciplina em turmas.csv sem professor habilitado
#   PRE_01-C → Capacidade ou número de alunos zero ou negativo
#   PRE_01-D → Professor com dia ou horário em branco (NaN)
# =============================================================================

def validar_consistencia_dados(data: dict) -> list[str]:
    """
    PRE_01 — Valida a consistência cruzada entre os três DataFrames de entrada.

    Detecta problemas estruturais que impediriam alocações válidas antes mesmo
    de o motor Greedy ser executado. Não lança exceções — apenas acumula e
    retorna avisos para exibição na interface.

    Parâmetro:
        data → dicionário com chaves 'professores', 'turmas', 'salas',
               no mesmo formato retornado por carregar_dados().

    Retorna:
        list[str] → lista de strings de aviso (vazia = dados consistentes).

    Regras verificadas:
        PRE_01-A: Turma do tipo 'Laboratorio' sem nenhuma sala 'Laboratorio'.
        PRE_01-B: Disciplina em turmas.csv sem professor habilitado.
        PRE_01-C: Coluna 'capacidade' (salas) ou 'alunos' (turmas) com valor
                  zero ou negativo — indica dado corrompido ou ausente.
        PRE_01-D: Professor com 'dia' ou 'horario' em branco (NaN).
    """
    avisos: list[str] = []

    professores = data.get('professores', pd.DataFrame())
    turmas      = data.get('turmas',      pd.DataFrame())
    salas       = data.get('salas',       pd.DataFrame())

    # ── PRE_01-A: turma de laboratório sem sala de laboratório ────────────
    # Só faz sentido verificar se ambos os DataFrames existem e não estão
    # vazios. Se não há nenhuma sala do tipo 'Laboratorio', qualquer turma
    # do tipo 'Laboratorio' nunca será alocada — aviso crítico.
    if not turmas.empty and not salas.empty:
        tem_sala_lab = (
            salas['tipo'].str.lower().str.strip() == 'laboratorio'
        ).any()

        turmas_lab = turmas[
            turmas['tipo'].str.lower().str.strip() == 'laboratorio'
        ]

        if not turmas_lab.empty and not tem_sala_lab:
            nomes = ', '.join(turmas_lab['turma'].tolist())
            avisos.append(
                f"[PRE_01-A] Turma(s) do tipo Laboratorio ({nomes}) sem "
                "nenhuma sala de Laboratorio cadastrada em salas.csv. "
                "Essas turmas não serão alocadas."
            )

    # ── PRE_01-B: disciplina sem professor habilitado ─────────────────────
    # Para cada disciplina distinta nas turmas, verifica se existe ao menos
    # uma linha em professores.csv com a mesma disciplina.
    # Se não existir, a disciplina nunca poderá ser alocada.
    if not turmas.empty and not professores.empty:
        disciplinas_turmas = set(turmas['disciplina'].dropna().unique())
        disciplinas_prof   = set(professores['disciplina'].dropna().unique())

        sem_professor = disciplinas_turmas - disciplinas_prof
        for disciplina in sorted(sem_professor):
            avisos.append(
                f"[PRE_01-B] Disciplina '{disciplina}' presente em turmas.csv "
                "não possui nenhum professor habilitado em professores.csv."
            )

    # ── PRE_01-C: capacidade ou número de alunos inválido (zero/negativo) ─
    # Valores zero ou negativos são dados corrompidos: uma sala com capacidade
    # 0 nunca aceita ninguém; uma turma com 0 alunos não faz sentido.
    if not salas.empty and 'capacidade' in salas.columns:
        salas_invalidas = salas[
            pd.to_numeric(salas['capacidade'], errors='coerce').fillna(0) <= 0
        ]
        if not salas_invalidas.empty:
            nomes = ', '.join(salas_invalidas['sala'].astype(str).tolist())
            avisos.append(
                f"[PRE_01-C] Sala(s) com capacidade zero ou negativa: {nomes}. "
                "Verifique os valores na coluna 'capacidade' de salas.csv."
            )

    if not turmas.empty and 'alunos' in turmas.columns:
        turmas_invalidas = turmas[
            pd.to_numeric(turmas['alunos'], errors='coerce').fillna(0) <= 0
        ]
        if not turmas_invalidas.empty:
            nomes = ', '.join(turmas_invalidas['turma'].astype(str).tolist())
            avisos.append(
                f"[PRE_01-C] Turma(s) com número de alunos zero ou negativo: "
                f"{nomes}. Verifique a coluna 'alunos' de turmas.csv."
            )

    # ── PRE_01-D: professor com dia ou horário em branco ──────────────────
    # Linha com NaN em 'dia' ou 'horario' nunca passa na validar_disponibilidade,
    # então o slot é desperdiçado silenciosamente — melhor avisar antes.
    if not professores.empty:
        dia_nan     = professores['dia'].isna()
        horario_nan = professores['horario'].isna()
        profs_invalidos = professores[dia_nan | horario_nan]

        if not profs_invalidos.empty:
            nomes = ', '.join(profs_invalidos['nome'].astype(str).unique())
            avisos.append(
                f"[PRE_01-D] Professor(es) com dia ou horário em branco: "
                f"{nomes}. Esses slots de disponibilidade serão ignorados "
                "pelo motor de alocação."
            )

    return avisos


# =============================================================================
# MÓDULO 7 — RELATÓRIO DE FALHAS (Sprint S9 — REL_01)
#
# Gera um CSV separado com o motivo provável de cada turma não alocada.
# Analogia: é o "laudo do diagnóstico" — não basta saber que o paciente
# não passou; o médico precisa saber POR QUÊ para prescrever a correção.
# =============================================================================

def _normalizar_tipo_sala(tipo: str) -> str:
    """
    REL_01 — Normaliza o tipo de sala para comparação consistente.

    O CSV de salas aceita 'Sala' e 'Teorica' como sinônimos para
    ambientes teóricos (conforme validar_tipo_sala usa .lower()).
    Internamente o motor compara turma['tipo'].lower() == sala['tipo'].lower(),
    então 'Teorica' casa com 'Teorica', mas 'Sala' não casa com 'Teorica'.

    Para o diagnóstico de falha, qualquer tipo que NÃO seja 'laboratorio'
    é tratado como teórico, espelhando a mesma lógica do motor.
    """
    normalizado = tipo.strip().lower()
    if normalizado == 'laboratorio':
        return 'laboratorio'
    # 'sala', 'teorica' e qualquer outro valor → teórico
    return normalizado


def _inferir_motivo_falha(
    turma_row: pd.Series,
    professores: pd.DataFrame,
    salas: pd.DataFrame
) -> str:
    """
    REL_01 — Infere o motivo mais provável pelo qual uma turma não foi alocada.

    Hierarquia de diagnóstico (da causa mais restritiva à menos):
        1. Nenhum professor habilitado para a disciplina.
        2. Nenhuma sala do tipo correto disponível.
        3. Nenhuma sala do tipo correto com capacidade suficiente.
        4. Conflito de horário: recursos existem mas todos os slots estavam
           ocupados por alocações de outras turmas.

    O diagnóstico é estático — analisa os CSVs de entrada, não simula a
    grade em tempo real. Por isso o campo chama-se 'motivo_provavel'.

    Retorna string descritiva do motivo.
    """
    disciplina = turma_row['disciplina']
    tipo_turma = _normalizar_tipo_sala(str(turma_row.get('tipo', '')))
    alunos     = turma_row.get('alunos', 0)

    # Diagnóstico 1: existe professor habilitado para essa disciplina?
    prof_habilitados = professores[
        professores['disciplina'] == disciplina
    ]
    if prof_habilitados.empty:
        return "Nenhum professor habilitado para esta disciplina"

    # Diagnóstico 2: existe sala do tipo correto?
    # Compara usando a mesma normalização do motor (lower + strip).
    salas_tipo = salas[
        salas['tipo'].str.lower().str.strip() == tipo_turma
    ]
    if salas_tipo.empty:
        tipo_legivel = tipo_turma.capitalize()
        return f"Nenhuma sala do tipo {tipo_legivel} cadastrada"

    # Diagnóstico 3: existe sala do tipo correto com capacidade suficiente?
    salas_com_capacidade = salas_tipo[
        pd.to_numeric(salas_tipo['capacidade'], errors='coerce').fillna(0)
        >= alunos
    ]
    if salas_com_capacidade.empty:
        tipo_legivel = tipo_turma.capitalize()
        return (
            f"Nenhuma sala do tipo {tipo_legivel} com capacidade "
            f"suficiente para {int(alunos)} aluno(s)"
        )

    # Diagnóstico 4: todos os recursos existem mas algo impediu a alocação
    # (provavelmente conflito de horário com outras turmas já alocadas).
    return (
        "Conflito de horário: todos os slots do professor ou da sala "
        "estavam ocupados por outras alocações"
    )


def gerar_relatorio_falhas(
    turmas_df: pd.DataFrame,
    grade: pd.DataFrame,
    professores: pd.DataFrame = None,
    salas: pd.DataFrame = None,
    caminho: str = 'csv/falhas_alocacao.csv',
) -> pd.DataFrame:
    """
    REL_01 — Gera relatório das turmas que não puderam ser alocadas.

    Cruza o DataFrame original de turmas com a grade gerada e, para cada
    turma ausente, infere o motivo provável da falha com base nos CSVs.

    O relatório só é salvo em disco se houver ao menos uma falha (evita
    criar arquivo vazio enganoso). Usa UTF-8 e index=False, igual ao
    exportar_grade().

    Parâmetros:
        turmas_df    → DataFrame original de turmas.csv
        grade        → DataFrame da grade gerada por gerar_grade()
        professores  → DataFrame de professores.csv (opcional; usado para
                       inferir motivo mais preciso)
        salas        → DataFrame de salas.csv (opcional; idem)
        caminho      → destino do CSV de saída
                       (padrão: 'csv/falhas_alocacao.csv')

    Retorna:
        pd.DataFrame com colunas:
            turma | disciplina | alunos | tipo | motivo_provavel
        DataFrame vazio se todas as turmas foram alocadas.
    """
    # Identifica turmas ausentes na grade
    alocadas = set(grade['turma'].unique()) if not grade.empty else set()
    nao_alocadas = turmas_df[
        ~turmas_df['turma'].isin(alocadas)
    ].reset_index(drop=True)

    if nao_alocadas.empty:
        return pd.DataFrame(
            columns=['turma', 'disciplina', 'alunos', 'tipo', 'motivo_provavel']
        )

    # DataFrames vazios como fallback quando não fornecidos
    df_prof  = professores if professores is not None else pd.DataFrame(
        columns=['nome', 'disciplina', 'dia', 'horario']
    )
    df_salas = salas if salas is not None else pd.DataFrame(
        columns=['sala', 'capacidade', 'tipo']
    )

    # Infere o motivo de cada turma não alocada
    motivos = [
        _inferir_motivo_falha(row, df_prof, df_salas)
        for _, row in nao_alocadas.iterrows()
    ]

    relatorio = nao_alocadas[['turma', 'disciplina', 'alunos', 'tipo']].copy()
    relatorio['motivo_provavel'] = motivos

    # Salva em disco somente se houver falhas
    diretorio = os.path.dirname(caminho)
    if diretorio:
        os.makedirs(diretorio, exist_ok=True)

    relatorio.to_csv(caminho, index=False, encoding='utf-8')
    caminho_absoluto = os.path.abspath(caminho)
    print(f"📋 Relatório de falhas exportado em '{caminho_absoluto}'.")

    return relatorio