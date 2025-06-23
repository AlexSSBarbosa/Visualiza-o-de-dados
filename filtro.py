import pandas as pd
import streamlit as st

@st.cache_data(hash_funcs={"_io.BufferedReader": hash})
def load_and_filter_data(
    caminho_csv="dados_finais_para_dashboard.csv",
    filtro_acesso_default=True,
    filtro_cronico_default=True,
    anos_selecionados=None,
    meses_selecionados=None,
    filtros_acesso=None
):
    try:
        df = pd.read_csv(
            caminho_csv,
            parse_dates=["DATA_INICIO_DIALISE", "DATA_CRIACAO_FAV"]
        )
    except FileNotFoundError:
        return pd.DataFrame(), [], [], []

    # Colunas auxiliares
    df['ANO_FAV'] = df['DATA_CRIACAO_FAV'].dt.year
    df['MES_FAV'] = df['DATA_CRIACAO_FAV'].dt.month

    # Opções de acesso disponíveis
    opcoes_acesso = df['ACESSO_VASCULAR_INICIAL'].dropna().unique().tolist()

    # Define filtros padrão se não fornecidos
    if filtros_acesso is None:
        filtros_acesso = (
            [ac for ac in opcoes_acesso if "Fístula" in ac]
            if filtro_acesso_default else opcoes_acesso
        )

    # Caso filtro de acesso esteja vazio (sem seleção), retorna DataFrame vazio com colunas certas
    if not filtros_acesso:
        colunas_esperadas = [
            "TEMPO_ESPERA_DIAS", "COD_UNIDADE_HOSPITALAR", "SEXO", "FAIXA_ETARIA",
            "RACA_COR", "ACESSO_VASCULAR_INICIAL", "ANO_FAV", "MES_FAV"
        ]
        df_vazio = pd.DataFrame(columns=colunas_esperadas)
        return df_vazio, opcoes_acesso, [], []

    df_filtrado = df[df['ACESSO_VASCULAR_INICIAL'].isin(filtros_acesso)]

    if filtro_cronico_default:
        df_filtrado = df_filtrado[df_filtrado['CRONICO_3_MESES'] == True]

    # Se vazio após filtro, retornar DataFrame vazio com colunas essenciais
    if df_filtrado.empty:
        colunas_esperadas = [
            "TEMPO_ESPERA_DIAS", "COD_UNIDADE_HOSPITALAR", "SEXO", "FAIXA_ETARIA",
            "RACA_COR", "ACESSO_VASCULAR_INICIAL", "ANO_FAV", "MES_FAV"
        ]
        df_vazio = pd.DataFrame(columns=colunas_esperadas)
        return df_vazio, opcoes_acesso, [], []

    # Filtro por ano
    ano_min = df_filtrado['ANO_FAV'].min()
    ano_max = df_filtrado['ANO_FAV'].max()

    if pd.isna(ano_min) or pd.isna(ano_max):
        anos_disponiveis = []
    else:
        anos_disponiveis = list(range(int(ano_min), int(ano_max) + 1))

    if anos_selecionados is None:
        anos_selecionados = anos_disponiveis

    df_filtrado = df_filtrado[df_filtrado['ANO_FAV'].isin(anos_selecionados)]

    # Filtro por mês
    meses_disponiveis = list(range(1, 13))
    if meses_selecionados is None:
        meses_selecionados = meses_disponiveis

    df_filtrado = df_filtrado[df_filtrado['MES_FAV'].isin(meses_selecionados)]

    # Garante apenas tempos válidos de espera
    df_filtrado = df_filtrado[
        (df_filtrado['TEMPO_ESPERA_DIAS'] >= 0) &
        (df_filtrado['TEMPO_ESPERA_DIAS'] <= 730)
    ]

    return df_filtrado, opcoes_acesso, anos_disponiveis, meses_disponiveis
