import pandas as pd

# --- Arquivos de Entrada e Saída ---
ARQUIVO_PLANO_CONTAS = 'plano_de_contas_pcpl.csv'
ARQUIVO_FLUXO_CAIXA_ENTRADA = 'fluxo_caixa_entrada.csv' # Arquivo com Débito/Crédito vazios
ARQUIVO_FLUXO_CAIXA_SAIDA = 'fluxo_caixa_preenchido_final.csv' # Arquivo final com tudo preenchido

def preencher_lancamentos():
    """
    Lê um fluxo de caixa com colunas de D/C vazias e as preenche
    com os códigos do plano de contas, aceitando códigos duplicados no plano.
    """
    try:
        # Carrega os dois arquivos de base
        df_plano = pd.read_csv(ARQUIVO_PLANO_CONTAS, sep=';', encoding='latin-1')
        df_fluxo = pd.read_csv(ARQUIVO_FLUXO_CAIXA_ENTRADA, sep=';', decimal=',', encoding='latin-1')
        print("Arquivos de entrada carregados com sucesso!")

    except FileNotFoundError as e:
        print(f"ERRO: Arquivo não encontrado! Verifique o nome dos arquivos de entrada.")
        print(e)
        return
    except Exception as e:
        print(f"Ocorreu um erro ao ler os arquivos: {e}")
        return

    # A verificação de subgrupos duplicados é mais importante.
    if df_plano['subgrupo'].duplicated().any():
        print("AVISO: Existem subgrupos duplicados no seu Plano de Contas. O sistema usará a primeira ocorrência encontrada.")

    # Cria um "mapa" para pesquisas rápidas: {subgrupo: Codigo}
    # Ex: {'Vendas de proteses': 504, 'Aluguel de imovel': 740}
    # Se houver subgrupos duplicados, o último a aparecer no CSV será usado.
    mapa_contas = pd.Series(df_plano.Codigo.values, index=df_plano.subgrupo).to_dict()

    # Garante que as colunas Débito e Crédito existam e estejam prontas para preencher
    # Usamos object como tipo para evitar conversões automáticas de tipo pelo pandas
    df_fluxo['Débito'] = pd.Series(dtype='object')
    df_fluxo['Crédito'] = pd.Series(dtype='object')

    print("Iniciando o preenchimento dos lançamentos...")

    # Itera sobre cada linha do fluxo de caixa
    for index, row in df_fluxo.iterrows():
        subgrupo_transacao = row['subgrupo']
        valor_transacao = row['Valor']

        # Procura o código da conta no mapa que criamos
        codigo_conta = mapa_contas.get(subgrupo_transacao)

        if codigo_conta:
            # Lógica de Débito e Crédito baseada no sinal do Valor
            if valor_transacao < 0: # Saída de dinheiro (Despesa/Custo)
                df_fluxo.loc[index, 'Débito'] = codigo_conta
            elif valor_transacao > 0: # Entrada de dinheiro (Receita)
                df_fluxo.loc[index, 'Crédito'] = codigo_conta
        else:
            print(f"Aviso: O subgrupo '{subgrupo_transacao}' não foi encontrado no Plano de Contas. Linha {index+2} do CSV.")

    # Preenche células vazias com '' para um CSV mais limpo
    df_fluxo[['Débito', 'Crédito']] = df_fluxo[['Débito', 'Crédito']].fillna('')

    # Reordena as colunas para ficar igual ao seu exemplo
    df_fluxo = df_fluxo[['Débito', 'Crédito', 'Data', 'subgrupo', 'Valor']]

    print("Preenchimento concluído com sucesso!")

    # Salva o arquivo final
    try:
        df_fluxo.to_csv(ARQUIVO_FLUXO_CAIXA_SAIDA, sep=';', decimal=',', index=False)
        print(f"\nArquivo final salvo como '{ARQUIVO_FLUXO_CAIXA_SAIDA}'")
        print("\n--- Amostra do Resultado Final ---")
        print(df_fluxo.head().to_string())
    except Exception as e:
        print(f"Ocorreu um erro ao salvar o arquivo de saída: {e}")


if __name__ == "__main__":
    preencher_lancamentos()
