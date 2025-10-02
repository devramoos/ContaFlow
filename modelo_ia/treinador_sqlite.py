import pandas as pd
import sqlite3
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from unidecode import unidecode
from pathlib import Path

# --- 1. CONFIGURAÇÕES ---
# ===== CORREÇÃO APLICADA AQUI =====
# Agora, o script procura o banco de dados na mesma pasta em que ele está.
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
NOME_BANCO_DE_DADOS = REPO_ROOT / 'contaflow.db'  # Nome do arquivo do banco de dados SQLite
NOME_BANCO_DE_DADOS_ALTERNATIVO = REPO_ROOT / 'base_de_conhecimento' / 'contaflow.db'
# ==================================

# Nome do "cérebro" da IA que será gerado nesta pasta
NOME_MODELO_IA = BASE_DIR / 'modelo_classificador_avancado.pkl'


def normalizar_texto(texto):
    """Função de limpeza de texto."""
    if not isinstance(texto, str): return ''
    return unidecode(texto).lower().strip()


def treinar_modelo_com_db():
    """
    Lê os dados de treinamento diretamente do banco de dados SQLite
    e treina um modelo de IA robusto.
    """
    print("--- INICIANDO TREINAMENTO AVANÇADO DO MODELO DE IA (VERSÃO BANCO DE DADOS) ---")

    try:
        # Conecta-se ao banco de dados
        caminho_db = NOME_BANCO_DE_DADOS if NOME_BANCO_DE_DADOS.exists() else NOME_BANCO_DE_DADOS_ALTERNATIVO
        if not caminho_db.exists():
            print(
                "ERRO CRÍTICO: Banco de dados não encontrado nos caminhos esperados: "
                f"'{NOME_BANCO_DE_DADOS}' ou '{NOME_BANCO_DE_DADOS_ALTERNATIVO}'."
            )
            print(
                "Por favor, execute o script 'migrador_csv_para_sqlite.py' primeiro e verifique se o .db está em um desses locais.")
            return

        conexao = sqlite3.connect(caminho_db)

        # Carrega a base de treinamento e o plano de contas do banco de dados
        df_treino_real = pd.read_sql_query("SELECT * FROM base_de_treinamento", conexao)
        df_mestre = pd.read_sql_query("SELECT * FROM plano_de_contas", conexao)

        conexao.close()

        df_treino_real.dropna(subset=['descricao', 'codigo_correto'], inplace=True)
        print(f" -> {len(df_treino_real)} exemplos reais carregados do banco de dados.")

        df_mestre.dropna(subset=['subgrupo', 'codigo'], inplace=True)
        print(f" -> {len(df_mestre)} contas oficiais carregadas do banco de dados.")

        # Junta os exemplos do mundo real com os nomes oficiais do plano de contas
        exemplos_reais = df_treino_real.rename(columns={'descricao': 'texto', 'codigo_correto': 'codigo'})
        exemplos_oficiais = df_mestre[['subgrupo', 'codigo']].rename(columns={'subgrupo': 'texto'})

        df_treino_completo = pd.concat([exemplos_reais, exemplos_oficiais], ignore_index=True)
        print(f" -> Total de {len(df_treino_completo)} exemplos para treinamento.")

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

    print(" -> Treinando o modelo com dados do banco de dados...")
    pipeline_ia.fit(X_treino, y_treino)
    joblib.dump(pipeline_ia, NOME_MODELO_IA)

    print(f"\n✅ SUCESSO! O modelo de IA foi treinado com os dados centralizados e está mais inteligente!")
    print(f"   O novo cérebro da IA está salvo em: '{NOME_MODELO_IA}'")


if __name__ == "__main__":
    # Verifica se as bibliotecas necessárias estão instaladas
    try:
        import sklearn
        from unidecode import unidecode
    except ImportError as e:
        print(f"ERRO: Biblioteca '{e.name}' não está instalada.")
        print("Por favor, execute no seu terminal: pip install scikit-learn unidecode")
    else:
        treinar_modelo_com_db()