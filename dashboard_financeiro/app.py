import math
from typing import Iterable

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard Financeiro",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def carregar_dados(arquivo) -> pd.DataFrame | None:
    """Lê e processa o arquivo CSV do balancete, tratando diferentes cenários."""
    try:
        df = pd.read_csv(
            arquivo,
            sep=";",
            header=2,
            decimal=",",
            encoding="latin-1",
        )
        df.dropna(axis=1, how="all", inplace=True)

        colunas_obrigatorias = {"Classificação", "Código"}
        if not colunas_obrigatorias.issubset(df.columns):
            st.error(
                "As colunas obrigatórias 'Classificação' e 'Código' não foram encontradas. "
                "Verifique o arquivo enviado."
            )
            return None

        df["Classificação"] = df["Classificação"].astype(str).str.strip()
        df["Código"] = df["Código"].astype(str).str.strip()

        colunas_financeiras = ["Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]
        for coluna in colunas_financeiras:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)
            else:
                st.warning(
                    f"A coluna '{coluna}' não foi encontrada. Os cálculos podem ser afetados."
                )

        df["Nível"] = df["Classificação"].str.count(r"\\.") + 1
        return df
    except Exception as exc:  # pragma: no cover - feedback amigável no Streamlit
        st.error(f"Erro ao processar o arquivo: {exc}")
        return None


def formatar_moeda(valor: float) -> str:
    simbolo = "R$"
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return f"{simbolo} 0,00"
    return f"{simbolo} {valor:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")


def agrupar_por_grupo(df: pd.DataFrame, coluna_valor: str) -> pd.DataFrame:
    mapeamento = {"1": "Ativo", "2": "Passivo", "3": "Receitas", "4": "Despesas"}
    df_aux = df[df["Classificação"].str.match(r"^[1-4](?:\\.|$)", na=False)].copy()
    df_aux["Grupo"] = df_aux["Classificação"].str.split(".").str[0]
    df_aux["Nome do Grupo"] = df_aux["Grupo"].map(mapeamento).fillna("Outros")
    agrupado = (
        df_aux.groupby(["Grupo", "Nome do Grupo"], as_index=False)[coluna_valor]
        .sum()
        .sort_values("Grupo")
    )
    return agrupado


def extrair_chave_classificacao(classificacao: str, nivel: int) -> str:
    partes = [p for p in classificacao.split(".") if p]
    return ".".join(partes[:nivel])


def resumir_por_nivel(df: pd.DataFrame, coluna_valor: str, nivel: int) -> pd.DataFrame:
    df_validos = df[df["Classificação"].notna()].copy()
    df_validos["Chave"] = df_validos["Classificação"].apply(
        lambda valor: extrair_chave_classificacao(valor, nivel)
    )
    df_validos = df_validos[df_validos["Chave"].ne("")]

    df_resumo = (
        df_validos.groupby("Chave", as_index=False)[coluna_valor]
        .sum()
        .rename(columns={"Chave": "Classificação"})
    )

    referencias = (
        df_validos.sort_values(
            by="Classificação",
            key=lambda serie: serie.str.len(),
        )
        .drop_duplicates("Chave")
        .set_index("Chave")
    )
    serie_descricoes = referencias.get("Descrição da conta", pd.Series(dtype="object"))
    df_resumo["Descrição da conta"] = df_resumo["Classificação"].map(serie_descricoes)
    df_resumo = (
        df_resumo[["Classificação", "Descrição da conta", coluna_valor]]
        .sort_values("Classificação")
        .reset_index(drop=True)
    )
    return df_resumo


st.title("📊 Dashboard de Análise Financeira")
st.markdown("Faça o upload do seu balancete em formato CSV para visualizar e explorar os dados.")

arquivo_carregado = st.file_uploader(
    "Selecione o arquivo CSV do balancete",
    type=["csv"],
)

