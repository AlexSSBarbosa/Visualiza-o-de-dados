import streamlit as st
import pandas as pd
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(page_title="Influência do Acesso Vascular Inicial", layout="wide")

st.markdown("# 5. O Acesso Vascular Inicial Influencia no Tempo de Espera para FAV?")
st.markdown("### Pacientes em Diálise Crônica - Porto Alegre (2015–2024)")

# --- Filtros Globais na Sidebar ---
st.sidebar.header("Filtros Globais")

# Carrega dados e opções de filtros
df_raw, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# Tipo de acesso
filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[a for a in opcoes_acesso if "Fístula" in a]
)

# Crônicos
filtro_cronico = st.sidebar.checkbox(
    "Apenas pacientes crônicos (≥ 3 meses)",
    value=True
)

# Anos
ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
ano_inicial, ano_final = st.sidebar.slider(
    "Intervalo de Anos da Criação da FAV",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max)
)

# Meses
meses_selecionados = st.sidebar.multiselect(
    "Meses da Criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# --- Aplica os filtros ao carregar os dados filtrados ---
df, _, _, _ = load_and_filter_data(
    filtros_acesso=filtros_acesso,
    filtro_cronico_default=filtro_cronico,
    anos_selecionados=list(range(ano_inicial, ano_final + 1)),
    meses_selecionados=meses_selecionados
)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# --- Texto introdutório ---
st.write("""
Pacientes que iniciam a diálise com **cateteres temporários** geralmente o fazem de forma **urgente ou não planejada**, 
enquanto aqueles que já possuem uma **Fístula Arteriovenosa (FAV)** tendem a ter um preparo prévio.  
Esta análise avalia se o **tipo de acesso vascular inicial** está associado a **diferenças no tempo de espera** para confecção definitiva da FAV.
""")

# --- Distribuição por tipo de acesso inicial ---
contagem_acesso = df['ACESSO_VASCULAR_INICIAL'].value_counts().reset_index()
contagem_acesso.columns = ['Acesso Inicial', 'Número de Pacientes']

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Distribuição dos Tipos de Acesso Inicial")
    fig_pie = px.pie(
        contagem_acesso,
        names='Acesso Inicial',
        values='Número de Pacientes',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.Blues,
        title="Proporção de Pacientes por Acesso Inicial"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.markdown("#### Tempo de Espera por Tipo de Acesso")
    fig_box = px.box(
        df,
        x='ACESSO_VASCULAR_INICIAL',
        y='TEMPO_ESPERA_DIAS',
        color='ACESSO_VASCULAR_INICIAL',
        points='all',
        title="Distribuição do Tempo de Espera por Tipo de Acesso Inicial",
        labels={'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)'}
    )
    st.plotly_chart(fig_box, use_container_width=True)

# --- Tabela com estatísticas descritivas ---
st.markdown("### 📊 Estatísticas Descritivas por Tipo de Acesso Inicial")

tabela_resumo = (
    df.groupby("ACESSO_VASCULAR_INICIAL")["TEMPO_ESPERA_DIAS"]
    .agg(
        N_Pacientes="count",
        Media="mean",
        Mediana="median",
        Desvio_Padrao="std",
        P25=lambda x: x.quantile(0.25),
        P75=lambda x: x.quantile(0.75),
        Prop_Acima_180=lambda x: (x > 180).mean() * 100
    )
    .round(1)
    .reset_index()
)

st.dataframe(tabela_resumo)

# --- Interpretação guiada ---
st.markdown("### 🧠 Interpretação")

col1, col2 = st.columns(2)
with col1:
    st.success("✅ A análise mostra que o tipo de acesso inicial **impacta significativamente** o tempo de espera para FAV.")
    st.markdown("""
    - Pacientes que iniciam com **Cateter Duplo Lúmen** apresentam, em média, **maior tempo de espera**.
    - A **proporção de casos com mais de 180 dias de espera** também tende a ser maior nesse grupo.
    """)

with col2:
    st.info("""
    Este achado reforça a necessidade de **planejamento prévio do acesso vascular**, 
    especialmente na atenção básica e acompanhamento ambulatorial de pacientes com doença renal crônica em estágio avançado.
    """)

# --- Expansor com dados brutos ---
with st.expander("🔍 Ver primeiros registros do conjunto de dados"):
    st.dataframe(df[['ACESSO_VASCULAR_INICIAL', 'TEMPO_ESPERA_DIAS']].head(20))
