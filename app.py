"""
INT_01 + INT_02 — Dashboard de Upload e Visualizador Dinâmico da Grade
Sprint S8 | Faculdade Impacta — Engenharia de Software | SI NOITE 2A

Responsabilidade deste arquivo:
    Apenas interface visual (upload, validação de entrada, exibição de resultados).
    Toda a lógica de alocação permanece em projeto.py (separação de conceitos).

Execução:
    streamlit run app.py
"""

import io
import contextlib

import pandas as pd
import streamlit as st

from projeto import gerar_grade

# =============================================================================
# CONSTANTES
# =============================================================================

COLUNAS_OBRIGATORIAS: dict[str, list[str]] = {
    'professores': ['matricula', 'nome', 'disciplina', 'dia', 'horario'],
    'turmas':      ['turma', 'alunos', 'disciplina', 'tipo'],
    'salas':       ['sala', 'capacidade', 'tipo'],
}

# Ordem canônica dos dias para exibição na grade visual
ORDEM_DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']

# Paleta de cores (fundo pastel, borda accent) para os cartões de aula.
# Cada professor recebe um par de cores exclusivo (ciclado se necessário).
PALETA_CORES: list[tuple[str, str]] = [
    ('#DBEAFE', '#2563EB'),  # azul
    ('#D1FAE5', '#059669'),  # verde
    ('#FEF3C7', '#D97706'),  # âmbar
    ('#FCE7F3', '#DB2777'),  # rosa
    ('#EDE9FE', '#7C3AED'),  # violeta
    ('#FFEDD5', '#EA580C'),  # laranja
    ('#CFFAFE', '#0891B2'),  # ciano
    ('#DCFCE7', '#16A34A'),  # esmeralda
    ('#FEE2E2', '#DC2626'),  # vermelho
    ('#F3F4F6', '#374151'),  # cinza
]


# =============================================================================
# MÓDULO 1 — FUNÇÕES DE VALIDAÇÃO E LEITURA DE UPLOAD (INT_01)
# Testáveis independentemente da UI (ver testes/teste_interface.py).
# =============================================================================

def validar_colunas(df: pd.DataFrame, chave: str) -> list[str]:
    """
    Verifica se todas as colunas obrigatórias do arquivo 'chave' existem no
    DataFrame. Retorna lista com os nomes das colunas ausentes (lista vazia = OK).
    """
    return [c for c in COLUNAS_OBRIGATORIAS[chave] if c not in df.columns]


def ler_csv_upload(arquivo, chave: str) -> tuple:
    """
    Lê e valida um arquivo CSV do file_uploader do Streamlit.
    Verifica: leitura válida, arquivo não vazio, colunas obrigatórias presentes
    e tipos numéricos corretos (capacidade / alunos).

    Retorna: (pd.DataFrame, None) em sucesso | (None, str_erro) em falha.
    """
    try:
        df = pd.read_csv(arquivo)
    except Exception as e:
        return None, f"Não foi possível ler o arquivo. Verifique se é um CSV válido. Detalhe: {e}"

    if df.empty:
        return None, "O arquivo está vazio. Adicione pelo menos uma linha de dados."

    ausentes = validar_colunas(df, chave)
    if ausentes:
        return None, (
            f"Colunas obrigatórias ausentes: **{', '.join(ausentes)}**. "
            "Verifique se o arquivo está no formato correto."
        )

    if chave == 'salas':
        df['capacidade'] = pd.to_numeric(df['capacidade'], errors='coerce')
        inv = int(df['capacidade'].isna().sum())
        if inv > 0:
            return None, (
                f"{inv} valor(es) inválido(s) na coluna **capacidade**. "
                "Certifique-se de que são números inteiros."
            )

    if chave == 'turmas':
        df['alunos'] = pd.to_numeric(df['alunos'], errors='coerce')
        inv = int(df['alunos'].isna().sum())
        if inv > 0:
            return None, (
                f"{inv} valor(es) inválido(s) na coluna **alunos**. "
                "Certifique-se de que são números inteiros."
            )

    return df, None


