# 💰 Projeto de Classificação Financeira — ContaFlow

Este projeto tem como objetivo **automatizar a classificação de lançamentos financeiros** (fluxos de caixa, extratos e planilhas) utilizando **Python, bancos de dados SQLite e modelos de Inteligência Artificial**.  

A solução foi pensada para:  
- Organizar dados brutos vindos de planilhas e arquivos CSV.  
- Classificar automaticamente os lançamentos em categorias financeiras pré-definidas.  
- Permitir consultas via banco de dados SQLite.  
- Oferecer modelos treinados que podem ser atualizados conforme novos dados são inseridos.  


---

## 📂 Estrutura do Projeto

```text
📁 Base de dados/
│── 📜 app.py                      → Script principal da aplicação
│── 📜 contaflow.db                → Banco de dados SQLite com registros processados
│── 🖼️ favicon-32x32.png           → Ícone do projeto
│── 📜 holograma.py                → Geração da visualização da estrutura (Holograma)
│── 📜 README.md                   → Documentação do projeto
│── ⚙️ run_bot.bat                 → Automação para execução rápida do sistema
│
├── 📁 arquivos_classificados/     # Dados já processados
│   └── 📑 classificado_fluxo_de_caixa_diversos.csv
│
├── 📁 arquivos_para_classificar/  # Dados brutos
│   ├── 📑 fluxo_de_caixa_diversos.csv
│   ├── 📑 fluxo_caixa_entrada.csv
│   ├── 📑 fluxo_caixa_para_ia.csv
│   └── 📊 FLUXO_BANCOS_Abril_novo_categoria.xlsx
│
├── 📁 base_de_conhecimento/       # Dados de apoio e scripts auxiliares
│   ├── 📑 base_de_treinamento_ia.csv  → Conjunto de dados para treinar modelos
│   ├── 📑 plano_de_contas_mestre.csv → Estrutura de categorias padrão
│   ├── 📑 plano_de_contas_pcpl.csv   → Estrutura alternativa de contas
│   ├── ⚙️ unificador_sqlite.py       → Script de unificação de bases SQLite
│   ├── ⚙️ migrador_csv_para_sqlite.py→ Conversão de CSVs para o banco de dados
│   └── 📁 gerenciamento_db/          → Scripts especializados de banco
│
├── 📁 modelo_ia/                  # Inteligência Artificial
│   ├── ⚙️ classificador_sqlite.py     → Classificação via banco de dados
│   ├── ⚙️ treinador_sqlite.py         → Treinamento de modelos baseado em novos dados
│   └── 🤖 modelo_classificador_avancado.pkl → Modelo treinado persistido
│
└── 📁 __pycache__/                # Cache gerado automaticamente pelo Python
```

---

## ⚙️ Funcionamento do Projeto

### 1️⃣ Entrada de dados
Os arquivos brutos (fluxos de caixa, extratos e planilhas em `.csv` ou `.xlsx`) são armazenados na pasta `arquivos_para_classificar/`.  
Esses dados representam lançamentos financeiros sem classificação padronizada.

### 2️⃣ Pré-processamento
Os scripts em `base_de_conhecimento/` limpam, organizam e migram os dados.  
- `migrador_csv_para_sqlite.py` transforma os arquivos CSV em registros no banco SQLite (`contaflow.db`).  
- O plano de contas mestre garante padronização das categorias.

### 3️⃣ Classificação
O modelo de Inteligência Artificial (em `modelo_ia/`) é treinado com base em dados históricos (`base_de_treinamento_ia.csv`).  
- `classificador_sqlite.py` aplica o modelo sobre os novos lançamentos.  
- A classificação é gravada em `arquivos_classificados/` e também no banco `contaflow.db`.

### 4️⃣ Saída de dados
Os resultados podem ser exportados em CSV (dados classificados) ou consultados diretamente no banco SQLite, permitindo filtros e relatórios personalizados.

---

## 🚀 Como Executar

Clone o repositório:

```bash
git clone https://github.com/seu-usuario/projeto_classificacao_financeira.git
cd projeto_classificacao_financeira
```

Crie um ambiente virtual e instale as dependências:

```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
pip install -r requirements.txt
```

Organize seus arquivos:  
- Coloque planilhas/CSVs em `arquivos_para_classificar/`.  
- Confirme que os planos de contas estão em `base_de_conhecimento/`.  

Rode o pipeline de classificação:

```bash
python app.py
```

Resultado:  
- Arquivos processados estarão em `arquivos_classificados/`.  
- Banco atualizado estará em `contaflow.db`.  

---

## 🧠 Inteligência Artificial

O modelo é baseado em **aprendizado supervisionado**, treinado em históricos financeiros.  

Pode ser re-treinado usando:

```bash
python modelo_ia/treinador_sqlite.py
```

O modelo salvo (`modelo_classificador_avancado.pkl`) garante reuso sem necessidade de treinar a cada execução.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**  
- **SQLite** (banco de dados leve e local)  
- **Pandas / NumPy** (manipulação de dados)  
- **Scikit-learn** (treinamento e classificação IA)  
- **OpenPyXL** (manipulação de planilhas Excel)  
- **Batch scripts (.bat)** para automação no Windows  

---

## 📌 Possíveis Melhorias Futuras

- Dashboard web para visualização dos resultados.  
- Integração com APIs bancárias para importação automática.  
- Suporte a múltiplos modelos de IA em paralelo.  
- Exportação para relatórios em PDF diretamente.  

---

## 👨‍💻 Autor

Desenvolvido por **Rodrigo Ramos** — projeto de automação e inteligência financeira.