if arquivo_carregado:
    df = carregar_dados(arquivo_carregado)

    if df is not None and not df.empty:
        st.success("Arquivo carregado e processado com sucesso!")

        with st.sidebar:
            st.header("Configurações do painel")
            colunas_disponiveis = [
                coluna
                for coluna in ["Saldo Atual", "Saldo Anterior", "Débito", "Crédito"]
                if coluna in df.columns
            ]
            if colunas_disponiveis:
                indice_padrao = (
                    colunas_disponiveis.index("Saldo Atual")
                    if "Saldo Atual" in colunas_disponiveis
                    else 0
                )
                coluna_metricas = st.selectbox(
                    "Coluna financeira de análise",
                    options=colunas_disponiveis,
                    index=indice_padrao,
                )
            else:
                st.warning(
                    "Nenhuma coluna financeira padrão foi identificada. Um campo fictício será utilizado para as análises."
                )
                coluna_metricas = "Saldo Atual"
                if coluna_metricas not in df.columns:
                    df[coluna_metricas] = 0

            opcoes_grupos: Iterable[str] = ("Ativo", "Passivo", "Receitas", "Despesas")
            grupos_selecionados = st.multiselect(
                "Grupos contábeis exibidos",
                options=list(opcoes_grupos),
                default=list(opcoes_grupos),
            )

            nivel_resumo = st.slider(
                "Nível do resumo hierárquico",
                min_value=1,
                max_value=int(df["Nível"].max()),
                value=2,
                help="Controle a profundidade das contas exibidas no resumo tabular.",
            )

            mostrar_dados_originais = st.checkbox(
                "Exibir balancete completo",
                value=False,
            )

        st.header("Indicadores chave de performance (KPIs)")
        df_receitas = df[df["Classificação"].str.startswith("3", na=False)]
        df_despesas = df[df["Classificação"].str.startswith("4", na=False)]

        receita_liquida = df_receitas[coluna_metricas].sum()
        despesas_totais = df_despesas[coluna_metricas].sum()
        resultado_operacional = receita_liquida + despesas_totais

        df_ativo = df[df["Classificação"].str.startswith("1", na=False)]
        df_passivo = df[df["Classificação"].str.startswith("2", na=False)]
        total_ativo = df_ativo[coluna_metricas].sum()
        total_passivo = df_passivo[coluna_metricas].sum()

        col_metricas = st.columns(4)
        col_metricas[0].metric("Receita líquida", formatar_moeda(receita_liquida))
        col_metricas[1].metric("Despesas totais", formatar_moeda(despesas_totais))
        col_metricas[2].metric("Resultado operacional", formatar_moeda(resultado_operacional))
        col_metricas[3].metric("Ativo vs. Passivo", f"{formatar_moeda(total_ativo)} / {formatar_moeda(total_passivo)}")

        st.markdown("---")
        st.header("Visualizações gráficas")

        col_graficos_superiores = st.columns(2)

        with col_graficos_superiores[0]:
            st.subheader("Saldo por grande grupo")
            df_grupos = agrupar_por_grupo(df, coluna_metricas)
            if grupos_selecionados:
                df_grupos = df_grupos[df_grupos["Nome do Grupo"].isin(grupos_selecionados)]
            if not df_grupos.empty:
                fig_grupos = px.bar(
                    df_grupos,
                    x="Nome do Grupo",
                    y=coluna_metricas,
                    color="Nome do Grupo",
                    text_auto=".2s",
                    labels={"Nome do Grupo": "Grupo", coluna_metricas: "Valor (R$)"},
                    title=f"{coluna_metricas} por grande grupo",
                )
                fig_grupos.update_layout(showlegend=False)
                st.plotly_chart(fig_grupos, use_container_width=True)
            else:
                st.info("Nenhum grupo selecionado para exibição.")

        with col_graficos_superiores[1]:
            st.subheader("Distribuição relativa dos grupos")
            if not df_grupos.empty:
                fig_pie = px.pie(
                    df_grupos,
                    names="Nome do Grupo",
                    values=coluna_metricas,
                    hole=0.35,
                    title="Participação percentual",
                )
                fig_pie.update_traces(textposition="outside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Selecione ao menos um grupo para montar o gráfico de pizza.")

        st.subheader("Despesas detalhadas")
        df_despesas_detalhe = df_despesas[df_despesas["Nível"] >= 2].copy()
        if not df_despesas_detalhe.empty:
            df_despesas_detalhe["Grupo principal"] = df_despesas_detalhe["Classificação"].apply(
                lambda valor: extrair_chave_classificacao(valor, 2)
            )
            fig_despesas = px.treemap(
                df_despesas_detalhe,
                path=[px.Constant("Despesas"), "Grupo principal", "Descrição da conta"],
                values=coluna_metricas,
                title="Hierarquia das despesas",
            )
            st.plotly_chart(fig_despesas, use_container_width=True)
        else:
            st.info("Não há dados suficientes para detalhar despesas.")

        st.markdown("---")
        st.header("Resumo tabular das contas")
        df_resumo = resumir_por_nivel(df, coluna_metricas, nivel_resumo)
        if not df_resumo.empty:
            st.dataframe(
                df_resumo.style.format({coluna_metricas: formatar_moeda}),
                use_container_width=True,
            )
            st.download_button(
                "Baixar resumo em CSV",
                data=df_resumo.to_csv(index=False).encode("utf-8"),
                file_name="resumo_balancete.csv",
                mime="text/csv",
            )
        else:
            st.info("Não foi possível gerar o resumo para o nível selecionado.")

        if mostrar_dados_originais:
            st.markdown("---")
            st.header("Balancete completo")
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("Não foi possível interpretar o arquivo enviado. Verifique o formato e tente novamente.")
else:
    st.info("Aguardando o upload do arquivo CSV.")
