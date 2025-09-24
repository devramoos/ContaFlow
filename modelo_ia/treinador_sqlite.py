import pandas as pd
import sqlite3
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from unidecode import unidecode

# --- 1. CONFIGURAÇÕES ---
PASTA_RAIZ_PROJETO = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
CAMINHO_BANCO_DE_DADOS = os.path.join(PASTA_RAIZ_PROJETO, 'contaflow.db')
NOME_MODELO_IA = 'modelo_classificador_avancado.pkl'

# Nomes dos arquivos de treinamento
NOME_ARQUIVO_TREINO_ANTIGO = 'base_de_treinamento_ia.csv'
NOME_ARQUIVO_TREINO_NOVO = 'base_de_treinamento_completa.csv'

CAMINHO_TREINO_ANTIGO = os.path.join(PASTA_RAIZ_PROJETO, 'base_de_conhecimento', NOME_ARQUIVO_TREINO_ANTIGO)
CAMINHO_TREINO_NOVO = os.path.join(PASTA_RAIZ_PROJETO, 'base_de_conhecimento', NOME_ARQUIVO_TREINO_NOVO)


def normalizar_texto(texto):
    """Função de limpeza de texto."""
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def treinar_modelo_com_db():
    """
    Lê dados de MÚLTIPLAS FONTES (método antigo e novo) para treinar um modelo de IA híbrido e mais robusto.
    """
    print("--- INICIANDO TREINAMENTO HÍBRIDO DO MODELO DE IA (MÚLTIPLAS FONTES) ---")
    lista_dfs_treino = []

    try:
        # --- FONTE 1: PLANO DE CONTAS (OFICIAL) ---
        if not os.path.exists(CAMINHO_BANCO_DE_DADOS):
            raise FileNotFoundError(f"ERRO CRÍTICO: Banco de dados '{CAMINHO_BANCO_DE_DADOS}' não encontrado.")
        conexao = sqlite3.connect(CAMINHO_BANCO_DE_DADOS)
        df_mestre = pd.read_sql_query("SELECT * FROM plano_de_contas", conexao)
        conexao.close()
        df_mestre.dropna(subset=['subgrupo', 'codigo'], inplace=True)
        exemplos_oficiais = df_mestre[['subgrupo', 'codigo']].rename(columns={'subgrupo': 'texto'})
        lista_dfs_treino.append(exemplos_oficiais)
        print(f" -> FONTE 1: {len(exemplos_oficiais)} exemplos oficiais carregados do banco de dados.")

        # --- FONTE 2: TREINAMENTO ANTIGO (APENAS DESCRIÇÃO) ---
        if os.path.exists(CAMINHO_TREINO_ANTIGO):
            df_treino_antigo = pd.read_csv(CAMINHO_TREINO_ANTIGO, sep=';', header=0,
                                           names=['DescricaoExemplo', 'CodigoCorreto'], encoding='latin-1')
            df_treino_antigo.dropna(subset=['DescricaoExemplo', 'CodigoCorreto'], inplace=True)
            exemplos_antigos = df_treino_antigo.rename(columns={'DescricaoExemplo': 'texto', 'CodigoCorreto': 'codigo'})
            lista_dfs_treino.append(exemplos_antigos)
            print(
                f" -> FONTE 2: {len(exemplos_antigos)} exemplos (descrição) carregados de '{NOME_ARQUIVO_TREINO_ANTIGO}'.")
        else:
            print(
                f" -> AVISO: Arquivo de treinamento antigo '{NOME_ARQUIVO_TREINO_ANTIGO}' não encontrado. Pulando esta fonte.")

        # --- FONTE 3: TREINAMENTO NOVO (GRUPO + SUBGRUPO + DESCRIÇÃO) ---
        if os.path.exists(CAMINHO_TREINO_NOVO):
            df_treino_novo = pd.read_csv(CAMINHO_TREINO_NOVO, sep=';', encoding='latin-1')

            # ===== CORREÇÃO APLICADA AQUI: Normaliza todos os nomes das colunas =====
            df_treino_novo.columns = [normalizar_texto(col) for col in df_treino_novo.columns]

            # Verifica se as colunas essenciais existem após a normalização
            if 'descricao' in df_treino_novo.columns and 'codigo_correto' in df_treino_novo.columns:
                df_treino_novo.dropna(subset=['descricao', 'codigo_correto'], inplace=True)

                # Pega as colunas de contexto, tratando as que podem não existir
                grupo_texto = df_treino_novo['grupo'].fillna('') if 'grupo' in df_treino_novo.columns else ''
                subgrupo_texto = df_treino_novo['subgrupo'].fillna('') if 'subgrupo' in df_treino_novo.columns else ''
                descricao_texto = df_treino_novo['descricao'].fillna('')

                df_treino_novo['texto'] = grupo_texto + ' ' + subgrupo_texto + ' ' + descricao_texto

                exemplos_novos = df_treino_novo[['texto', 'codigo_correto']].rename(
                    columns={'codigo_correto': 'codigo'})
                lista_dfs_treino.append(exemplos_novos)
                print(
                    f" -> FONTE 3: {len(exemplos_novos)} exemplos (contexto) carregados de '{NOME_ARQUIVO_TREINO_NOVO}'.")
            else:
                print(
                    f" -> AVISO: O arquivo '{NOME_ARQUIVO_TREINO_NOVO}' foi encontrado, mas não contém as colunas 'descricao' e 'codigo_correto' após a normalização. Pulando esta fonte.")
        else:
            print(
                f" -> AVISO: Arquivo de treinamento novo '{NOME_ARQUIVO_TREINO_NOVO}' não encontrado. Pulando esta fonte.")

        # Concatena todos os exemplos em um único DataFrame
        if not lista_dfs_treino:
            print("ERRO CRÍTICO: Nenhuma fonte de dados para treinamento foi encontrada.")
            return

        df_treino_completo = pd.concat(lista_dfs_treino, ignore_index=True)
        print(f"\n -> Total de {len(df_treino_completo)} exemplos combinados para o treinamento.")

    except Exception as e:
        print(f"ERRO CRÍTICO ao preparar os dados de treinamento: {e}")
        return

    # Prepara os dados: a IA vai prever o 'codigo' a partir do 'texto'
    X_treino = df_treino_completo['texto'].apply(normalizar_texto)
    y_treino = df_treino_completo['codigo']

    # Constrói o Pipeline do Modelo
    pipeline_ia = Pipeline([
        ('vectorizer', TfidfVectorizer(ngram_range=(1, 3))),
        ('classifier', LogisticRegression(random_state=42, max_iter=1000, class_weight='balanced'))
    ])

    print(" -> Treinando o modelo com todas as fontes de dados...")
    pipeline_ia.fit(X_treino, y_treino)

    # Salva o modelo treinado na pasta correta
    caminho_modelo_salvo = os.path.join(os.path.dirname(__file__), NOME_MODELO_IA)
    joblib.dump(pipeline_ia, caminho_modelo_salvo)

    print(f"\n✅ SUCESSO! O modelo de IA foi treinado com os dados combinados e está mais inteligente!")
    print(f"   O novo cérebro da IA está salvo em: '{caminho_modelo_salvo}'")


if __name__ == "__main__":
    try:
        import sklearn
        from unidecode import unidecode
    except ImportError as e:
        print(f"ERRO: Biblioteca '{e.name}' não está instalada.")
        print("Por favor, execute no seu terminal: pip install scikit-learn unidecode")
    else:
        treinar_modelo_com_db()