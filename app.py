"""
INT_01 — Dashboard de Upload e Geração da Grade de Horários
Sprint S8 | Faculdade Impacta — Engenharia de Software | SI NOITE 2A

Responsabilidade deste arquivo:
    Apenas interface visual (upload, validação de entrada, exibição de resultados).
    Toda a lógica de alocação permanece em projeto.py (separação de conceitos).

Execução:
    streamlit run app.py
"""

import io
import contextlib
import tempfile
import os

import pandas as pd
import streamlit as st

# Importa apenas as funções necessárias de projeto.py.
# A lógica de negócio NÃO é replicada aqui.
from projeto import gerar_grade, exportar_grade

# =============================================================================
# CONSTANTES — Colunas obrigatórias por arquivo CSV (usadas na validação)
# =============================================================================

COLUNAS_OBRIGATORIAS: dict[str, list[str]] = {
    'professores': ['matricula', 'nome', 'disciplina', 'dia', 'horario'],
    'turmas':      ['turma', 'alunos', 'disciplina', 'tipo'],
    'salas':       ['sala', 'capacidade', 'tipo'],
}


# =============================================================================
# FUNÇÕES AUXILIARES DE VALIDAÇÃO E CONVERSÃO
# Separadas da UI para facilitar testes unitários (testes/teste_interface.py).
# =============================================================================

def validar_colunas(df: pd.DataFrame, chave: str) -> list[str]:
    """
    Verifica se todas as colunas obrigatórias do arquivo 'chave' estão presentes
    no DataFrame. Retorna uma lista com os nomes das colunas ausentes (lista
    vazia significa que o DataFrame está correto).
    """
    esperadas = COLUNAS_OBRIGATORIAS[chave]
    return [col for col in esperadas if col not in df.columns]


def ler_csv_upload(arquivo, chave: str) -> tuple:
    """
    Lê um arquivo CSV enviado pelo usuário via st.file_uploader e valida:
      1. Leitura do conteúdo (detecta arquivos corrompidos ou não-CSV).
      2. Ausência de colunas obrigatórias.
      3. Arquivo completamente vazio.
      4. Valores inválidos nas colunas numéricas (capacidade, alunos).

    Retorna:
        (pd.DataFrame, None)  → sucesso
        (None, str)           → falha, com mensagem de erro amigável
    """
    try:
        df = pd.read_csv(arquivo)
    except Exception as e:
        return None, f"Não foi possível ler o arquivo. Verifique se é um CSV válido. Detalhe: {e}"

    if df.empty:
        return None, "O arquivo está vazio. Adicione pelo menos uma linha de dados."

    colunas_ausentes = validar_colunas(df, chave)
    if colunas_ausentes:
        return None, (
            f"Colunas obrigatórias ausentes: **{', '.join(colunas_ausentes)}**. "
            f"Verifique se o arquivo está no formato correto."
        )

    # Converte colunas numéricas e reporta valores inválidos
    if chave == 'salas':
        df['capacidade'] = pd.to_numeric(df['capacidade'], errors='coerce')
        invalidos = df['capacidade'].isna().sum()
        if invalidos > 0:
            return None, (
                f"{invalidos} valor(es) inválido(s) encontrado(s) na coluna "
                f"**capacidade**. Certifique-se de que são números inteiros."
            )

    if chave == 'turmas':
        df['alunos'] = pd.to_numeric(df['alunos'], errors='coerce')
        invalidos = df['alunos'].isna().sum()
        if invalidos > 0:
            return None, (
                f"{invalidos} valor(es) inválido(s) encontrado(s) na coluna "
                f"**alunos**. Certifique-se de que são números inteiros."
            )

    return df, None


def converter_grade_para_bytes(grade: pd.DataFrame) -> bytes:
    """
    Converte o DataFrame da grade para bytes CSV prontos para download,
    sem precisar gravar nenhum arquivo em disco.
    Agrupa turmas compartilhadas no formato 'SI1;CC1' (RF_11).
    """
    grade_exportacao = (
        grade
        .groupby(['disciplina', 'professor', 'sala', 'dia', 'horario'], sort=False)
        .agg(turma=('turma', lambda ids: ';'.join(ids)))
        .reset_index()
    )[['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']]

    buffer = io.StringIO()
    grade_exportacao.to_csv(buffer, index=False)
    return buffer.getvalue().encode('utf-8')


