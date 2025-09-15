import pandas as pd
from unidecode import unidecode
import os

# --- 1. CONFIGURAÇÕES DE CAMINHOS ---
# ATENÇÃO: Verifique se o caminho para a sua pasta da "Base de Conhecimento" está correto.
PASTA_DA_BASE_DE_CONHECIMENTO = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\base_de_conhecimento'

# Arquivos que devem estar nesta pasta (a pasta do "Motor")
ARQUIVO_FLUXO_CAIXA_ENTRADA = 'fluxo_caixa_entrada.csv'

# Nomes dos arquivos que serão usados ou gerados
NOME_ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'
NOME_ARQUIVO_SAIDA = 'fluxo_caixa_classificado_final.csv'

ARQUIVO_PLANO_CONTAS = os.path.join(PASTA_DA_BASE_DE_CONHECIMENTO, NOME_ARQUIVO_MESTRE)


def normalizar_texto(texto):
    """Converte texto para minúsculas, remove acentos e espaços."""
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def gerar_fluxo_classificado():
    """
    Script final que usa o PLANO DE CONTAS MESTRE de uma pasta externa
    para classificar o fluxo de caixa de qualquer cliente.
    """
    print("--- INICIANDO GERADOR DE FLUXO DE CAIXA CLASSIFICADO ---")

    try:
        print(f" -> Lendo a base de conhecimento de: '{ARQUIVO_PLANO_CONTAS}'")
        df_plano = pd.read_csv(ARQUIVO_PLANO_CONTAS, sep=';', encoding='latin-1')
        print(f" -> Base de conhecimento carregada com {len(df_plano)} contas.")

        df_fluxo = pd.read_csv(ARQUIVO_FLUXO_CAIXA_ENTRADA, sep=';', decimal=',', encoding='latin-1')
        print(f" -> Arquivo de fluxo de caixa ('{ARQUIVO_FLUXO_CAIXA_ENTRADA}') carregado.")
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: O arquivo '{e.filename}' não foi encontrado.")
        print("   Verifique se os nomes e os caminhos das pastas estão corretos.")
        return
    except Exception as e:
        print(f"ERRO CRÍTICO ao ler os arquivos: {e}")
        return

    df_plano.columns = [col.strip() for col in df_plano.columns]
    df_fluxo.columns = [col.strip() for col in df_fluxo.columns]
    mapa_correcao = {'subgrupos': 'subgrupo', 'valor': 'Valor', 'VALOR': 'Valor'}
    df_plano.rename(columns=mapa_correcao, inplace=True)
    df_fluxo.rename(columns=mapa_correcao, inplace=True)

    if 'subgrupo' not in df_plano.columns or 'Codigo' not in df_plano.columns:
        print(f"ERRO: O Plano de Contas Mestre não contém as colunas 'subgrupo' e/ou 'Codigo'.")
        return
    if 'subgrupo' not in df_fluxo.columns or 'Valor' not in df_fluxo.columns:
        print(f"ERRO: Fluxo de Caixa não contém as colunas 'subgrupo' e/ou 'Valor'.")
        return

    print(" -> Classificando transações usando a base de conhecimento mestre...")
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
        else:
            if row['subgrupo'] and pd.notna(row['subgrupo']):
                print(f"Aviso: O subgrupo '{row['subgrupo']}' não foi encontrado na base de conhecimento mestre.")

    df_fluxo[['Débito', 'Crédito']] = df_fluxo[['Débito', 'Crédito']].fillna('')
    colunas_finais = [col for col in ['Débito', 'Crédito', 'Data', 'grupo', 'subgrupo', 'Valor'] if
                      col in df_fluxo.columns]
    df_fluxo = df_fluxo[colunas_finais]
    print(" -> Classificação concluída.")

    # ===== CORREÇÃO APLICADA AQUI =====
    # Adicionamos encoding='utf-8-sig' para garantir que os acentos sejam salvos corretamente
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