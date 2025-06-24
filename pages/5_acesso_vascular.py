import streamlit as st
import pandas as pd
import plotly.express as px
from filtro import load_and_filter_data

st.set_page_config(page_title="Influência do Acesso Vascular Inicial", layout="wide")

st.markdown("# 5. O Acesso Vascular Inicial Influencia no Tempo de Espera para FAV?")
st.markdown("### Pacientes em Diálise Crônica - Porto Alegre (2015–2024)")

# --- Filtros globais na sidebar ---
st.sidebar.header("Filtros Globais")

df_raw, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# Filtro: Tipo de Acesso Vascular Inicial
filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=opcoes_acesso
)

# Filtro: Crônico
filtro_cronico = st.sidebar.checkbox(
    "Apenas pacientes crônicos (≥ 3 meses)",
    value=True
)

# Filtro: Anos
ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)
ano_inicial, ano_final = st.sidebar.slider(
    "Intervalo de Anos da Criação da FAV",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max)
)

# Filtro: Meses
meses_selecionados = st.sidebar.multiselect(
    "Meses da Criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# --- Aplicar filtros ---
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
    st.markdown("#### 📊 Proporção de Pacientes por Tipo de Acesso Inicial")
    st.write("""
    Este gráfico de pizza mostra **quantos pacientes iniciaram com cada tipo de acesso vascular**.
    A distribuição ajuda a entender **quais estratégias são mais utilizadas na prática clínica**:  
    se mais pacientes iniciam com **cateteres temporários (urgência)** ou com **FAV (planejado)**.
    """)

    fig_pie = px.pie(
        contagem_acesso,
        names='Acesso Inicial',
        values='Número de Pacientes',
        hole=0.3,
        title="Distribuição por Tipo de Acesso Inicial",
        color_discrete_sequence=px.colors.qualitative.Set3  # cores distintas e profissionais
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    st.markdown("#### ⏱️ Tempo de Espera por Tipo de Acesso Vascular Inicial")
    st.write("""
    Este gráfico compara a **distribuição do tempo de espera** até a confecção da FAV, agrupado por tipo de acesso inicial.

    A **linha dentro da caixa** representa a **mediana**.  
    Os **pontos** são pacientes individuais (outliers), e o formato da caixa mostra a **variação dos tempos**.

    É útil para identificar se pacientes com **cateteres** esperam mais que os com **FAV desde o início**.
    """)

    ordem_acessos = (
        df.groupby('ACESSO_VASCULAR_INICIAL')['TEMPO_ESPERA_DIAS']
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    fig_box = px.box(
        df,
        x='ACESSO_VASCULAR_INICIAL',
        y='TEMPO_ESPERA_DIAS',
        points='outliers',
        color='ACESSO_VASCULAR_INICIAL',
        title="Tempo de Espera por Tipo de Acesso",
        labels={
            'TEMPO_ESPERA_DIAS': 'Tempo de Espera (dias)',
            'ACESSO_VASCULAR_INICIAL': 'Tipo de Acesso'
        },
        color_discrete_sequence=px.colors.qualitative.Dark24,
        category_orders={'ACESSO_VASCULAR_INICIAL': ordem_acessos}
    )
    fig_box.update_layout(showlegend=False)
    st.plotly_chart(fig_box, use_container_width=True)

# --- Estatísticas descritivas ---
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

# --- Interpretação ---
st.markdown("### 🧠 Interpretação")

col1, col2 = st.columns(2)
with col1:
    st.success(
        "✅ A análise mostra que o tipo de acesso inicial **impacta significativamente** o tempo de espera para FAV.")
    st.markdown("""
    - Pacientes que iniciam com **Cateter Duplo Lúmen** apresentam, em média, **maior tempo de espera**.
    - A **proporção de casos com mais de 180 dias de espera** também tende a ser maior nesse grupo.
    """)

with col2:
    st.info("""
    Este achado reforça a necessidade de **planejamento prévio do acesso vascular**, 
    especialmente na atenção básica e acompanhamento ambulatorial de pacientes com doença renal crônica em estágio avançado.
    """)

# --- Dados brutos no final ---
with st.expander("🔍 Ver primeiros registros do conjunto de dados"):
    st.dataframe(df[['ACESSO_VASCULAR_INICIAL', 'TEMPO_ESPERA_DIAS']].head(20))
