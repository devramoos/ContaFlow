import pandas as pd
import sqlite3
import os

# --- 1. CONFIGURAÇÕES ---
# Nomes dos arquivos de entrada (de onde vamos ler os dados)
ARQUIVO_PLANO_MESTRE = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\base_de_conhecimento\plano_de_contas_mestre.csv'
ARQUIVO_TREINAMENTO_IA = r'C:\Users\rodri\Documents\PROGRAMAÇÃO\PYTHON\projeto_classificacao_financeira\Base de dados\modelo_ia\base_de_treinamento_ia.csv'

# Nome do arquivo do banco de dados que será criado
NOME_BANCO_DE_DADOS = 'contaflow.db'

def ler_csv_com_fallback(caminho_arquivo):
    """Lê um CSV tentando diferentes codificações e separadores."""
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    separators = [';', ',', '\t'] # Adiciona TAB como um separador possível
    for enc in encodings:
        for sep in separators:
            try:
                df = pd.read_csv(caminho_arquivo, sep=sep, engine='python', encoding=enc)
                if df.shape[1] > 1:
                    print(f" -> Arquivo '{os.path.basename(caminho_arquivo)}' lido com sucesso.")
                    return df
            except Exception:
                continue
    raise ValueError(f"Não foi possível ler ou decodificar o arquivo '{caminho_arquivo}'.")

def migrar_csv_para_sqlite():
    """
    Lê os arquivos CSV principais e os migra para um banco de dados SQLite.
    Este script deve ser rodado apenas uma vez para criar a base.
    """
    print("--- INICIANDO MIGRAÇÃO DE CSV PARA BANCO DE DADOS SQLITE ---")

    try:
        # Carrega os dados dos arquivos CSV
        df_plano_mestre = ler_csv_com_fallback(ARQUIVO_PLANO_MESTRE)
        df_treinamento = ler_csv_com_fallback(ARQUIVO_TREINAMENTO_IA)

        # Padroniza os nomes das colunas para garantir consistência no banco de dados
        df_plano_mestre.columns = [col.strip().lower() for col in df_plano_mestre.columns]
        df_treinamento.columns = [col.strip().lower() for col in df_treinamento.columns]

        # Renomeia colunas específicas para o padrão do banco de dados
        df_plano_mestre.rename(columns={'movimentacao': 'movimentacao'}, inplace=True) # Exemplo, caso precise
        df_treinamento.rename(columns={'descricaoexemplo': 'descricao', 'codigocorreto': 'codigo_correto'}, inplace=True)

    except (FileNotFoundError, ValueError) as e:
        print(f"ERRO CRÍTICO ao ler arquivos CSV: {e}")
        return

    # --- Conexão com o Banco de Dados ---
    # O arquivo .db será criado na mesma pasta onde o script for executado
    try:
        conexao = sqlite3.connect(NOME_BANCO_DE_DADOS)
        print(f" -> Conexão com o banco de dados '{NOME_BANCO_DE_DADOS}' estabelecida.")

        # --- Inserindo os Dados ---
        # Usa o método to_sql do pandas para criar as tabelas e inserir os dados
        # 'if_exists='replace'' significa que se você rodar o script de novo, ele apagará a tabela antiga e criará uma nova.

        print(" -> Migrando Plano de Contas Mestre...")
        df_plano_mestre.to_sql('plano_de_contas', conexao, if_exists='replace', index=False)

        print(" -> Migrando Base de Treinamento da IA...")
        df_treinamento.to_sql('base_de_treinamento', conexao, if_exists='replace', index=False)

        # Adicional: Criando a tabela para futuras transações
        print(" -> Criando tabela 'transacoes_classificadas' para o futuro...")
        cursor = conexao.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transacoes_classificadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                descricao_original TEXT,
                valor REAL,
                codigo_classificado INTEGER,
                metodo TEXT,
                confianca REAL,
                status TEXT DEFAULT 'para_verificar',
                data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Fecha a conexão com o banco de dados
        conexao.commit()
        conexao.close()

        print(f"\n✅ SUCESSO! O banco de dados '{NOME_BANCO_DE_DADOS}' foi criado e populado com os dados.")
        print("   As tabelas 'plano_de_contas', 'base_de_treinamento' e 'transacoes_classificadas' foram criadas.")

    except Exception as e:
        print(f"ERRO CRÍTICO durante a operação com o banco de dados: {e}")

if __name__ == "__main__":
    migrar_csv_para_sqlite()