import pandas as pd
from unidecode import unidecode

# --- Arquivos de Entrada e Saída ---
ARQUIVO_PLANO_CONTAS = 'plano_de_contas_pcpl.csv'
ARQUIVO_FLUXO_CAIXA_ENTRADA = 'fluxo_caixa_entrada.csv'
ARQUIVO_FLUXO_CAIXA_SAIDA = 'fluxo_caixa_preenchido_final.csv'


def normalizar_texto(texto):
    """Converte texto para minúsculas, remove acentos e espaços."""
    if not isinstance(texto, str):
        return ''
    return unidecode(texto).lower().strip()


def preencher_lancamentos():
    """Script final e robusto que corrige nomes de colunas, normaliza textos e preenche os lançamentos."""
    try:
        df_plano = pd.read_csv(ARQUIVO_PLANO_CONTAS, sep=';', encoding='latin-1')
        df_fluxo = pd.read_csv(ARQUIVO_FLUXO_CAIXA_ENTRADA, sep=';', decimal=',', encoding='latin-1')
        print("Arquivos de entrada carregados com sucesso!")
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: O arquivo '{e.filename}' não foi encontrado.")
        return
    except Exception as e:
        print(f"ERRO CRÍTICO ao ler os arquivos: {e}")
        return

    # ===== ROTINA DE LIMPEZA E CORREÇÃO AUTOMÁTICA DE CABEÇALHOS =====
    print("\n--- Nomes das colunas ANTES da correção ---")
    print(f"Plano de Contas: {df_plano.columns.tolist()}")
    print(f"Fluxo de Caixa: {df_fluxo.columns.tolist()}")

    # 1. Limpeza geral (remove espaços extras)
    df_plano.columns = df_plano.columns.str.strip()
    df_fluxo.columns = df_fluxo.columns.str.strip()

    # 2. Correção automática de nomes comuns
    mapa_correcao = {'subgrupos': 'subgrupo', 'valor': 'Valor', 'VALOR': 'Valor'}
    df_plano.rename(columns=mapa_correcao, inplace=True)
    df_fluxo.rename(columns=mapa_correcao, inplace=True)

    print("\n--- Nomes das colunas DEPOIS da correção ---")
    print(f"Plano de Contas: {df_plano.columns.tolist()}")
    print(f"Fluxo de Caixa: {df_fluxo.columns.tolist()}\n")
    # =================================================================

    # Validação final para garantir que as colunas essenciais existem
    if 'subgrupo' not in df_plano.columns or 'Codigo' not in df_plano.columns:
        print(f"ERRO: Plano de Contas não contém as colunas 'subgrupo' e/ou 'Codigo'.")
        return
    if 'subgrupo' not in df_fluxo.columns or 'Valor' not in df_fluxo.columns:
        print(f"ERRO: Fluxo de Caixa não contém as colunas 'subgrupo' e/ou 'Valor'.")
        return

    # --- Lógica de Normalização e Preenchimento ---
    df_plano['subgrupo_normalizado'] = df_plano['subgrupo'].apply(normalizar_texto)
    df_plano_sem_duplicatas = df_plano.drop_duplicates(subset=['subgrupo_normalizado'], keep='first')
    mapa_contas = pd.Series(df_plano_sem_duplicatas.Codigo.values,
                            index=df_plano_sem_duplicatas.subgrupo_normalizado).to_dict()

    df_fluxo['Débito'] = pd.Series(dtype='object')
    df_fluxo['Crédito'] = pd.Series(dtype='object')

    print("Iniciando o preenchimento (com normalização de texto)...")
    for index, row in df_fluxo.iterrows():
        subgrupo_transacao = row['subgrupo']
        subgrupo_normalizado = normalizar_texto(subgrupo_transacao)
        valor_transacao = row['Valor']
        codigo_conta = mapa_contas.get(subgrupo_normalizado)
        if codigo_conta:
            if valor_transacao < 0:
                df_fluxo.loc[index, 'Débito'] = codigo_conta
            elif valor_transacao > 0:
                df_fluxo.loc[index, 'Crédito'] = codigo_conta
        else:
            if subgrupo_transacao and pd.notna(subgrupo_transacao):
                print(f"Aviso: O subgrupo '{subgrupo_transacao}' não foi encontrado no Plano de Contas.")

    df_fluxo[['Débito', 'Crédito']] = df_fluxo[['Débito', 'Crédito']].fillna('')
    colunas_finais = [col for col in ['Débito', 'Crédito', 'Data', 'grupo', 'subgrupo', 'Valor'] if
                      col in df_fluxo.columns]
    df_fluxo = df_fluxo[colunas_finais]
    print("Preenchimento concluído com sucesso!")

    try:
        df_fluxo.to_csv(ARQUIVO_FLUXO_CAIXA_SAIDA, sep=';', decimal=',', index=False)
        print(f"\nArquivo final salvo como '{ARQUIVO_FLUXO_CAIXA_SAIDA}'")
        print("\n--- Amostra do Resultado Final ---")
        print(df_fluxo.head().to_string())
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo de saída: {e}")


if __name__ == "__main__":
    preencher_lancamentos()