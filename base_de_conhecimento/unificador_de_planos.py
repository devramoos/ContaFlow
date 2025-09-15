import pandas as pd
import os
from unidecode import unidecode

# --- Nomes dos arquivos ---
ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'
ARQUIVO_NOVO_CLIENTE = 'plano_de_contas_pcpl.csv'


def ler_csv_com_fallback(caminho_arquivo):
    """
    Função robusta que tenta ler um arquivo CSV com diferentes codificações.
    """
    encodings_para_tentar = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    for enc in encodings_para_tentar:
        try:
            return pd.read_csv(caminho_arquivo, sep=';', encoding=enc)
        except (UnicodeDecodeError, FileNotFoundError):
            continue
    raise ValueError(f"Não foi possível decodificar ou encontrar o arquivo '{caminho_arquivo}'.")


def normalizar_texto(texto):
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def unificar_planos_com_validacao():
    """
    Versão final que valida contas obrigatórias e preenche campos opcionais
    ausentes (como 'grupo') com um valor padrão.
    """
    colunas_mestre_obrigatorias = ['Codigo', 'grupo', 'subgrupo', 'Movimentacao']

    if os.path.exists(ARQUIVO_MESTRE):
        df_mestre = ler_csv_com_fallback(ARQUIVO_MESTRE)
        print(f" -> Plano de Contas Mestre carregado com {len(df_mestre)} contas.")
    else:
        print(f"Aviso: Arquivo Mestre não encontrado. Um novo será criado.")
        df_mestre = pd.DataFrame(columns=colunas_mestre_obrigatorias)

    try:
        df_cliente = ler_csv_com_fallback(ARQUIVO_NOVO_CLIENTE)
        print(f" -> Plano de Contas do Cliente carregado com {len(df_cliente)} contas.")
    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO CRÍTICO: {e}")
        return

    df_mestre.columns = [col.strip() for col in df_mestre.columns]
    df_cliente.columns = [col.strip() for col in df_cliente.columns]
    df_cliente.rename(columns={'subgrupos': 'subgrupo'}, inplace=True)

    colunas_essenciais_cliente = ['Codigo', 'subgrupo', 'Movimentacao']
    if not all(col in df_cliente.columns for col in colunas_essenciais_cliente):
        print(f"ERRO CRÍTICO: O arquivo do cliente precisa conter as colunas {colunas_essenciais_cliente}.")
        return

    subgrupos_mestre_normalizados = set(df_mestre['subgrupo'].apply(normalizar_texto))
    novas_contas_para_adicionar = []

    print("\nAnalisando e validando contas do arquivo do cliente...")
    for index, row_cliente in df_cliente.iterrows():
        subgrupo_cliente_original = row_cliente.get('subgrupo')
        subgrupo_cliente_normalizado = normalizar_texto(subgrupo_cliente_original)

        if subgrupo_cliente_normalizado and subgrupo_cliente_normalizado not in subgrupos_mestre_normalizados:
            codigo_cliente = row_cliente.get('Codigo')
            movimentacao_cliente = row_cliente.get('Movimentacao')

            if pd.notna(codigo_cliente) and str(codigo_cliente).strip() != '' and pd.notna(
                    movimentacao_cliente) and str(movimentacao_cliente).strip() != '':
                print(f"   -> Nova conta VÁLIDA encontrada: '{subgrupo_cliente_original}'")

                # ===== LÓGICA DE PREENCHIMENTO RESTAURADA AQUI =====
                nova_linha = {}
                for col in colunas_mestre_obrigatorias:
                    # Pega o valor se a coluna existir no arquivo do cliente
                    valor = row_cliente.get(col)
                    # Se não existir ou estiver vazio, preenche com um padrão
                    if pd.isna(valor) or str(valor).strip() == '':
                        # A coluna 'grupo' é opcional e pode ser preenchida
                        if col == 'grupo':
                            nova_linha[col] = "Não Informado"
                        # As outras são obrigatórias, mas deixamos vazio por segurança
                        else:
                            nova_linha[col] = ''
                    else:
                        nova_linha[col] = valor

                # Garante que o subgrupo original seja mantido
                nova_linha['subgrupo'] = subgrupo_cliente_original

                novas_contas_para_adicionar.append(nova_linha)
                subgrupos_mestre_normalizados.add(subgrupo_cliente_normalizado)

    if novas_contas_para_adicionar:
        df_novas_contas = pd.DataFrame(novas_contas_para_adicionar)
        df_mestre_atualizado = pd.concat([df_mestre, df_novas_contas], ignore_index=True)
        df_mestre_atualizado.drop_duplicates(subset=['subgrupo'], inplace=True)
        df_mestre_atualizado.sort_values(by=['grupo', 'subgrupo'], inplace=True, na_position='first')

        df_mestre_atualizado.to_csv(ARQUIVO_MESTRE, sep=';', index=False, encoding='utf-8-sig')
        print(
            f"\n✅ SUCESSO! {len(novas_contas_para_adicionar)} nova(s) conta(s) foram adicionadas ao '{ARQUIVO_MESTRE}'.")
    else:
        print("\nNenhuma conta nova e válida foi encontrada para adicionar.")


if __name__ == "__main__":
    unificar_planos_com_validacao()