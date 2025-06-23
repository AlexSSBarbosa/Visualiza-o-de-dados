import streamlit as st
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(
    page_title="2. Análise por Perfil",
    page_icon="👤",
    layout="wide"
)

st.sidebar.header("Filtros")

# Carregar dados e opções iniciais
df, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# Filtros na sidebar
filtro_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Mostrar somente pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

anos_selecionados = st.sidebar.multiselect(
    "Ano da criação da FAV",
    options=anos_disponiveis,
    default=anos_disponiveis
)

meses_selecionados = st.sidebar.multiselect(
    "Mês da criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# Aplicar filtro nos dados
df_filtrado, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=False,
    filtros_acesso=filtro_acesso,
    anos_selecionados=anos_selecionados,
    meses_selecionados=meses_selecionados
)

# Aplicar filtro de crônico se marcado
if filtro_cronico:
    df_filtrado = df_filtrado[df_filtrado['CRONICO_3_MESES'] == True]

# Verificação de segurança: se DataFrame está vazio ou colunas essenciais ausentes
colunas_necessarias = ['IDADE', 'TEMPO_ESPERA_DIAS']
if df_filtrado.empty or any(col not in df_filtrado.columns for col in colunas_necessarias):
    st.warning("Nenhum dado disponível para os filtros selecionados.")
    st.stop()

# Título da página
st.title("2. Análise por Perfil Demográfico")
st.markdown("Visualização do tempo de espera conforme idade, sexo, raça/cor e faixa etária dos pacientes.")

# Faixa etária: slider
idade_min, idade_max = int(df_filtrado['IDADE'].min()), int(df_filtrado['IDADE'].max())
idade_range = st.slider(
    "Idade dos Pacientes",
    min_value=idade_min,
    max_value=idade_max,
    value=(idade_min, idade_max)
)

df_filtrado = df_filtrado[(df_filtrado['IDADE'] >= idade_range[0]) & (df_filtrado['IDADE'] <= idade_range[1])]

# Métricas principais
col1, col2, col3 = st.columns(3)
col1.metric("Tempo Médio de Espera", f"{df_filtrado['TEMPO_ESPERA_DIAS'].mean():.0f} dias")
col2.metric("Número de Pacientes", f"{len(df_filtrado)}")
col3.metric("Unidades Hospitalares", f"{df_filtrado['COD_UNIDADE_HOSPITALAR'].nunique()}")

st.markdown("---")

# Boxplot por faixa etária
with st.expander("📊 Tempo de Espera por Faixa Etária"):
    fig_faixa = px.box(
        df_filtrado,
        x='FAIXA_ETARIA',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'FAIXA_ETARIA': 'Faixa Etária', 'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'},
        title="Tempo de Espera por Faixa Etária"
    )
    st.plotly_chart(fig_faixa, use_container_width=True)

# Boxplot por sexo
with st.expander("📊 Tempo de Espera por Sexo"):
    fig_sexo = px.box(
        df_filtrado,
        x='SEXO',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'SEXO': 'Sexo', 'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'},
        title="Tempo de Espera por Sexo"
    )
    st.plotly_chart(fig_sexo, use_container_width=True)

# Boxplot por raça/cor
with st.expander("📊 Tempo de Espera por Raça/Cor"):
    fig_raca = px.box(
        df_filtrado,
        x='RACA_COR',
        y='TEMPO_ESPERA_DIAS',
        points="all",
        labels={'RACA_COR': 'Raça/Cor', 'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'},
        title="Tempo de Espera por Raça/Cor"
    )
    st.plotly_chart(fig_raca, use_container_width=True)

# Amostra de dados
with st.expander("📋 Mostrar dados filtrados"):
    st.dataframe(df_filtrado, use_container_width=True)

# Exportar CSV
st.markdown("---")
with st.expander("📥 Exportar dados filtrados"):
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📄 Baixar CSV",
        data=csv,
        file_name='dados_filtrados_perfil.csv',
        mime='text/csv'
    )