def converter_grade_para_bytes(grade: pd.DataFrame) -> bytes:
    """
    Converte o DataFrame da grade para bytes CSV (sem gravar em disco),
    agrupando turmas compartilhadas no formato 'SI1;CC1' (RF_11).
    """
    exportacao = (
        grade
        .groupby(['disciplina', 'professor', 'sala', 'dia', 'horario'], sort=False)
        .agg(turma=('turma', lambda ids: ';'.join(ids)))
        .reset_index()
    )[['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']]
    buf = io.StringIO()
    exportacao.to_csv(buf, index=False)
    return buf.getvalue().encode('utf-8')


def capturar_avisos_grade(data: dict) -> tuple:
    """
    Executa gerar_grade() capturando os prints de turmas não alocadas que iriam
    para o terminal, devolvendo-os como string para a UI.

    Retorna: (pd.DataFrame, str_avisos)
    """
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        grade = gerar_grade(data)
    return grade, buf.getvalue().strip()


# =============================================================================
# MÓDULO 2 — FUNÇÕES DO VISUALIZADOR DINÂMICO (INT_02)
# Testáveis independentemente da UI (ver testes/teste_visualizador.py).
# =============================================================================

def mapear_cores_professores(grade: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """
    Associa cada professor único da grade a um par de cores (fundo, borda)
    da PALETA_CORES. Se houver mais professores que cores na paleta, ela
    é ciclada (operador módulo). Retorna um dicionário {nome: (fundo, borda)}.
    """
    professores = grade['professor'].dropna().unique()
    return {
        prof: PALETA_CORES[i % len(PALETA_CORES)]
        for i, prof in enumerate(professores)
    }


def agregar_turmas_compartilhadas(grade: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega linhas do DataFrame interno (uma linha por turma) em linhas de exibição
    onde múltiplas turmas no mesmo slot aparecem como 'SI1;CC1' (RF_11).
    Retorna um DataFrame com colunas: turma, disciplina, professor, sala, dia, horario.
    """
    if grade.empty:
        return grade.copy()
    return (
        grade
        .groupby(['disciplina', 'professor', 'sala', 'dia', 'horario'], sort=False)
        .agg(turma=('turma', lambda ids: ';'.join(ids)))
        .reset_index()
    )[['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']]


def obter_turmas_nao_alocadas(
    turmas_df: pd.DataFrame,
    grade: pd.DataFrame
) -> pd.DataFrame:
    """
    Cruza o DataFrame original de turmas com a grade gerada para identificar
    quais turmas não foram alocadas pelo motor (escassez de recursos).

    Retorna um DataFrame com as turmas ausentes na grade, contendo as colunas
    originais do turmas.csv para exibição dos detalhes da falha.
    """
    if turmas_df.empty:
        return pd.DataFrame()
    alocadas = set(grade['turma'].unique()) if not grade.empty else set()
    return turmas_df[~turmas_df['turma'].isin(alocadas)].reset_index(drop=True)


def construir_html_grade(
    grade: pd.DataFrame,
    cores: dict[str, tuple[str, str]],
    filtro_coluna: str | None = None,
    filtro_valor: str | None = None,
) -> str:
    """
    Constrói uma tabela HTML estilizada com horários nas linhas e dias nas colunas.
    Cada célula exibe um cartão colorido por professor com turma, disciplina e sala.

    Parâmetros:
        grade          → DataFrame interno (uma linha por turma)
        cores          → dicionário {professor: (cor_fundo, cor_borda)}
        filtro_coluna  → coluna para filtrar (ex: 'professor' ou 'turma')
        filtro_valor   → valor do filtro

    Retorna a string HTML pronta para st.markdown(unsafe_allow_html=True).
    """
    if grade.empty:
        return '<p style="color:#9CA3AF;padding:24px;text-align:center;">Nenhuma alocação para exibir.</p>'

    # Aplica filtro opcional antes de agregar
    df = grade.copy()
    if filtro_coluna and filtro_valor:
        df = df[df[filtro_coluna] == filtro_valor]

    df_agg = agregar_turmas_compartilhadas(df)

    if df_agg.empty:
        return '<p style="color:#9CA3AF;padding:24px;text-align:center;">Nenhuma alocação para este filtro.</p>'

    # Usa apenas os dias que aparecem na grade, na ordem canônica
    dias = [d for d in ORDEM_DIAS if d in df_agg['dia'].values]
    if not dias:
        dias = sorted(df_agg['dia'].unique())

    horarios = sorted(df_agg['horario'].unique())

    # ── Estilos CSS embutidos ──────────────────────────────────────────────
    css = """
    <style>
      .grade-wrap { overflow-x: auto; margin-top: 8px; }
      .grade-tbl  { border-collapse: collapse; width: 100%; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
      .grade-tbl th {
        background: #1E293B; color: #F8FAFC; padding: 10px 14px;
        text-align: center; white-space: nowrap; font-weight: 600;
        border: 1px solid #334155; position: sticky; top: 0;
      }
      .grade-tbl td {
        border: 1px solid #E2E8F0; padding: 6px; vertical-align: top;
        min-width: 140px; background: #FAFAFA;
      }
      .hora-cel {
        background: #F1F5F9 !important; color: #475569;
        font-weight: 700; font-size: 12px; text-align: center;
        white-space: nowrap; min-width: 60px;
      }
      .vazio { color: #CBD5E1; text-align: center; font-size: 18px; padding: 12px; }
      .aula-card {
        padding: 7px 9px; border-radius: 6px; margin: 2px 0;
        border-left: 4px solid;
      }
      .aula-turma  { font-weight: 700; font-size: 13px; letter-spacing: 0.3px; }
      .aula-disc   { font-size: 11px; color: #374151; margin-top: 2px; }
      .aula-info   { font-size: 11px; color: #6B7280; margin-top: 3px; }
    </style>
    """

    # ── Cabeçalho da tabela ────────────────────────────────────────────────
    cabecalho = '<tr><th class="hora-cel">⏰ Horário</th>'
    for dia in dias:
        cabecalho += f'<th>{dia}</th>'
    cabecalho += '</tr>'

    # ── Linhas de dados ────────────────────────────────────────────────────
    linhas_html = ''
    for horario in horarios:
        linha = f'<tr><td class="hora-cel">{horario}</td>'
        for dia in dias:
            celula = df_agg[(df_agg['dia'] == dia) & (df_agg['horario'] == horario)]
            if celula.empty:
                linha += '<td><div class="vazio">—</div></td>'
            else:
                conteudo = ''
                for _, aula in celula.iterrows():
                    fundo, borda = cores.get(aula['professor'], ('#F3F4F6', '#6B7280'))
                    conteudo += f"""
                    <div class="aula-card" style="background:{fundo};border-left-color:{borda};">
                      <div class="aula-turma">{aula['turma']}</div>
                      <div class="aula-disc">{aula['disciplina']}</div>
                      <div class="aula-info">👤 {aula['professor']}</div>
                      <div class="aula-info">🏫 {aula['sala']}</div>
                    </div>"""
                linha += f'<td>{conteudo}</td>'
        linha += '</tr>'
        linhas_html += linha

    html = f"""
    {css}
    <div class="grade-wrap">
      <table class="grade-tbl">
        <thead>{cabecalho}</thead>
        <tbody>{linhas_html}</tbody>
      </table>
    </div>"""
    return html


def construir_html_legenda(cores: dict[str, tuple[str, str]]) -> str:
    """
    Gera uma legenda HTML com um chip colorido para cada professor,
    exibida abaixo da grade visual para facilitar a leitura das cores.
    """
    if not cores:
        return ''
    chips = ''.join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'background:{fundo};border:1.5px solid {borda};'
        f'border-radius:20px;padding:3px 10px;margin:3px;font-size:12px;">'
        f'<span style="width:10px;height:10px;background:{borda};border-radius:50%;display:inline-block;"></span>'
        f'{prof}</span>'
        for prof, (fundo, borda) in cores.items()
    )
    return f'<div style="margin-top:10px;line-height:2;">{chips}</div>'


def construir_html_alertas(nao_alocadas: pd.DataFrame) -> str:
    """
    Gera cartões HTML de alerta para cada turma que não pôde ser alocada
    (Teste 10 — escassez de salas; Teste 12 — tipo de sala indisponível).
    Exibe turma, disciplina, número de alunos e tipo, além de uma dica de ação.
    """
    if nao_alocadas.empty:
        return ''

    cards = ''
    for _, row in nao_alocadas.iterrows():
        tipo_icone = '🔬' if str(row.get('tipo', '')).lower() == 'laboratorio' else '📚'
        dica = (
            'Verifique se há laboratório disponível nos CSVs.'
            if str(row.get('tipo', '')).lower() == 'laboratorio'
            else 'Verifique se há professor habilitado e sala com capacidade suficiente.'
        )
        cards += f"""
        <div style="background:#FFF7ED;border:1px solid #FED7AA;border-left:5px solid #F97316;
                    border-radius:8px;padding:12px 16px;margin:6px 0;">
          <div style="font-weight:700;font-size:14px;color:#C2410C;">
            {tipo_icone} {row['turma']} — {row['disciplina']}
          </div>
          <div style="font-size:12px;color:#78350F;margin-top:4px;">
            👥 {row['alunos']} alunos &nbsp;|&nbsp; Tipo: {row['tipo']}
          </div>
          <div style="font-size:11px;color:#92400E;margin-top:6px;">
            💡 {dica}
          </div>
        </div>"""
    return cards


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Grade de Horários — Impacta",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .cabecalho-titulo { font-size:2rem; font-weight:700; letter-spacing:-0.5px; }
  .aviso-turma {
    background:#FFF3E0; border-left:4px solid #F57C00;
    padding:0.4rem 0.8rem; border-radius:4px; margin:0.3rem 0; font-size:0.9rem;
  }
  /* Remove margem extra do st.tabs */
  div[data-testid="stTabs"] { margin-top: 0 !important; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CABEÇALHO
# =============================================================================

_, col_titulo = st.columns([1, 8])
with col_titulo:
    st.markdown(
        '<p class="cabecalho-titulo">🗓️ Sistema de Coordenação de Horários</p>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Faculdade Impacta · Engenharia de Software · SI NOITE 2A  |  "
        "Beatriz Carvalho Santos · Larissa da Silva Maschio · Mariana Braga Sevarolli"
    )

st.divider()


# =============================================================================
# PASSO 1 — UPLOAD DOS ARQUIVOS CSV (INT_01)
# =============================================================================

st.subheader("Passo 1 — Upload dos arquivos CSV")
st.caption(
    "Envie os três arquivos obrigatórios. O sistema valida o formato "
    "automaticamente e exibe os erros antes de processar."
)

col_prof, col_turmas, col_salas = st.columns(3)

with col_prof:
    st.markdown("**📋 professores.csv**")
    st.caption("`matricula · nome · disciplina · dia · horario`")
    upload_prof = st.file_uploader(
        "Selecione professores.csv", type="csv", key="up_prof",
        label_visibility="collapsed",
    )

with col_turmas:
    st.markdown("**👥 turmas.csv**")
    st.caption("`turma · alunos · disciplina · tipo`")
    upload_turmas = st.file_uploader(
        "Selecione turmas.csv", type="csv", key="up_turmas",
        label_visibility="collapsed",
    )

with col_salas:
    st.markdown("**🏫 salas.csv**")
    st.caption("`sala · capacidade · tipo`")
    upload_salas = st.file_uploader(
        "Selecione salas.csv", type="csv", key="up_salas",
        label_visibility="collapsed",
    )


# ── Validação e acumulação dos DataFrames válidos ──────────────────────────

dados_validos: dict[str, pd.DataFrame] = {}


def _processar_upload(arquivo, chave: str, container):
    """Lê, valida e exibe status inline no container. Retorna df ou None."""
    if arquivo is None:
        return None
    df, erro = ler_csv_upload(arquivo, chave)
    if erro:
        container.error(f"❌ **Erro em `{arquivo.name}`:** {erro}")
        return None
    container.success(f"✅ `{arquivo.name}` — {len(df)} linha(s).")
    return df


df_prof   = _processar_upload(upload_prof,   'professores', col_prof)
df_turmas = _processar_upload(upload_turmas, 'turmas',      col_turmas)
df_salas  = _processar_upload(upload_salas,  'salas',       col_salas)

todos_validos = all(df is not None for df in [df_prof, df_turmas, df_salas])

if df_prof   is not None: dados_validos['professores'] = df_prof
if df_turmas is not None: dados_validos['turmas']      = df_turmas
if df_salas  is not None: dados_validos['salas']       = df_salas


# =============================================================================
# PASSO 2 — PRÉVIA DOS DADOS (INT_01)
# =============================================================================

if dados_validos:
    st.divider()
    st.subheader("Passo 2 — Prévia dos dados carregados")
    nomes = [k for k in ['professores', 'turmas', 'salas'] if k in dados_validos]
    abas  = st.tabs([f"📄 {n}.csv" for n in nomes])
    for aba, nome in zip(abas, nomes):
        with aba:
            st.dataframe(dados_validos[nome], use_container_width=True, height=200)
            st.caption(
                f"{len(dados_validos[nome])} linha(s) · "
                f"{len(dados_validos[nome].columns)} coluna(s)"
            )


# =============================================================================
# PASSO 3 — GERAÇÃO DA GRADE (INT_01)
# =============================================================================

st.divider()
st.subheader("Passo 3 — Gerar a Grade de Horários")

if not todos_validos:
    faltando = sum(u is None for u in [upload_prof, upload_turmas, upload_salas])
    st.info(f"⏳ Aguardando **{faltando}** arquivo(s) para liberar a geração.")

btn_gerar = st.button(
    "🚀 Gerar Grade de Horários",
    disabled=not todos_validos,
    type="primary",
    use_container_width=True,
)

if btn_gerar and todos_validos:
    with st.spinner("Processando alocações..."):
        grade, avisos = capturar_avisos_grade(dados_validos)
    st.session_state['grade']  = grade
    st.session_state['avisos'] = avisos


# =============================================================================
# PASSO 4 — VISUALIZADOR DINÂMICO DA GRADE (INT_02)
#
# Exibe a grade em três perspectivas via abas:
#   📊 Grade Visual   → tabela HTML (dias × horários) com cartões coloridos
#   👤 Por Professor  → mesma tabela filtrada por um professor selecionado
#   👥 Por Turma      → lista detalhada das aulas de uma turma selecionada
#
# Alertas visuais identificam turmas sem alocação (escassez de recursos).
# =============================================================================

if 'grade' in st.session_state:
    grade: pd.DataFrame = st.session_state['grade']
    avisos: str         = st.session_state.get('avisos', '')

    st.divider()
    st.subheader("Passo 4 — Visualizador da Grade")

    # ── Métricas de resumo ────────────────────────────────────────────────
    total_csv   = len(dados_validos.get('turmas', pd.DataFrame()))
    total_aloc  = grade['turma'].nunique() if not grade.empty else 0
    total_nao   = total_csv - total_aloc

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Turmas no CSV",       total_csv)
    m2.metric("Turmas alocadas",     total_aloc,
              delta=f"+{total_aloc}" if total_aloc else None)
    m3.metric("Sem alocação",        total_nao,
              delta=f"-{total_nao}" if total_nao > 0 else None,
              delta_color="inverse")
    m4.metric("Professores usados",
              grade['professor'].nunique() if not grade.empty else 0)

    # ── Alertas de escassez (Teste 10 e 12) ──────────────────────────────
    # Cruza o CSV original de turmas com a grade para identificar as turmas
    # ausentes e exibe um cartão laranja por cada uma delas.
    turmas_df = dados_validos.get('turmas', pd.DataFrame())
    nao_alocadas = obter_turmas_nao_alocadas(turmas_df, grade)

    if not nao_alocadas.empty:
        with st.expander(
            f"⚠️ {len(nao_alocadas)} turma(s) não alocada(s) — "
            "escassez de recursos (clique para detalhar)",
            expanded=True,
        ):
            html_alertas = construir_html_alertas(nao_alocadas)
            st.markdown(html_alertas, unsafe_allow_html=True)
            st.caption(
                "Revise os CSVs: certifique-se de que há professor habilitado, "
                "sala do tipo correto e horário disponível para essas turmas."
            )

    # ── Aviso genérico de grade vazia ─────────────────────────────────────
    if grade.empty:
        st.warning(
            "Nenhuma aula pôde ser alocada. "
            "Revise os dados dos CSVs e tente novamente."
        )
    else:
        # Pré-calcula o mapeamento de cores (professor → par de cores)
        cores = mapear_cores_professores(grade)

        # ── Abas de visualização ──────────────────────────────────────────
        aba_visual, aba_prof, aba_turma = st.tabs([
            "📊 Grade Visual",
            "👤 Por Professor",
            "👥 Por Turma",
        ])

        # ════════════════════════════════════════════════════════════════
        # ABA 1 — GRADE VISUAL COMPLETA
        # Renderiza a tabela HTML (horários × dias) com todos os cartões.
        # Abaixo da tabela, exibe a legenda de cores por professor.
        # ════════════════════════════════════════════════════════════════
        with aba_visual:
            st.caption(
                "Visão completa da grade. "
                "Cada cartão representa uma aula alocada."
            )
            html_grade = construir_html_grade(grade, cores)
            st.markdown(html_grade, unsafe_allow_html=True)

            # Legenda: um chip colorido por professor
            st.markdown("**Legenda de professores:**")
            st.markdown(construir_html_legenda(cores), unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════
        # ABA 2 — FILTRO POR PROFESSOR
        # Selectbox lista apenas os professores presentes na grade.
        # A tabela HTML é regeada filtrando apenas as linhas do professor.
        # ════════════════════════════════════════════════════════════════
        with aba_prof:
            professores_grade = sorted(grade['professor'].unique())
            prof_sel = st.selectbox(
                "Selecione o professor:",
                options=professores_grade,
                key="sel_prof",
            )

            if prof_sel:
                # Quantidade de aulas alocadas para feedback rápido
                qtd_aulas = len(grade[grade['professor'] == prof_sel])
                st.caption(f"👤 **{prof_sel}** — {qtd_aulas} aula(s) alocada(s) na grade.")

                # Tabela HTML filtrada pelo professor selecionado
                html_prof = construir_html_grade(
                    grade, cores,
                    filtro_coluna='professor',
                    filtro_valor=prof_sel,
                )
                st.markdown(html_prof, unsafe_allow_html=True)

        # ════════════════════════════════════════════════════════════════
        # ABA 3 — FILTRO POR TURMA
        # Selectbox lista as turmas alocadas. Exibe uma tabela detalhada
        # (sem o pivot de horários) mostrando cada aula da turma.
        # ════════════════════════════════════════════════════════════════
        with aba_turma:
            # Lista de turmas únicas alocadas (pode ter "SI1;CC1" após agregação)
            grade_agg = agregar_turmas_compartilhadas(grade)
            # Explode turmas compartilhadas para o selectbox mostrar "SI1" e "CC1"
            turmas_lista = sorted({
                t.strip()
                for entrada in grade['turma'].unique()
                for t in entrada.split(';')
            })
            turma_sel = st.selectbox(
                "Selecione a turma:",
                options=turmas_lista,
                key="sel_turma",
            )

            if turma_sel:
                # Filtra linhas onde a turma aparece (mesmo em entradas compartilhadas)
                linhas_turma = grade[grade['turma'].str.contains(
                    rf'\b{turma_sel}\b', regex=True
                )].copy()

                st.caption(
                    f"👥 **Turma {turma_sel}** — "
                    f"{len(linhas_turma)} aula(s) alocada(s)."
                )

                if not linhas_turma.empty:
                    # Exibe tabela interativa das aulas da turma
                    st.dataframe(
                        linhas_turma[['disciplina', 'professor', 'sala', 'dia', 'horario']]
                        .sort_values(['dia', 'horario'])
                        .reset_index(drop=True),
                        use_container_width=True,
                        height=min(300, 60 + len(linhas_turma) * 38),
                    )
                    # Tabela visual da turma (grade dos horários dela)
                    html_turma = construir_html_grade(
                        grade, cores,
                        filtro_coluna='turma',
                        filtro_valor=turma_sel,
                    )
                    st.markdown(html_turma, unsafe_allow_html=True)

        # ── Download do CSV final ─────────────────────────────────────────
        st.divider()
        st.download_button(
            label="⬇️ Baixar grade_final.csv",
            data=converter_grade_para_bytes(grade),
            file_name="grade_final.csv",
            mime="text/csv",
            use_container_width=True,
        )


# =============================================================================
# RODAPÉ
# =============================================================================

st.divider()
st.caption(
    "Grade de Horários · Faculdade Impacta · 2025 · "
    "Python + Pandas + Streamlit"
)