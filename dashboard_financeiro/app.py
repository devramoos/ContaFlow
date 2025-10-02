import pandas as pd
import plotly.express as px
import streamlit as st


# --- Configuração da Página ---
st.set_page_config(
+    page_title="Dashboard Financeiro",
+    page_icon="📊",
+    layout="wide",
+)
+
+
+# --- Funções Auxiliares ---
+@st.cache_data
+def carregar_dados(arquivo):
+    """Lê e processa o arquivo CSV do balancete, com tratamento de codificação."""
+    try:
+        df = pd.read_csv(
+            arquivo,
+            sep=";",
+            header=2,
+            decimal=",",
+            encoding="latin-1",
+        )
+        df.dropna(axis=1, how="all", inplace=True)
+
+        if "Classificação" not in df.columns or "Código" not in df.columns:
+            st.error(
+                "As colunas 'Classificação' e/ou 'Código' não foram encontradas. "
+                "Verifique o cabeçalho do arquivo."
+            )
+            return None
+
+        df["Classificação"] = df["Classificação"].astype(str)
+        df["Código"] = df["Código"].astype(str)
+
+        colunas_financeiras = ["Saldo Anterior", "Débito", "Crédito", "Saldo Atual"]
+        for coluna in colunas_financeiras:
+            if coluna in df.columns:
+                df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0)
+            else:
+                st.warning(
+                    f"A coluna '{coluna}' não foi encontrada. Os cálculos podem ser afetados."
+                )
+
+        return df
+    except Exception as exc:  # pragma: no cover - tratamento específico do Streamlit
+        st.error(f"Erro ao processar o arquivo: {exc}")
+        return None
+
+
+# --- Título do Dashboard ---
+st.title("📊 Dashboard de Análise Financeira")
+st.markdown("Faça o upload do seu balancete em formato CSV para visualizar os dados.")
+
+# --- Upload do Arquivo ---
+arquivo_carregado = st.file_uploader(
+    "Selecione o arquivo CSV do balancete",
+    type=["csv"],
+)
+
+if arquivo_carregado:
+    df = carregar_dados(arquivo_carregado)
+
+    if df is not None and not df.empty:
+        st.success("Arquivo carregado e processado com sucesso!")
+
+        # --- Cálculo e Exibição de KPIs ---
+        st.header("Indicadores Chave de Performance (KPIs)")
+
+        df_despesas_kpi = df[df["Classificação"].str.startswith("4", na=False)].copy()
+        if not df_despesas_kpi.empty:
+            tamanho_max_desp = df_despesas_kpi["Classificação"].str.len().max()
+            custos_despesas = df_despesas_kpi[
+                df_despesas_kpi["Classificação"].str.len() == tamanho_max_desp
+            ]["Saldo Atual"].sum()
+        else:
+            custos_despesas = 0
+
+        df_receitas_kpi = df[df["Classificação"].str.startswith("3", na=False)].copy()
+        if not df_receitas_kpi.empty:
+            tamanho_max_rec = df_receitas_kpi["Classificação"].str.len().max()
+            receita_liquida = df_receitas_kpi[
+                df_receitas_kpi["Classificação"].str.len() == tamanho_max_rec
+            ]["Saldo Atual"].sum()
+        else:
+            receita_liquida = 0
+
+        col1, col2 = st.columns(2)
+        with col1:
+            st.metric(
+                label="Receita Líquida (soma das analíticas)",
+                value=f"R$ {receita_liquida:,.2f}",
+            )
+        with col2:
+            st.metric(
+                label="Custos e Despesas (soma das analíticas)",
+                value=f"R$ {custos_despesas:,.2f}",
+            )
+
+        st.markdown("---")
+
+        # --- Criação de Gráficos ---
+        st.header("Visualizações Gráficas")
+
+        col_grafico1, col_grafico2 = st.columns(2)
+
+        with col_grafico1:
+            st.subheader("Saldo dos Grandes Grupos")
+            contas_principais = ["1", "2", "3", "4"]
+            df_grupos = df[df["Classificação"].isin(contas_principais)].copy()
+            mapeamento_grupos = {
+                "1": "Ativo",
+                "2": "Passivo",
+                "3": "Receitas",
+                "4": "Despesas",
+            }
+            df_grupos["Nome Grupo"] = df_grupos["Classificação"].map(mapeamento_grupos)
+            fig_grupos = px.bar(
+                df_grupos,
+                x="Nome Grupo",
+                y="Saldo Atual",
+                title="Saldo Atual por Grande Grupo",
+                labels={"Nome Grupo": "Grupo", "Saldo Atual": "Saldo (R$)"},
+                color="Nome Grupo",
+                text_auto=".2s",
+            )
+            fig_grupos.update_layout(showlegend=False)
+            st.plotly_chart(fig_grupos, use_container_width=True)
+
+        with col_grafico2:
+            st.subheader("Composição Patrimonial")
+
+            pie_data_list = []
+
+            df_ativo = df[df["Classificação"] == "1"].head(1)
+            if not df_ativo.empty:
+                pie_data_list.append(
+                    df_ativo[["Descrição da conta", "Saldo Atual"]].to_dict("records")[0]
+                )
+
+            df_passivo = df[df["Classificação"] == "2"].head(1)
+            if not df_passivo.empty:
+                pie_data_list.append(
+                    df_passivo[["Descrição da conta", "Saldo Atual"]].to_dict("records")[0]
+                )
+
+            df_antecip_socios = df[
+                (df["Código"] == "80") & (df["Classificação"] == "1.2.2.04")
+            ].head(1)
+            if not df_antecip_socios.empty:
+                pie_data_list.append(
+                    df_antecip_socios[["Descrição da conta", "Saldo Atual"]].to_dict("records")[0]
+                )
+            else:
+                st.warning(
+                    "Conta 'Antecipação dos Sócios' (Cód: 80, Class: 1.2.2.04) não encontrada."
+                )
+
+            df_adiant_clientes = df[
+                (df["Código"] == "535")
+                & (df["Classificação"] == "2.1.6.01.001")
+            ].head(1)
+            if not df_adiant_clientes.empty:
+                pie_data_list.append(
+                    df_adiant_clientes[["Descrição da conta", "Saldo Atual"]].to_dict("records")[0]
+                )
+            else:
+                st.warning(
+                    "Conta 'Adiantamento de Clientes' (Cód: 535, Class: 2.1.6.01.001) não encontrada."
+                )
+
+            valor_pl_base = df[df["Classificação"].str.startswith("2.3", na=False)][
+                "Saldo Atual"
+            ].sum()
+            valor_receitas = df[df["Classificação"].str.startswith("3", na=False)][
+                "Saldo Atual"
+            ].sum()
+            valor_despesas = df[df["Classificação"].str.startswith("4", na=False)][
+                "Saldo Atual"
+            ].sum()
+            valor_total_pl = valor_pl_base + valor_receitas + valor_despesas
+            pie_data_list.append(
+                {
+                    "Descrição da conta": "Patrimônio Líquido (calculado)",
+                    "Saldo Atual": valor_total_pl,
+                }
+            )
+
+            if pie_data_list:
+                df_pie_final = pd.DataFrame(pie_data_list)
+                df_pie_final["Saldo Absoluto"] = df_pie_final["Saldo Atual"].abs()
+                df_pie_final = df_pie_final[df_pie_final["Saldo Absoluto"] > 0]
+
+                if not df_pie_final.empty:
+                    fig_pie = px.pie(
+                        df_pie_final,
+                        names="Descrição da conta",
+                        values="Saldo Absoluto",
+                        title="Composição de Contas Selecionadas",
+                        hole=0.3,
+                    )
+                    fig_pie.update_traces(textinfo="percent+label", textposition="outside")
+                    st.plotly_chart(fig_pie, use_container_width=True)
+                else:
+                    st.warning(
+                        "As contas encontradas para o gráfico de pizza possuem saldo zero."
+                    )
+            else:
+                st.warning("Nenhuma das contas para o gráfico de pizza foi encontrada.")
+
+        st.markdown("---")
+
+        st.subheader("Análise de Despesas por Grupo")
+        df_despesas_full = df[df["Classificação"].str.startswith("4.", na=False)].copy()
+        df_despesas_full["nivel"] = df_despesas_full["Classificação"].str.count("\\.")
+        df_grupos_despesa = df_despesas_full[df_despesas_full["nivel"] == 2]
+
+        if not df_grupos_despesa.empty:
+            fig_despesas_grupo = px.bar(
+                df_grupos_despesa,
+                x="Descrição da conta",
+                y="Saldo Atual",
+                title="Análise de Despesas por Grupo",
+                labels={"Descrição da conta": "Grupo de Despesa", "Saldo Atual": "Saldo (R$)"},
+                text_auto=".2s",
+            )
+            fig_despesas_grupo.update_layout(xaxis={"categoryorder": "total descending"})
+            fig_despesas_grupo.update_xaxes(tickangle=45)
+            st.plotly_chart(fig_despesas_grupo, use_container_width=True)
+        else:
+            st.warning("Não foram encontrados grupos de despesa para exibir no gráfico de análise.")
+
+        st.markdown("---")
+
+        st.subheader("Composição das Despesas por Grupo")
+        if not df_grupos_despesa.empty:
+            df_grupos_despesa["Total"] = "Total de Despesas"
+            fig_stacked_bar = px.bar(
+                df_grupos_despesa,
+                x="Total",
+                y="Saldo Atual",
+                color="Descrição da conta",
+                title="Composição das Despesas por Grupo",
+                labels={"Descrição da conta": "Grupo de Despesa", "Saldo Atual": "Saldo (R$)"},
+            )
+            fig_stacked_bar.update_layout(xaxis_title=None, xaxis_ticks=None)
+            st.plotly_chart(fig_stacked_bar, use_container_width=True)
+        else:
+            st.warning(
+                "Não foram encontrados dados para gerar o gráfico de composição de despesas."
+            )
+
+        st.markdown("---")
+        st.header("Dados do Balancete")
+        st.dataframe(df)
+else:
+    st.info("Aguardando o upload do arquivo CSV.")
 
EOF
)
