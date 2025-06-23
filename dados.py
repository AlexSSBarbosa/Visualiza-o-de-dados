import pandas as pd
import numpy as np
import csv

def criar_chave_composta_robusta(df):
    df_copy = df.copy()
    campos_chave = ['AP_SEXO', 'AP_RACACOR', 'AP_CEPPCN', 'AP_UFNACIO']
    for col in campos_chave:
        df_copy[col] = df_copy[col].astype(str).str.strip().fillna('NA')
    df_copy['CHAVE_COMPOSTA'] = df_copy[campos_chave].agg('_'.join, axis=1)
    return df_copy

print("--- Iniciando a Etapa 1: Carregamento dos Dados ---")
caminho_pasta = './'
arquivo_dialise = f'{caminho_pasta}ATDRS.csv'
arquivo_fav = f'{caminho_pasta}ACFRS.csv'

df_dialise = pd.read_csv(
    arquivo_dialise,
    sep=';',
    header=0,
    encoding='iso-8859-1',
    engine='python',
    quoting=csv.QUOTE_NONE,
    on_bad_lines='warn'
)

df_fav = pd.read_csv(
    arquivo_fav,
    sep=';',
    header=0,
    encoding='iso-8859-1',
    engine='python',
    quoting=csv.QUOTE_NONE,
    on_bad_lines='warn'
)

df_dialise = df_dialise.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)
df_fav = df_fav.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)

print("✔️ Arquivos carregados e limpos com sucesso!")

df_dialise.columns = df_dialise.columns.str.upper().str.strip().str.replace('"', '')
df_fav.columns = df_fav.columns.str.upper().str.strip().str.replace('"', '')

df_dialise_poa = df_dialise[df_dialise['AP_UFMUN'].astype(str).str.strip() == '431490'].copy()
df_fav_poa = df_fav[df_fav['AP_UFMUN'].astype(str).str.strip() == '431490'].copy()

df_dialise_chave = criar_chave_composta_robusta(df_dialise_poa)
df_fav_chave = criar_chave_composta_robusta(df_fav_poa)

df_dialise_chave['DATA_INICIO_DIALISE'] = pd.to_datetime(df_dialise_chave['AP_DTINIC'], format='%Y%m%d', errors='coerce')
df_dialise_chave.dropna(subset=['DATA_INICIO_DIALISE', 'CHAVE_COMPOSTA'], inplace=True)
df_primeira_dialise = df_dialise_chave.loc[df_dialise_chave.groupby('CHAVE_COMPOSTA')['DATA_INICIO_DIALISE'].idxmin()]

df_fav_chave['DATA_FAV'] = pd.to_datetime(df_fav_chave['AP_DTINIC'], format='%Y%m%d', errors='coerce')
df_fav_chave.dropna(subset=['DATA_FAV', 'CHAVE_COMPOSTA'], inplace=True)

df_merged = pd.merge(df_primeira_dialise, df_fav_chave, on='CHAVE_COMPOSTA', how='inner', suffixes=('_DIALISE', '_FAV'))

if not df_merged.empty:
    df_merged['TEMPO_ESPERA_DIAS'] = (df_merged['DATA_FAV'] - df_merged['DATA_INICIO_DIALISE']).dt.days
    df_com_espera = df_merged[df_merged['TEMPO_ESPERA_DIAS'] > 0].copy()
    df_primeira_fav = df_com_espera.loc[df_com_espera.groupby('CHAVE_COMPOSTA')['TEMPO_ESPERA_DIAS'].idxmin()]
    df_primeira_fav['ANO_FAV'] = df_primeira_fav['DATA_FAV'].dt.year
    df_primeira_fav['ANO_INICIO'] = df_primeira_fav['DATA_INICIO_DIALISE'].dt.year
    df_primeira_fav['CRONICO_3_MESES'] = df_primeira_fav['TEMPO_ESPERA_DIAS'] >= 90
    df_final = df_primeira_fav[(df_primeira_fav['ANO_FAV'] >= 2015) & (df_primeira_fav['ANO_FAV'] <= 2024)].copy()
