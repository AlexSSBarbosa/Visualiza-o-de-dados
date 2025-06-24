import streamlit as st
import altair as alt
from filtro import load_and_filter_data

# --- Configuração da página ---
st.set_page_config(
    page_title="Tempo de Espera para FAV - Porto Alegre",
    page_icon="🩺",
    layout="wide"
)

st.title("⏱️ Tempo de Espera para Confecção de FAV")
st.markdown("### Pacientes em Diálise Crônica | Porto Alegre (2015–2024)")

# --- Filtros na barra lateral ---
st.sidebar.header("Filtros Globais")

# Carregamento inicial dos dados e opções
df_base, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=False
)

if df_base is None or df_base.empty:
    st.warning("⚠️ Dados não disponíveis.")
    st.stop()

# Tipo de acesso
filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

# Pacientes crônicos
filtro_cronico = st.sidebar.checkbox(
    "Somente pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

# Intervalo de anos
ano_min = min(anos_disponiveis) if anos_disponiveis else 2015
ano_max = max(anos_disponiveis) if anos_disponiveis else 2024
ano_inicial, ano_final = st.sidebar.slider(
    "Intervalo de Anos (Criação da FAV)",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1
)

# Meses
meses_selecionados = st.sidebar.multiselect(
    "Meses (Criação da FAV)",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# --- Aplicar filtros e carregar dados filtrados ---
df_filtrado, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtros_acesso,
    anos_selecionados=list(range(ano_inicial, ano_final + 1)),
    meses_selecionados=meses_selecionados
)

if df_filtrado.empty:
    st.warning("⚠️ Nenhum paciente encontrado com os filtros aplicados.")
    st.stop()

# --- Indicadores principais ---
col1, col2, col3 = st.columns(3)
col1.metric("Tempo Médio de Espera", f"{df_filtrado['TEMPO_ESPERA_DIAS'].mean():.0f} dias")
col2.metric("Número de Pacientes", f"{len(df_filtrado)}")
col3.metric("Unidades Hospitalares", f"{df_filtrado['COD_UNIDADE_HOSPITALAR'].nunique()}")

# --- Evolução temporal ---
with st.expander("📈 Evolução Anual do Tempo de Espera"):
    media_anual = df_filtrado.groupby("ANO_FAV")["TEMPO_ESPERA_DIAS"].mean().reset_index()
    media_anual.columns = ["Ano", "Tempo Médio (dias)"]

    chart_linha = alt.Chart(media_anual).mark_line(point=True).encode(
        x=alt.X("Ano:O", axis=alt.Axis(title="Ano")),
        y=alt.Y("Tempo Médio (dias):Q", axis=alt.Axis(title="Tempo Médio (dias)", format=".0f")),
        tooltip=["Ano", "Tempo Médio (dias)"]
    ).properties(
        title="Tempo Médio Anual para Confecção da FAV",
        width=700,
        height=350
    )
    st.altair_chart(chart_linha, use_container_width=True)

    chart_boxplot = alt.Chart(df_filtrado).mark_boxplot(extent='min-max').encode(
        x=alt.X("ANO_FAV:O", title="Ano"),
        y=alt.Y("TEMPO_ESPERA_DIAS:Q", title="Tempo de Espera (dias)"),
        tooltip=["ANO_FAV", "TEMPO_ESPERA_DIAS"]
    ).properties(
        title="Distribuição Anual do Tempo de Espera",
        width=700,
        height=350
    )
    st.altair_chart(chart_boxplot, use_container_width=True)

# --- Distribuições por características dos pacientes ---
with st.expander("📊 Distribuição dos Pacientes por Características"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Distribuição por Sexo**")
        st.bar_chart(df_filtrado['SEXO'].value_counts())

    with col2:
        st.write("**Distribuição por Faixa Etária**")
        st.bar_chart(df_filtrado['FAIXA_ETARIA'].value_counts().sort_index())

    with col3:
        st.write("**Distribuição por Raça/Cor**")
        st.bar_chart(df_filtrado['RACA_COR'].value_counts())

# --- Tempo médio por tipo de acesso ---
with st.expander("📋 Tempo Médio por Tipo de Acesso Vascular"):
    media_por_acesso = (
        df_filtrado
        .groupby("ACESSO_VASCULAR_INICIAL")["TEMPO_ESPERA_DIAS"]
        .agg(['mean', 'count'])
        .round(0)
        .rename(columns={'mean': 'Tempo Médio (dias)', 'count': 'Número de Pacientes'})
    )
    st.dataframe(media_por_acesso)

# --- Amostra de dados ---
st.markdown("---")
if st.checkbox("🔍 Visualizar amostra dos dados filtrados"):
    st.dataframe(df_filtrado.head(20), use_container_width=True)

# --- Rodapé informativo ---
st.info("""
📌 Este painel interativo visa apresentar o tempo de espera entre o início da diálise crônica e a confecção da fístula arteriovenosa (FAV) em Porto Alegre, entre os anos de 2015 e 2024.  
Os filtros permitem explorar padrões conforme período, tipo de acesso vascular e características clínicas dos pacientes.
""")
