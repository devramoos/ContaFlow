import pandas as pd
import os
from unidecode import unidecode

# --- Nomes dos arquivos ---
ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'
ARQUIVO_NOVO_CLIENTE = 'plano_de_contas_pcpl.csv'


def normalizar_texto(texto):
    """Converte texto para minúsculas, remove acentos e espaços para comparação."""
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def unificar_planos_de_contas():
    """
    Versão robusta que lê o plano de contas de um cliente, mesmo com colunas faltando,
    e adiciona as novas contas ao plano de contas mestre, salvando com a codificação correta.
    """
    colunas_mestre_obrigatorias = ['Codigo', 'grupo', 'subgrupo', 'Movimentacao']

    # --- Carregar o Plano de Contas Mestre ---
    if os.path.exists(ARQUIVO_MESTRE):
        df_mestre = pd.read_csv(ARQUIVO_MESTRE, sep=';', encoding='latin-1')
        print(f" -> Plano de Contas Mestre ('{ARQUIVO_MESTRE}') carregado com {len(df_mestre)} contas.")
    else:
        print(f"Aviso: Arquivo '{ARQUIVO_MESTRE}' não encontrado. Um novo será criado.")
        df_mestre = pd.DataFrame(columns=colunas_mestre_obrigatorias)

    # --- Carregar o Plano de Contas do Novo Cliente ---
    try:
        df_cliente = pd.read_csv(ARQUIVO_NOVO_CLIENTE, sep=';', encoding='latin-1')
        print(f" -> Plano de Contas do Cliente ('{ARQUIVO_NOVO_CLIENTE}') carregado com {len(df_cliente)} contas.")
    except FileNotFoundError:
        print(f"ERRO CRÍTICO: O arquivo do novo cliente '{ARQUIVO_NOVO_CLIENTE}' não foi encontrado.")
        return

    # --- Processo de Unificação ---
    df_mestre.columns = [col.strip() for col in df_mestre.columns]
    df_cliente.columns = [col.strip() for col in df_cliente.columns]
    df_cliente.rename(columns={'subgrupos': 'subgrupo'}, inplace=True)

    if 'subgrupo' not in df_cliente.columns:
        print("ERRO CRÍTICO: O arquivo do cliente não contém a coluna essencial 'subgrupo'.")
        return

    subgrupos_mestre_normalizados = set(df_mestre['subgrupo'].apply(normalizar_texto))
    novas_contas_para_adicionar = []

    print("\nComparando planos e procurando por contas novas...")
    for index, row_cliente in df_cliente.iterrows():
        subgrupo_cliente_normalizado = normalizar_texto(row_cliente['subgrupo'])

        if subgrupo_cliente_normalizado not in subgrupos_mestre_normalizados:
            print(f"   -> Nova conta encontrada: '{row_cliente['subgrupo']}'")

            nova_linha = {}
            for col in colunas_mestre_obrigatorias:
                valor = row_cliente.get(col)
                if pd.isna(valor):
                    nova_linha[col] = "A Classificar" if col == 'grupo' else ''
                else:
                    nova_linha[col] = valor

            novas_contas_para_adicionar.append(nova_linha)
            subgrupos_mestre_normalizados.add(subgrupo_cliente_normalizado)

    # --- Salvar o resultado ---
    if novas_contas_para_adicionar:
        df_novas_contas = pd.DataFrame(novas_contas_para_adicionar)
        df_mestre_atualizado = pd.concat([df_mestre, df_novas_contas], ignore_index=True)

        df_mestre_atualizado = df_mestre_atualizado.drop_duplicates().sort_values(by=['grupo', 'subgrupo']).reset_index(
            drop=True)

        # ===== CORREÇÃO APLICADA AQUI =====
        # Adicionamos encoding='utf-8-sig' para garantir que os acentos sejam salvos corretamente
        df_mestre_atualizado.to_csv(ARQUIVO_MESTRE, sep=';', index=False, encoding='utf-8-sig')

        print(
            f"\n✅ SUCESSO! {len(novas_contas_para_adicionar)} nova(s) conta(s) foram adicionadas ao '{ARQUIVO_MESTRE}'.")
        print(f"   O arquivo mestre agora possui um total de {len(df_mestre_atualizado)} contas.")
    else:
        print("\nNenhuma conta nova encontrada. O plano mestre já está atualizado com as contas deste cliente.")


if __name__ == "__main__":
    unificar_planos_de_contas()