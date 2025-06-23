import streamlit as st
import altair as alt
from filtro import load_and_filter_data

st.set_page_config(
    page_title="Dashboard Tempo de Espera FAV - POA",
    page_icon="🩺",
    layout="wide"
)

st.sidebar.header("Filtros Globais")

# Carrega dados brutos, opções de filtro para UI
df, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=False
)

if df is None or df.empty:
    st.warning("Dados não encontrados ou vazios.")
    st.stop()

# Filtros na sidebar
filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Mostrar somente pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

ano_min = min(anos_disponiveis) if anos_disponiveis else 2015
ano_max = max(anos_disponiveis) if anos_disponiveis else 2024
ano_inicial, ano_final = st.sidebar.slider(
    "Selecione o intervalo de anos da criação da FAV",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1
)

meses_selecionados = st.sidebar.multiselect(
    "Selecione os meses da criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# Recarrega dados já filtrados conforme seleção
df_filtrado, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtros_acesso,
    anos_selecionados=list(range(ano_inicial, ano_final + 1)),
    meses_selecionados=meses_selecionados
)

st.title("⏱️ Tempo de Espera para Confecção de FAV em Pacientes em Diálise Crônica")
st.markdown("### Porto Alegre (2015–2024)")

# Indicadores principais
col1, col2, col3 = st.columns(3)
col1.metric("Tempo Médio de Espera", f"{df_filtrado['TEMPO_ESPERA_DIAS'].mean():.0f} dias")
col2.metric("Número de Pacientes", f"{len(df_filtrado)}")
col3.metric("Unidades Hospitalares", f"{df_filtrado['COD_UNIDADE_HOSPITALAR'].nunique()}")

# Gráficos temporais
with st.expander("📈 Evolução Anual da Média e Dispersão de Espera"):
    media_anual = df_filtrado.groupby("ANO_FAV")["TEMPO_ESPERA_DIAS"].mean().reset_index()
    media_anual.columns = ["Ano", "Tempo Médio (dias)"]

    chart_media = alt.Chart(media_anual).mark_line(point=True).encode(
        x=alt.X("Ano:O", axis=alt.Axis(title="Ano")),
        y=alt.Y("Tempo Médio (dias):Q", axis=alt.Axis(title="Tempo Médio (dias)", format=".0f")),
        tooltip=["Ano", "Tempo Médio (dias)"]
    ).properties(
        width=700,
        height=350,
        title="Evolução Anual da Média de Espera"
    )
    st.altair_chart(chart_media, use_container_width=True)

    boxplot = alt.Chart(df_filtrado).mark_boxplot(extent='min-max').encode(
        x=alt.X("ANO_FAV:O", title="Ano"),
        y=alt.Y("TEMPO_ESPERA_DIAS:Q", title="Tempo de Espera (dias)"),
        tooltip=["ANO_FAV", "TEMPO_ESPERA_DIAS"]
    ).properties(
        width=700,
        height=350,
        title="Boxplot da Distribuição Anual dos Tempos de Espera"
    )
    st.altair_chart(boxplot, use_container_width=True)

# Distribuições demográficas
with st.expander("📊 Distribuições por Característica"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Sexo**")
        st.bar_chart(df_filtrado['SEXO'].value_counts())

    with col2:
        st.write("**Faixa Etária**")
        st.bar_chart(df_filtrado['FAIXA_ETARIA'].value_counts().sort_index())

    with col3:
        st.write("**Raça/Cor**")
        st.bar_chart(df_filtrado['RACA_COR'].value_counts())

# Tempo médio por tipo de acesso
with st.expander("📋 Tempo Médio por Tipo de Acesso Vascular"):
    media_por_acesso = df_filtrado.groupby("ACESSO_VASCULAR_INICIAL")["TEMPO_ESPERA_DIAS"].agg(['mean', 'count']).round(0)
    media_por_acesso = media_por_acesso.rename(columns={'mean': 'Tempo Médio (dias)', 'count': 'Pacientes'})
    st.dataframe(media_por_acesso)

# Amostra dos dados filtrados
st.markdown("---")
if st.checkbox("🔍 Mostrar amostra dos dados filtrados"):
    st.dataframe(df_filtrado.head(20), use_container_width=True)

# Informação final
st.info("💡 Este painel busca identificar padrões temporais e populacionais na criação da FAV para pacientes em diálise crônica em Porto Alegre.")
