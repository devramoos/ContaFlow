import pandas as pd
import sqlite3
import os
from unidecode import unidecode

# --- 1. CONFIGURAÇÕES ---
# Nome do arquivo do banco de dados (deve estar na mesma pasta)
NOME_BANCO_DE_DADOS = 'contaflow.db'

# Nome do arquivo do novo cliente que queremos "aprender"
ARQUIVO_NOVO_CLIENTE = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\arquivo_para_classificar\plano_de_contas_pcpl.csv'


def ler_csv_com_fallback(caminho_arquivo):
    """Lê um CSV tentando diferentes codificações e separadores."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    separators = [';', ',', '\t']
    for enc in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(caminho_arquivo, sep=sep, engine='python', encoding=enc)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    raise ValueError(f"Não foi possível ler ou decodificar o arquivo '{caminho_arquivo}'.")


def normalizar_texto(texto):
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def unificar_planos_no_db():
    """
    Lê o plano de contas de um cliente e adiciona novas contas válidas
    diretamente no banco de dados SQLite.
    """
    print("--- INICIANDO UNIFICADOR DE PLANOS (VERSÃO BANCO DE DADOS) ---")

    try:
        # --- Conexão com o Banco de Dados ---
        conexao = sqlite3.connect(NOME_BANCO_DE_DADOS)

        # --- Carregar o Plano de Contas Mestre do Banco de Dados ---
        # A cláusula 'try-except' lida com o caso de a tabela ainda não existir
        try:
            df_mestre = pd.read_sql_query("SELECT * FROM plano_de_contas", conexao)
            print(f" -> Plano de Contas Mestre lido do banco de dados com {len(df_mestre)} contas.")
        except pd.io.sql.DatabaseError:
            print("Aviso: Tabela 'plano_de_contas' não encontrada. Será criada uma nova.")
            df_mestre = pd.DataFrame(columns=['codigo', 'grupo', 'subgrupo', 'movimentacao'])

        # --- Carregar o Plano de Contas do Novo Cliente ---
        df_cliente = ler_csv_com_fallback(ARQUIVO_NOVO_CLIENTE)
        print(f" -> Plano de Contas do Cliente carregado com {len(df_cliente)} contas.")

    except Exception as e:
        print(f"ERRO CRÍTICO na leitura dos dados: {e}")
        return

    # --- Processo de Unificação ---
    df_mestre.columns = [normalizar_texto(col) for col in df_mestre.columns]
    df_cliente.columns = [normalizar_texto(col) for col in df_cliente.columns]

    colunas_essenciais = ['codigo', 'subgrupo', 'movimentacao']
    if not all(col in df_cliente.columns for col in colunas_essenciais):
        print(f"ERRO CRÍTICO: Arquivo do cliente não contém as colunas essenciais {colunas_essenciais}.")
        return

    subgrupos_mestre_normalizados = set(df_mestre['subgrupo'].apply(normalizar_texto))
    novas_contas_para_adicionar = []

    print("\nAnalisando e validando contas do arquivo do cliente...")
    for index, row_cliente in df_cliente.iterrows():
        subgrupo_cliente_original = row_cliente.get('subgrupo')
        subgrupo_cliente_normalizado = normalizar_texto(subgrupo_cliente_original)

        if subgrupo_cliente_normalizado and subgrupo_cliente_normalizado not in subgrupos_mestre_normalizados:
            codigo = row_cliente.get('codigo')
            movimentacao = row_cliente.get('movimentacao')

            if pd.notna(codigo) and str(codigo).strip() != '' and pd.notna(movimentacao) and str(
                    movimentacao).strip() != '':
                print(f"   -> Nova conta VÁLIDA encontrada: '{subgrupo_cliente_original}'")
                nova_linha = {
                    'codigo': codigo,
                    'grupo': row_cliente.get('grupo', 'Não Informado'),
                    'subgrupo': subgrupo_cliente_original,
                    'movimentacao': movimentacao
                }
                novas_contas_para_adicionar.append(nova_linha)
                subgrupos_mestre_normalizados.add(subgrupo_cliente_normalizado)

    # --- Salvar o resultado no Banco de Dados ---
    if novas_contas_para_adicionar:
        df_novas_contas = pd.DataFrame(novas_contas_para_adicionar)

        # O método .to_sql com if_exists='append' adiciona as novas linhas sem apagar as antigas
        df_novas_contas.to_sql('plano_de_contas', conexao, if_exists='append', index=False)

        print(f"\n✅ SUCESSO! {len(df_novas_contas)} nova(s) conta(s) foram adicionadas ao banco de dados.")
    else:
        print("\nNenhuma conta nova e válida foi encontrada para adicionar.")

    conexao.close()
    print("\n--- Processo de Unificação Concluído ---")


if __name__ == "__main__":
    unificar_planos_no_db()