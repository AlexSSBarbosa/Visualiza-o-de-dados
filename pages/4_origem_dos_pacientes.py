import streamlit as st
import pandas as pd
import plotly.express as px
from filtro import load_and_filter_data

# --- Configuração da página ---
st.set_page_config(page_title="Origem dos Pacientes", page_icon="📍", layout="wide")
st.title("📍 Origem dos Pacientes em Tratamento Dialítico")

# --- Carregar dados base para opções de filtro ---
df_base, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()

# --- Sidebar: Filtros globais ---
st.sidebar.header("Filtros Globais")

anos_selecionados = st.sidebar.multiselect(
    "Ano de Criação da FAV",
    options=anos_disponiveis,
    default=anos_disponiveis
)

meses_selecionados = st.sidebar.multiselect(
    "Mês de Criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico_default = st.sidebar.checkbox(
    "Apenas pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

# --- Aplicar filtros e carregar dados ---
df, _, _, _ = load_and_filter_data(
    anos_selecionados=anos_selecionados,
    meses_selecionados=meses_selecionados,
    filtros_acesso=filtros_acesso,
    filtro_cronico_default=filtro_cronico_default
)

# --- Verificação de dados ---
if df.empty:
    st.warning("⚠️ Nenhum dado disponível com os filtros selecionados.")
    st.stop()

# --- Carregar base de municípios ---
@st.cache_data
def load_municipios():
    return pd.read_csv("municipios_rs.csv")

df_mun = load_municipios()

# --- Padronização e mapeamento dos municípios ---
df['codigo6'] = df['MUN_RESIDENCIA_COD'].astype(str).str[:6].str.zfill(6)
df_mun['codigo6'] = df_mun['codigo'].astype(str).str[:6].str.zfill(6)

mapa_codigos = dict(zip(df_mun['codigo6'], df_mun['nome']))
df['Municipio'] = df['codigo6'].map(mapa_codigos).fillna("Não informado")

# --- Contagem por município ---
contagem = df['Municipio'].value_counts().reset_index()
contagem.columns = ['Municipio', 'Qtde']
contagem = contagem.sort_values("Qtde", ascending=False)

# --- Informações Resumidas ---
st.markdown(f"""
**Pacientes identificados:** {len(df)}  
**Municípios distintos:** {contagem['Municipio'].nunique()}  
**Sem município informado:** {contagem.loc[contagem['Municipio'] == 'Não informado', 'Qtde'].sum() if 'Não informado' in contagem['Municipio'].values else 0}
""")

# --- Gráfico 1: Treemap dos 10 principais municípios ---
fig_tree = px.treemap(
    contagem.head(10),
    path=['Municipio'], values='Qtde',
    title="🌳 Distribuição por Município (Top 10)",
    color='Qtde', color_continuous_scale='Blues'
)
st.plotly_chart(fig_tree, use_container_width=True)

# --- Gráfico 2: Barra horizontal (Top 10) ---
fig_bar = px.bar(
    contagem.head(10),
    x='Municipio', y='Qtde', text='Qtde',
    title="🏙️ Principais Municípios de Origem (Top 10)",
    labels={'Qtde': 'Número de Pacientes'},
    color='Qtde', color_continuous_scale='Tealgrn'
)
fig_bar.update_traces(textposition="outside")
st.plotly_chart(fig_bar, use_container_width=True)

# --- Gráfico 3: Pizza (Percentual dos Top 10) ---
contagem['Percentual'] = 100 * contagem['Qtde'] / contagem['Qtde'].sum()
fig_pie = px.pie(
    contagem.head(10),
    names='Municipio', values='Percentual',
    title="🥧 Participação Percentual por Município (Top 10)",
    hole=0.4
)
st.plotly_chart(fig_pie, use_container_width=True)