else:
    df_final = pd.DataFrame()

if not df_final.empty:
    df_final.rename(columns={'CHAVE_COMPOSTA': 'ID_PACIENTE_COMPOSTO'}, inplace=True)
    df_final['IDADE'] = pd.to_numeric(df_final['AP_NUIDADE_DIALISE'], errors='coerce')

    faixas_etarias = [18, 30, 45, 60, 120]
    labels_faixas = ['18-30 anos', '31-45 anos', '46-60 anos', '60+ anos']
    df_final['FAIXA_ETARIA'] = pd.cut(df_final['IDADE'], bins=faixas_etarias, labels=labels_faixas, right=False)

    df_final['SEXO'] = df_final['AP_SEXO_DIALISE'].map({'M': 'Masculino', 'F': 'Feminino'})

    mapa_raca = {
        '01': 'Branca', '1': 'Branca', '02': 'Preta', '2': 'Preta',
        '03': 'Parda', '3': 'Parda', '04': 'Amarela', '4': 'Amarela',
        '05': 'Indígena', '5': 'Indígena', '99': 'Não Informada'
    }
    df_final['RACA_COR'] = df_final['AP_RACACOR_DIALISE'].astype(str).str.strip().str.zfill(2).map(mapa_raca).fillna('Não Informada')

    mapa_acesso = {
        '1': 'Fístula Arteriovenosa (FAV)',
        '2': 'Cateter Duplo Lúmen',
        '3': 'Cateter Permanente (Permcath)',
        '4': 'Outros'
    }
    df_final['ACESSO_VASCULAR_INICIAL'] = df_final['ATD_ACEVAS'].astype(str).map(mapa_acesso).fillna('Não Informado')

    if 'AP_CODUNI_DIALISE' not in df_final.columns and 'AP_CODUNI_DIALISE' in df_merged.columns:
        df_final['AP_CODUNI_DIALISE'] = df_merged['AP_CODUNI_DIALISE']

    colunas_finais = {
        'ID_PACIENTE_COMPOSTO': 'ID_PACIENTE_COMPOSTO',
        'DATA_INICIO_DIALISE': 'DATA_INICIO_DIALISE',
        'DATA_FAV': 'DATA_CRIACAO_FAV',
        'TEMPO_ESPERA_DIAS': 'TEMPO_ESPERA_DIAS',
        'ANO_FAV': 'ANO_CRIACAO_FAV',
        'ANO_INICIO': 'ANO_INICIO',
        'CRONICO_3_MESES': 'CRONICO_3_MESES',
        'SEXO': 'SEXO',
        'RACA_COR': 'RACA_COR',
        'IDADE': 'IDADE',
        'FAIXA_ETARIA': 'FAIXA_ETARIA',
        'AP_MUNPCN_DIALISE': 'MUN_RESIDENCIA_COD',
        'ACESSO_VASCULAR_INICIAL': 'ACESSO_VASCULAR_INICIAL',
        'AP_CODUNI_DIALISE': 'COD_UNIDADE_HOSPITALAR'
    }

    if 'AP_CODUNI_DIALISE' not in df_final.columns:
        df_final['AP_CODUNI_DIALISE'] = 'Desconhecido'

    df_para_dashboard = df_final[list(colunas_finais.keys())].rename(columns=colunas_finais)

    caminho_saida = './dados_finais_para_dashboard.csv'
    df_para_dashboard.to_csv(caminho_saida, index=False, encoding='utf-8')
    print(f"\n--- Processo Concluído! ---")
    print(f"Arquivo final salvo em: {caminho_saida}")
else:
    print("\nAVISO: Não foram encontrados pacientes que atendam a todos os critérios. O arquivo final não será gerado.")