def capturar_avisos_grade(data: dict) -> tuple:
    """
    Executa gerar_grade() e captura os avisos de turmas não alocadas
    que seriam impressos no terminal, devolvendo-os como string para
    exibição na interface.

    Retorna: (pd.DataFrame, str) → (grade gerada, avisos capturados)
    """
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        grade = gerar_grade(data)
    avisos = buffer.getvalue().strip()
    return grade, avisos


# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================

st.set_page_config(
    page_title="Grade de Horários — Impacta",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS personalizado: ajustes visuais sem comprometer a legibilidade
st.markdown("""
<style>
    /* Cabeçalho principal */
    .cabecalho-titulo {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    /* Cards de status de upload */
    .status-ok   { color: #2e7d32; font-weight: 600; }
    .status-erro { color: #c62828; font-weight: 600; }
    /* Destaque nos avisos de turma não alocada */
    .aviso-turma {
        background: #fff3e0;
        border-left: 4px solid #f57c00;
        padding: 0.4rem 0.8rem;
        border-radius: 4px;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CABEÇALHO
# =============================================================================

col_logo, col_titulo = st.columns([1, 8])
with col_titulo:
    st.markdown(
        '<p class="cabecalho-titulo">🗓️ Sistema de Coordenação de Horários</p>',
        unsafe_allow_html=True
    )
    st.caption(
        "Faculdade Impacta · Engenharia de Software · SI NOITE 2A  |  "
        "Beatriz Carvalho Santos · Larissa da Silva Maschio · Mariana Braga Sevarolli"
    )

st.divider()


# =============================================================================
# PASSO 1 — UPLOAD DOS ARQUIVOS CSV
# Três colunas lado a lado, uma para cada arquivo obrigatório.
# =============================================================================

st.subheader("Passo 1 — Upload dos arquivos CSV")
st.caption(
    "Envie os três arquivos obrigatórios. O sistema valida automaticamente "
    "o formato e exibe os erros antes de processar."
)

col_prof, col_turmas, col_salas = st.columns(3)

with col_prof:
    st.markdown("**📋 professores.csv**")
    st.caption("`matricula · nome · disciplina · dia · horario`")
    upload_prof = st.file_uploader(
        "Selecione professores.csv", type="csv", key="up_prof",
        label_visibility="collapsed"
    )

with col_turmas:
    st.markdown("**👥 turmas.csv**")
    st.caption("`turma · alunos · disciplina · tipo`")
    upload_turmas = st.file_uploader(
        "Selecione turmas.csv", type="csv", key="up_turmas",
        label_visibility="collapsed"
    )

with col_salas:
    st.markdown("**🏫 salas.csv**")
    st.caption("`sala · capacidade · tipo`")
    upload_salas = st.file_uploader(
        "Selecione salas.csv", type="csv", key="up_salas",
        label_visibility="collapsed"
    )


# =============================================================================
# VALIDAÇÃO DOS ARQUIVOS ENVIADOS
# Cada arquivo é validado individualmente; erros são exibidos inline.
# A grade só pode ser gerada se os três passarem na validação.
# =============================================================================

# Dicionário que acumulará os DataFrames válidos
dados_validos: dict[str, pd.DataFrame] = {}
arquivos_com_erro = False

def _processar_upload(arquivo, chave: str, container) -> pd.DataFrame | None:
    """
    Lê, valida e exibe o status de um arquivo no container fornecido.
    Retorna o DataFrame em caso de sucesso, ou None em falha.
    """
    if arquivo is None:
        return None

    df, erro = ler_csv_upload(arquivo, chave)

    if erro:
        container.error(f"❌ **Erro em `{arquivo.name}`:** {erro}")
        return None
    else:
        container.success(
            f"✅ `{arquivo.name}` — {len(df)} linha(s) carregada(s)."
        )
        return df


df_prof   = _processar_upload(upload_prof,   'professores', col_prof)
df_turmas = _processar_upload(upload_turmas, 'turmas',      col_turmas)
df_salas  = _processar_upload(upload_salas,  'salas',       col_salas)

todos_validos = all(df is not None for df in [df_prof, df_turmas, df_salas])

if df_prof   is not None: dados_validos['professores'] = df_prof
if df_turmas is not None: dados_validos['turmas']      = df_turmas
if df_salas  is not None: dados_validos['salas']       = df_salas


# =============================================================================
# PASSO 2 — PRÉVIA DOS DADOS (expansível)
# Mostra as primeiras linhas de cada CSV carregado com sucesso.
# =============================================================================

if dados_validos:
    st.divider()
    st.subheader("Passo 2 — Prévia dos dados carregados")

    abas_nomes = [k for k in ['professores', 'turmas', 'salas'] if k in dados_validos]
    abas = st.tabs([f"📄 {n}.csv" for n in abas_nomes])

    for aba, nome in zip(abas, abas_nomes):
        with aba:
            df = dados_validos[nome]
            st.dataframe(df, use_container_width=True, height=200)
            st.caption(
                f"{len(df)} linha(s) · {len(df.columns)} coluna(s)"
            )


# =============================================================================
# PASSO 3 — GERAÇÃO DA GRADE
# Botão habilitado apenas quando os três arquivos estão válidos.
# Avisos de turmas não alocadas são capturados e exibidos na tela.
# =============================================================================

st.divider()
st.subheader("Passo 3 — Gerar a Grade de Horários")

if not todos_validos:
    arquivos_faltando = sum([
        upload_prof   is None,
        upload_turmas is None,
        upload_salas  is None,
    ])
    st.info(
        f"⏳ Aguardando o envio de **{arquivos_faltando}** arquivo(s) "
        f"para liberar a geração da grade."
    )

btn_gerar = st.button(
    "🚀 Gerar Grade de Horários",
    disabled=not todos_validos,
    type="primary",
    use_container_width=True,
)

# Armazena a grade e os avisos no estado da sessão para persistir entre
# re-renderizações do Streamlit (evita regerar ao interagir com a UI).
if btn_gerar and todos_validos:
    with st.spinner("Processando alocações..."):
        grade, avisos = capturar_avisos_grade(dados_validos)
    st.session_state['grade']  = grade
    st.session_state['avisos'] = avisos


# =============================================================================
# PASSO 4 — EXIBIÇÃO DOS RESULTADOS
# Exibe a grade gerada, estatísticas resumidas e avisos de turmas pendentes.
# =============================================================================

if 'grade' in st.session_state:
    grade: pd.DataFrame = st.session_state['grade']
    avisos: str         = st.session_state.get('avisos', '')

    st.divider()
    st.subheader("Passo 4 — Resultado da Grade")

    # ── Métricas resumidas ────────────────────────────────────────────────
    total_turmas_csv = len(dados_validos.get('turmas', pd.DataFrame()))
    total_alocadas   = grade['turma'].nunique() if not grade.empty else 0
    total_nao_aloc   = total_turmas_csv - total_alocadas

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Turmas no CSV",       total_turmas_csv)
    m2.metric("Turmas alocadas",     total_alocadas,
              delta=None if total_alocadas == 0 else f"+{total_alocadas}")
    m3.metric("Turmas sem alocação", total_nao_aloc,
              delta=f"-{total_nao_aloc}" if total_nao_aloc > 0 else None,
              delta_color="inverse")
    m4.metric("Professores usados",
              grade['professor'].nunique() if not grade.empty else 0)

    # ── Avisos de turmas não alocadas (capturados do stdout de gerar_grade) ─
    if avisos:
        with st.expander("⚠️ Turmas não alocadas — clique para ver detalhes", expanded=True):
            for linha in avisos.split('\n'):
                if linha.strip():
                    st.markdown(
                        f'<div class="aviso-turma">{linha}</div>',
                        unsafe_allow_html=True
                    )
            st.caption(
                "Verifique se há professores habilitados, salas compatíveis "
                "e horários disponíveis para essas turmas nos CSVs."
            )

    # ── Tabela da grade gerada ────────────────────────────────────────────
    if grade.empty:
        st.warning(
            "Nenhuma aula pôde ser alocada. Revise os dados dos CSVs e "
            "verifique se há professores habilitados e salas compatíveis."
        )
    else:
        st.markdown("**Grade gerada:**")

        # Agrupa turmas compartilhadas (SI1;CC1) para exibição
        grade_exibicao = (
            grade
            .groupby(['disciplina', 'professor', 'sala', 'dia', 'horario'], sort=False)
            .agg(turma=('turma', lambda ids: ';'.join(ids)))
            .reset_index()
        )[['turma', 'disciplina', 'professor', 'sala', 'dia', 'horario']]

        st.dataframe(
            grade_exibicao,
            use_container_width=True,
            height=min(400, 60 + len(grade_exibicao) * 35),
        )

        # ── Botão de download ─────────────────────────────────────────────
        csv_bytes = converter_grade_para_bytes(grade)
        st.download_button(
            label="⬇️ Baixar grade_final.csv",
            data=csv_bytes,
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
    "Desenvolvido com Python + Pandas + Streamlit"
)