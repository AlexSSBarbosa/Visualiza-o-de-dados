import streamlit as st
import pandas as pd
import plotly.express as px
from filtro import load_and_filter_data

# --- Configuração da página ---
st.set_page_config(
    page_title="3. Análise Temporal e Perfis Clínicos - FAV",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Análise Temporal e Perfis Clínicos do Tempo de Espera para FAV")

# --- Mapeamento de código para nome dos hospitais ---
codigo_hospital_nome = {
    '2237253': 'Santa Casa de Porto Alegre',
    '2237571': 'Nossa Senhora da Conceição',
    '2237598': 'Divina Providência',
    '2237601': 'Hospital de Clínicas de Porto Alegre',
    '2262460': 'Vitarim Clínica do Rim',
    '2262509': 'SER – Serviço de Doenças Renais',
    '2262568': 'Hospital São Lucas da PUCRS',
    '2262584': 'Clinirim',
    '2262770': 'Centro de Diálise e Transplante',
    '5844762': 'Instituto de Doenças Renais'
}

# --- Filtros Globais ---
st.sidebar.header("Filtros Globais")

df_base, opcoes_acesso, anos_disponiveis, meses_disponiveis = load_and_filter_data()
df_base['COD_UNIDADE_HOSPITALAR'] = df_base['COD_UNIDADE_HOSPITALAR'].astype(str)
df_base['NOME_HOSPITAL'] = df_base['COD_UNIDADE_HOSPITALAR'].map(codigo_hospital_nome).fillna("Desconhecido")

# Filtros
filtros_acesso = st.sidebar.multiselect(
    "Tipo de Acesso Vascular Inicial",
    options=opcoes_acesso,
    default=[ac for ac in opcoes_acesso if "Fístula" in ac]
)

filtro_cronico = st.sidebar.checkbox(
    "Apenas pacientes crônicos (≥ 3 meses de tratamento)",
    value=True
)

ano_inicial, ano_final = st.sidebar.slider(
    "Intervalo de Anos da Criação da FAV",
    min_value=min(anos_disponiveis),
    max_value=max(anos_disponiveis),
    value=(min(anos_disponiveis), max(anos_disponiveis)),
    step=1
)

meses_selecionados = st.sidebar.multiselect(
    "Meses de Criação da FAV",
    options=meses_disponiveis,
    format_func=lambda x: f"{x:02d}",
    default=meses_disponiveis
)

# --- Aplicar filtros globais ---
df, _, _, _ = load_and_filter_data(
    filtro_acesso_default=False,
    filtro_cronico_default=filtro_cronico,
    filtros_acesso=filtros_acesso,
    anos_selecionados=list(range(ano_inicial, ano_final + 1)),
    meses_selecionados=meses_selecionados
)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

df['COD_UNIDADE_HOSPITALAR'] = df['COD_UNIDADE_HOSPITALAR'].astype(str)
df['NOME_HOSPITAL'] = df['COD_UNIDADE_HOSPITALAR'].map(codigo_hospital_nome).fillna("Desconhecido")

# --- Resumo dos filtros aplicados ---
with st.sidebar.expander("📌 Resumo dos Filtros Aplicados"):
    st.markdown(f"**Acesso Vascular:** {', '.join(filtros_acesso) or 'Todos'}")
    st.markdown(f"**Crônicos:** {'Sim' if filtro_cronico else 'Não'}")
    st.markdown(f"**Anos:** {ano_inicial}–{ano_final}")
    st.markdown(f"**Meses:** {', '.join([f'{m:02d}' for m in meses_selecionados])}")

st.markdown(f"**Pacientes após filtros globais:** {len(df)}")

# --- Filtros adicionais da página ---
st.sidebar.header("Filtros Adicionais")

hospital_options = sorted(df['COD_UNIDADE_HOSPITALAR'].unique())
faixa_etaria_options = sorted(df['FAIXA_ETARIA'].astype(str).unique())
sexo_options = sorted(df['SEXO'].astype(str).unique())
raca_options = sorted(df['RACA_COR'].astype(str).unique())

hospital_selec = st.sidebar.multiselect(
    "Hospital",
    options=hospital_options,
    default=hospital_options,
    format_func=lambda x: codigo_hospital_nome.get(x, "Desconhecido")
)
faixa_etaria_selec = st.sidebar.multiselect("Faixa Etária", faixa_etaria_options, default=faixa_etaria_options)
sexo_selec = st.sidebar.multiselect("Sexo", sexo_options, default=sexo_options)
raca_selec = st.sidebar.multiselect("Raça/Cor", raca_options, default=raca_options)

# --- Aplicar filtros adicionais ---
df_filt = df[
    df['COD_UNIDADE_HOSPITALAR'].isin(hospital_selec) &
    df['FAIXA_ETARIA'].astype(str).isin(faixa_etaria_selec) &
    df['SEXO'].astype(str).isin(sexo_selec) &
    df['RACA_COR'].astype(str).isin(raca_selec)
].copy()

if df_filt.empty:
    st.warning("⚠️ Nenhum dado após aplicação dos filtros adicionais.")
    st.stop()

# --- Preparar dados temporais ---
df_filt['DATA_CRIACAO_FAV'] = pd.to_datetime(df_filt['DATA_CRIACAO_FAV'], errors='coerce')
df_filt.dropna(subset=['DATA_CRIACAO_FAV'], inplace=True)
df_filt['MES_ANO'] = df_filt['DATA_CRIACAO_FAV'].dt.to_period('M').dt.to_timestamp()

st.markdown(f"**Pacientes após filtros adicionais:** {len(df_filt)}")

# --- Parâmetros de pandemia ---
inicio_pandemia = pd.to_datetime("2020-03-01")
fim_pandemia = pd.to_datetime("2022-03-31")

# --- Gráfico Geral: Tempo Médio Mensal ---
st.markdown("---")
st.subheader("🗓️ Tempo Médio Mensal para Criação de FAV")

df_tempo_mes = df_filt.groupby('MES_ANO')['TEMPO_ESPERA_DIAS'].mean().reset_index()

fig_tempo = px.line(
    df_tempo_mes,
    x='MES_ANO',
    y='TEMPO_ESPERA_DIAS',
    title="Evolução do Tempo Médio para Criação da FAV (mensal)",
    markers=True,
    labels={'MES_ANO': 'Mês/Ano', 'TEMPO_ESPERA_DIAS': 'Tempo Médio (dias)'}
)

# Adiciona pico
pico = df_tempo_mes.loc[df_tempo_mes['TEMPO_ESPERA_DIAS'].idxmax()]
fig_tempo.add_scatter(
    x=[pico['MES_ANO']], y=[pico['TEMPO_ESPERA_DIAS']],
    mode='markers+text',
    marker=dict(size=12, color='green'),
    text=[f"Pico: {pico['TEMPO_ESPERA_DIAS']:.0f}d"],
    textposition="top center"
)

# Pandemia
fig_tempo.add_vrect(
    x0=inicio_pandemia, x1=fim_pandemia,
    fillcolor="red", opacity=0.2,
    layer="below", line_width=0,
    annotation_text="COVID-19", annotation_position="top left"
)

fig_tempo.update_layout(showlegend=False)
st.plotly_chart(fig_tempo, use_container_width=True)

# --- Função para gráficos por subgrupos ---
def grafico_temporal(df_grupo, grupo, titulo):
    fig = px.line(
        df_grupo,
        x='MES_ANO',
        y='TEMPO_ESPERA_DIAS',
        color=grupo,
        markers=True,
        title=titulo,
        labels={'MES_ANO': 'Mês/Ano', 'TEMPO_ESPERA_DIAS': 'Tempo Médio (dias)', grupo: grupo}
    )

    for categoria in df_grupo[grupo].unique():
        df_c = df_grupo[df_grupo[grupo] == categoria]
        if not df_c.empty:
            idx = df_c['TEMPO_ESPERA_DIAS'].idxmax()
            ponto = df_c.loc[idx]
            fig.add_scatter(
                x=[ponto['MES_ANO']],
                y=[ponto['TEMPO_ESPERA_DIAS']],
                mode='markers+text',
                marker=dict(size=10),
                text=[f"{categoria}: {ponto['TEMPO_ESPERA_DIAS']:.0f}d"],
                textposition="top center"
            )

    fig.add_vrect(
        x0=inicio_pandemia, x1=fim_pandemia,
        fillcolor="red", opacity=0.2,
        layer="below", line_width=0,
        annotation_text="COVID-19", annotation_position="top left"
    )

    return fig

# --- Gráficos por perfil clínico ---
st.markdown("---")
st.subheader("👥 Análises por Perfil Clínico")

# Sexo
df_sexo = df_filt.groupby(['MES_ANO', 'SEXO'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_sexo, 'SEXO', "Tempo Médio por Sexo"), use_container_width=True)

# Raça/Cor
df_raca = df_filt.groupby(['MES_ANO', 'RACA_COR'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_raca, 'RACA_COR', "Tempo Médio por Raça/Cor"), use_container_width=True)

# Faixa Etária
df_faixa = df_filt.groupby(['MES_ANO', 'FAIXA_ETARIA'])['TEMPO_ESPERA_DIAS'].mean().reset_index()
st.plotly_chart(grafico_temporal(df_faixa, 'FAIXA_ETARIA', "Tempo Médio por Faixa Etária"), use_container_width=True)
