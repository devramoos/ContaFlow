import pandas as pd
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from unidecode import unidecode

# --- CONFIGURAÇÕES ---
PASTA_DA_BASE_DE_CONHECIMENTO = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\base_de_conhecimento'
NOME_ARQUIVO_MESTRE = 'plano_de_contas_mestre.csv'

# O arquivo que será a "sala de aula" da IA
ARQUIVO_DE_TREINAMENTO = 'base_de_treinamento_ia.csv'

NOME_MODELO_IA = 'modelo_classificador.pkl'


def normalizar_texto(texto):
    """Função de limpeza de texto."""
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def treinar_modelo_avancado():
    """
    Lê a base de treinamento, valida os cabeçalhos e treina um modelo de IA robusto.
    """
    print("--- INICIANDO TREINAMENTO AVANÇADO DO MODELO DE IA ---")

    try:
        # ===== CORREÇÃO APLICADA AQUI =====
        # Mudamos o separador (sep) de volta para ';' para ler o arquivo de treinamento corretamente.
        df_treino = pd.read_csv(ARQUIVO_DE_TREINAMENTO, sep=';', encoding='latin-1')
        print(f" -> Base de treinamento ('{ARQUIVO_DE_TREINAMENTO}') carregada.")

        # Rotina de limpeza e correção de cabeçalhos
        df_treino.columns = [col.strip().lower() for col in df_treino.columns]  # Padroniza para minúsculas
        mapa_correcao = {
            'descricaoexemplo': 'DescricaoExemplo',
            'descriçãoexemplo': 'DescricaoExemplo',
            'codigocorreto': 'CodigoCorreto',
            'código correto': 'CodigoCorreto'
        }
        df_treino.rename(columns=mapa_correcao, inplace=True)

        colunas_essenciais = ['DescricaoExemplo', 'CodigoCorreto']
        if not all(col in df_treino.columns for col in colunas_essenciais):
            print(
                f"ERRO CRÍTICO: O arquivo '{ARQUIVO_DE_TREINAMENTO}' precisa ter as colunas 'DescricaoExemplo' e 'CodigoCorreto'.")
            print(f"Colunas encontradas após limpeza: {df_treino.columns.tolist()}")
            return
        # =========================================================

        df_treino.dropna(subset=['DescricaoExemplo', 'CodigoCorreto'], inplace=True)
        print(f" -> Encontrados {len(df_treino)} exemplos de treinamento válidos.")

        # Carrega o plano de contas mestre para adicionar seus subgrupos como exemplos
        caminho_mestre = os.path.join(PASTA_DA_BASE_DE_CONHECIMENTO, NOME_ARQUIVO_MESTRE)
        df_mestre = pd.read_csv(caminho_mestre, sep=';', encoding='utf-8-sig')
        df_mestre.dropna(subset=['subgrupo', 'Codigo'], inplace=True)

        # Junta os exemplos do mundo real com os nomes oficiais do plano de contas
        exemplos_reais = df_treino.rename(columns={'DescricaoExemplo': 'texto', 'CodigoCorreto': 'codigo'})
        exemplos_oficiais = df_mestre[['subgrupo', 'Codigo']].rename(columns={'subgrupo': 'texto', 'Codigo': 'codigo'})

        df_treino_completo = pd.concat([exemplos_reais, exemplos_oficiais], ignore_index=True)
        print(f" -> Total de {len(df_treino_completo)} exemplos de treinamento (reais + oficiais).")

    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO: O arquivo '{e.filename}' não foi encontrado. O treinamento não pode continuar.")
        return
    except Exception as e:
        print(f"ERRO CRÍTICO ao processar os arquivos de treinamento: {e}")
        return

    # Prepara os dados: a IA vai prever o 'codigo' a partir do 'texto'
    X_treino = df_treino_completo['texto'].apply(normalizar_texto)
    y_treino = df_treino_completo['codigo']

    # Constrói o Pipeline do Modelo
    pipeline_ia = Pipeline([
        ('vectorizer', TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'))
    ])

    print(" -> Treinando o modelo com os novos dados...")
    pipeline_ia.fit(X_treino, y_treino)

    joblib.dump(pipeline_ia, NOME_MODELO_IA)

    print(f"\n✅ SUCESSO! O modelo de IA foi treinado com a nova base e está mais inteligente!")
    print(f"   O novo cérebro da IA está salvo em: '{NOME_MODELO_IA}'")


if __name__ == "__main__":
    treinar_modelo_avancado()