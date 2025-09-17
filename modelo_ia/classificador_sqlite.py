import pandas as pd
import sqlite3
import os
import joblib
from unidecode import unidecode
import sys

# --- 1. CONFIGURAÇÕES ---
PASTA_RAIZ_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CAMINHO_BANCO_DE_DADOS = os.path.join(PASTA_RAIZ_PROJETO, 'contaflow.db')
PASTA_ENTRADA = os.path.join(PASTA_RAIZ_PROJETO, 'arquivos_para_classificar')
PASTA_SAIDA = os.path.join(PASTA_RAIZ_PROJETO, 'arquivos_classificados')
NOME_MODELO_IA = 'modelo_classificador_avancado.pkl'


def ler_csv_com_fallback(caminho_arquivo):
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    separators = [';', ',']
    for enc in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(caminho_arquivo, sep=sep, engine='python', encoding=enc)
                if df.shape[1] > 1:
                    print(f" -> Ficheiro '{os.path.basename(caminho_arquivo)}' lido com sucesso.")
                    return df
            except Exception:
                continue
    raise ValueError(f"Não foi possível ler o ficheiro '{caminho_arquivo}'.")


def normalizar_texto(texto):
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def limpar_e_converter_valor(valor):
    if pd.isna(valor): return 0.0
    if isinstance(valor, (int, float)): return valor
    s = str(valor).strip().replace('R$', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


def classificar_com_db(nome_do_arquivo_para_classificar):
    print("--- INICIANDO CLASSIFICADOR HÍBRIDO (VERSÃO BANCO DE DADOS) ---")
    print(f" -> Ficheiro alvo: {nome_do_arquivo_para_classificar}")

    try:
        caminho_script = os.path.dirname(__file__)
        caminho_modelo = os.path.join(caminho_script, NOME_MODELO_IA)
        modelo_ia = joblib.load(caminho_modelo)
        print(f" -> Modelo de IA carregado de: {caminho_modelo}")

        if not os.path.exists(CAMINHO_BANCO_DE_DADOS):
            raise FileNotFoundError(f"Banco de dados '{CAMINHO_BANCO_DE_DADOS}' não encontrado.")
        conexao = sqlite3.connect(CAMINHO_BANCO_DE_DADOS)

        df_mestre = pd.read_sql_query("SELECT * FROM plano_de_contas", conexao)
        print(" -> Base de conhecimento carregada do banco de dados.")

        caminho_arquivo_entrada = os.path.join(PASTA_ENTRADA, nome_do_arquivo_para_classificar)
        df_fluxo = ler_csv_com_fallback(caminho_arquivo_entrada)

    except Exception as e:
        print(f"ERRO CRÍTICO no carregamento: {e}")
        return None  # Retorna None em caso de erro

    # ... (O resto do seu código de classificação continua o mesmo) ...
    df_mestre.columns = [normalizar_texto(col) for col in df_mestre.columns]
    df_fluxo.columns = [normalizar_texto(col) for col in df_fluxo.columns]
    df_fluxo.rename(columns={'subcategoria': 'subgrupo', 'categoria': 'grupo'}, inplace=True)
    mapa_regras = pd.Series(df_mestre.codigo.values, index=df_mestre['subgrupo'].apply(normalizar_texto)).to_dict()
    mapa_detalhes = df_mestre.drop_duplicates(subset=['codigo']).set_index('codigo').to_dict('index')
    df_fluxo['valor'] = df_fluxo['valor'].apply(limpar_e_converter_valor)
    df_fluxo['Codigo'] = None
    df_fluxo['Metodo'] = ''
    df_fluxo['Confianca'] = 0.0
    print("\n -> Iniciando classificação Híbrida...")
    for index, row in df_fluxo.iterrows():
        codigo_encontrado = None
        grupo_cliente = row.get('grupo')
        subgrupo_cliente = row.get('subgrupo')
        if grupo_cliente and pd.notna(grupo_cliente) and subgrupo_cliente and pd.notna(subgrupo_cliente):
            df_mestre['chave_dupla'] = df_mestre['grupo'].apply(normalizar_texto) + '|' + df_mestre['subgrupo'].apply(
                normalizar_texto)
            mapa_regra_dupla = pd.Series(df_mestre.codigo.values, index=df_mestre.chave_dupla).to_dict()
            chave_cliente = normalizar_texto(grupo_cliente) + '|' + normalizar_texto(subgrupo_cliente)
            codigo_encontrado = mapa_regra_dupla.get(chave_cliente)
            if codigo_encontrado:
                df_fluxo.loc[index, 'Metodo'] = 'Regra (Grupo+Subgrupo)'
                df_fluxo.loc[index, 'Confianca'] = 1.0
        if not codigo_encontrado and subgrupo_cliente and pd.notna(subgrupo_cliente):
            codigo_encontrado = mapa_regras.get(normalizar_texto(subgrupo_cliente))
            if codigo_encontrado:
                df_fluxo.loc[index, 'Metodo'] = 'Regra (Subgrupo)'
                df_fluxo.loc[index, 'Confianca'] = 1.0
        if not codigo_encontrado:
            texto_contexto = f"{row.get('grupo', '')} {row.get('subgrupo', '')} {row.get('descricao', '')}"
            texto_normalizado = normalizar_texto(texto_contexto)
            if texto_normalizado:
                codigo_encontrado = modelo_ia.predict([texto_normalizado])[0]
                probabilidade = modelo_ia.predict_proba([texto_normalizado]).max()
                df_fluxo.loc[index, 'Metodo'] = 'IA (Contexto)'
                df_fluxo.loc[index, 'Confianca'] = probabilidade
        df_fluxo.loc[index, 'Codigo'] = codigo_encontrado if codigo_encontrado else 'Falha'
    print(" -> Classificação concluída.")
    df_fluxo.rename(columns={'data': 'Data', 'descricao': 'DescricaoOriginal', 'valor': 'Valor'}, inplace=True)
    df_fluxo['Débito'] = df_fluxo.apply(lambda row: row['Codigo'] if row['Valor'] < 0 else None, axis=1)
    df_fluxo['Crédito'] = df_fluxo.apply(lambda row: row['Codigo'] if row['Valor'] > 0 else None, axis=1)
    df_fluxo['GrupoClassificado'] = df_fluxo['Codigo'].map(lambda x: mapa_detalhes.get(x, {}).get('grupo', 'N/A'))
    df_fluxo['SubgrupoClassificado'] = df_fluxo['Codigo'].map(lambda x: mapa_detalhes.get(x, {}).get('subgrupo', 'N/A'))

    caminho_arquivo_saida = os.path.join(PASTA_SAIDA, f"classificado_{nome_do_arquivo_para_classificar}")
    colunas_finais_csv = ['Data', 'DescricaoOriginal', 'Valor', 'Débito', 'Crédito', 'GrupoClassificado',
                          'SubgrupoClassificado', 'Metodo', 'Confianca']
    df_resultado_csv = df_fluxo[[col for col in colunas_finais_csv if col in df_fluxo.columns]]
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    df_resultado_csv.to_csv(caminho_arquivo_saida, sep=';', decimal=',', index=False, encoding='utf-8-sig')
    print(f"\n -> Ficheiro CSV para o cliente salvo em: '{caminho_arquivo_saida}'")

    colunas_para_db = {'Data': 'data', 'DescricaoOriginal': 'descricao_original', 'Valor': 'valor',
                       'Codigo': 'codigo_classificado', 'Metodo': 'metodo', 'Confianca': 'confianca'}
    df_para_db = df_fluxo.rename(columns=colunas_para_db)
    df_para_db = df_para_db[list(colunas_para_db.values())]
    df_para_db.to_sql('transacoes_classificadas', conexao, if_exists='append', index=False)
    print(f" -> {len(df_para_db)} transações salvas no banco de dados para futura verificação.")
    conexao.close()
    print("\n✅ SUCESSO! Processo concluído.")

    return caminho_arquivo_saida  # <-- ALTERAÇÃO IMPORTANTE: retorna o caminho do ficheiro


if __name__ == "__main__":
    if len(sys.argv) > 1:
        nome_arquivo = sys.argv[1]
        classificar_com_db(nome_arquivo)
    else:
        print("ERRO: Nenhum nome de ficheiro foi fornecido. Use: python classificador_sqlite.py <nome_do_ficheiro.csv>")