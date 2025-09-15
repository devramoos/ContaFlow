import pandas as pd
from unidecode import unidecode
import os

# --- 1. CONFIGURAÇÕES DE CAMINHOS ---
PASTA_DA_BASE_DE_CONHECIMENTO = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\base_de_conhecimento'  # Verifique se o caminho está correto
ARQUIVO_FLUXO_CAIXA_ENTRADA = 'fluxo_caixa_entrada.csv'
NOME_ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'
NOME_ARQUIVO_SAIDA = 'fluxo_caixa_classificado_final.csv'
ARQUIVO_PLANO_CONTAS = os.path.join(PASTA_DA_BASE_DE_CONHECIMENTO, NOME_ARQUIVO_MESTRE)


def ler_csv_com_fallback(caminho_arquivo, decimal_char=None):
    """
    Função robusta que tenta ler um arquivo CSV com diferentes codificações.
    """
    encodings_para_tentar = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    for enc in encodings_para_tentar:
        try:
            if decimal_char:
                return pd.read_csv(caminho_arquivo, sep=';', encoding=enc, decimal=decimal_char)
            else:
                return pd.read_csv(caminho_arquivo, sep=';', encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    raise ValueError(
        f"Não foi possível decodificar ou encontrar o arquivo '{caminho_arquivo}'. Verifique o caminho e a codificação.")


def normalizar_texto(texto):
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def gerar_fluxo_classificado():
    print("--- INICIANDO GERADOR DE FLUXO DE CAIXA CLASSIFICADO ---")

    try:
        print(f" -> Lendo a base de conhecimento de: '{ARQUIVO_PLANO_CONTAS}'")
        df_plano = ler_csv_com_fallback(ARQUIVO_PLANO_CONTAS)
        print(f" -> Base de conhecimento carregada com {len(df_plano)} contas.")

        df_fluxo = ler_csv_com_fallback(ARQUIVO_FLUXO_CAIXA_ENTRADA, decimal_char=',')
        print(f" -> Arquivo de fluxo de caixa carregado.")
    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO CRÍTICO: {e}")
        return

    df_plano.columns = [col.strip() for col in df_plano.columns]
    df_fluxo.columns = [col.strip() for col in df_fluxo.columns]
    df_plano.rename(columns={'subgrupos': 'subgrupo'}, inplace=True)
    df_fluxo.rename(columns={'valor': 'Valor', 'VALOR': 'Valor'}, inplace=True)

    if 'subgrupo' not in df_plano.columns or 'Codigo' not in df_plano.columns:
        print(f"ERRO: O Plano de Contas Mestre não contém as colunas 'subgrupo' e/ou 'Codigo'.")
        return

    print(" -> Classificando transações...")
    df_plano['subgrupo_normalizado'] = df_plano['subgrupo'].apply(normalizar_texto)
    df_plano_sem_duplicatas = df_plano.drop_duplicates(subset=['subgrupo_normalizado'], keep='first')
    mapa_contas = pd.Series(df_plano_sem_duplicatas.Codigo.values,
                            index=df_plano_sem_duplicatas.subgrupo_normalizado).to_dict()
    df_fluxo['Débito'] = pd.Series(dtype='object')
    df_fluxo['Crédito'] = pd.Series(dtype='object')

    for index, row in df_fluxo.iterrows():
        subgrupo_normalizado = normalizar_texto(row['subgrupo'])
        valor_transacao = row['Valor']
        codigo_conta = mapa_contas.get(subgrupo_normalizado)
        if codigo_conta:
            if valor_transacao < 0:
                df_fluxo.loc[index, 'Débito'] = codigo_conta
            elif valor_transacao > 0:
                df_fluxo.loc[index, 'Crédito'] = codigo_conta

    df_fluxo[['Débito', 'Crédito']] = df_fluxo[['Débito', 'Crédito']].fillna('')
    colunas_finais = [col for col in ['Débito', 'Crédito', 'Data', 'grupo', 'subgrupo', 'Valor'] if
                      col in df_fluxo.columns]
    df_fluxo = df_fluxo[colunas_finais]

    # Salva SEMPRE com utf-8-sig para garantir a consistência da saída
    df_fluxo.to_csv(NOME_ARQUIVO_SAIDA, sep=';', decimal=',', index=False, encoding='utf-8-sig')
    print(f"\nArquivo final '{NOME_ARQUIVO_SAIDA}' salvo com sucesso!")
    print("\n--- PROCESSO CONCLUÍDO ---")


if __name__ == "__main__":
    try:
        from unidecode import unidecode
    except ImportError:
        print("ERRO: A biblioteca 'unidecode' não está instalada.")
        print("Por favor, execute no seu terminal: pip install Unidecode")
    else:
        gerar_fluxo_classificado()