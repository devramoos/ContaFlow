import pandas as pd
import os
import joblib
from unidecode import unidecode

# --- CONFIGURAÇÕES ---
PASTA_DA_BASE_DE_CONHECIMENTO = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\base_de_conhecimento'
NOME_ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'
NOME_MODELO_IA = 'modelo_classificador.pkl'
ARQUIVO_ENTRADA_IA = 'fluxo_caixa_para_ia.csv'
ARQUIVO_SAIDA_IA = 'fluxo_caixa_classificado_pela_ia.csv'
LIMITE_CONFIANCA = 0.70


def normalizar_texto(texto):
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def classificar_com_ia():
    print("--- INICIANDO O CLASSIFICADOR INTELIGENTE ---")

    try:
        modelo_ia = joblib.load(NOME_MODELO_IA)
        print(f" -> Modelo de IA ('{NOME_MODELO_IA}') carregado com sucesso.")

        caminho_mestre = os.path.join(PASTA_DA_BASE_DE_CONHECIMENTO, NOME_ARQUIVO_MESTRE)
        df_mestre = pd.read_csv(caminho_mestre, sep=';', encoding='utf-8-sig')
        df_mestre_unico = df_mestre.drop_duplicates(subset=['Codigo'], keep='first')
        mapa_detalhes_conta = df_mestre_unico.set_index('Codigo').to_dict('index')

        # Usamos sep=';' que é o padrão dos seus arquivos
        df_para_classificar = pd.read_csv(ARQUIVO_ENTRADA_IA, sep=';', decimal=',', encoding='latin-1')
        print(f" -> Arquivo '{ARQUIVO_ENTRADA_IA}' carregado com {len(df_para_classificar)} transações.")

    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: O arquivo '{e.filename}' não foi encontrado.")
        return
    except Exception as e:
        print(f"ERRO CRÍTICO: {e}")
        return

    # ===== ROTINA DE LIMPEZA E CORREÇÃO DE CABEÇALHOS (MAIS ROBUSTA) =====
    # 1. Remove colunas vazias ('Unnamed')
    df_para_classificar = df_para_classificar.loc[:, ~df_para_classificar.columns.str.contains('^Unnamed')]

    # 2. Converte todos os nomes de colunas para minúsculo para padronizar a busca
    df_para_classificar.columns = [col.strip().lower() for col in df_para_classificar.columns]

    # 3. Renomeia as colunas padronizadas para o formato que o script espera
    mapa_correcao_final = {
        'descrição': 'Descricao',  # com acento
        'descricao': 'Descricao',  # sem acento
        'historico': 'Descricao',  # sinônimo
        'histórico': 'Descricao',  # sinônimo com acento
        'data': 'Data',
        'valor': 'Valor'
    }
    df_para_classificar.rename(columns=mapa_correcao_final, inplace=True)

    if 'Descricao' not in df_para_classificar.columns or 'Valor' not in df_para_classificar.columns:
        print(
            f"ERRO CRÍTICO: Não foram encontradas as colunas 'Descricao' e/ou 'Valor' no arquivo '{ARQUIVO_ENTRADA_IA}'.")
        print(f"Colunas encontradas após limpeza: {df_para_classificar.columns.tolist()}")
        return
    # =================================================================

    print(" -> Classificando transações usando o modelo de IA...")
    textos_para_prever = df_para_classificar['Descricao'].apply(normalizar_texto)
    codigos_previstos = modelo_ia.predict(textos_para_prever)
    probabilidades = modelo_ia.predict_proba(textos_para_prever).max(axis=1)

    df_para_classificar['Codigo'] = codigos_previstos
    df_para_classificar['ConfiancaIA'] = probabilidades

    df_para_classificar['grupo'] = df_para_classificar['Codigo'].map(
        lambda x: mapa_detalhes_conta.get(x, {}).get('grupo', 'N/A'))
    df_para_classificar['subgrupo'] = df_para_classificar['Codigo'].map(
        lambda x: mapa_detalhes_conta.get(x, {}).get('subgrupo', 'N/A'))

    df_para_classificar['Débito'] = df_para_classificar.apply(lambda row: row['Codigo'] if row['Valor'] < 0 else '',
                                                              axis=1)
    df_para_classificar['Crédito'] = df_para_classificar.apply(lambda row: row['Codigo'] if row['Valor'] > 0 else '',
                                                               axis=1)
    df_para_classificar['Revisar'] = df_para_classificar['ConfiancaIA'] < LIMITE_CONFIANCA

    print(" -> Classificação concluída.")

    colunas_finais = ['Data', 'Descricao', 'Valor', 'Débito', 'Crédito', 'grupo', 'subgrupo', 'ConfiancaIA', 'Revisar']
    df_resultado = df_para_classificar[colunas_finais]
    df_resultado.to_csv(ARQUIVO_SAIDA_IA, sep=';', decimal=',', index=False, encoding='utf-8-sig')

    print(f"\n✅ SUCESSO! O arquivo final foi salvo como '{ARQUIVO_SAIDA_IA}'")


if __name__ == "__main__":
    classificar_com_ia()