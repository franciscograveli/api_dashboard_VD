import os
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, dash_table, Input, Output

# ---------- Dados ----------
pasta = os.path.dirname(os.path.abspath(__file__))
df = pd.read_excel(os.path.join(pasta, '1 - Base de Dados.xlsx'))

# ---------- Tratamento dos dados ----------
df = df.drop(columns='Unnamed: 0')                                    # coluna vazia do Excel
df = df.drop_duplicates().dropna()                                    # linhas repetidas ou vazias
df['Nome_Produto'] = df['Nome_Produto'].str.strip()                   # 'Teclado ' -> 'Teclado'
df['Nome_Cliente'] = df['Nome_Cliente'].str.title()                   # 'amazon' -> 'Amazon'
df['Estado_Cliente'] = df['Estado_Cliente'].replace({'MINAS': 'MG'})  # padroniza a sigla

# Mês em texto, na ordem do calendário (Jan, Fev, ...)
meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
df['Mes'] = pd.Categorical(df['Data_Pedido'].dt.month.map(lambda m: meses[m - 1]),
                           categories=meses, ordered=True)

# Renomeia as colunas para ficarem bonitas nos gráficos (sem "_")
df = df.rename(columns={'Valor_Total_Venda': 'Total de Vendas', 'Mes': 'Mês',
                        'Nome_Representante': 'Representante', 'Nome_Produto': 'Produto',
                        'Nome_Cliente': 'Cliente', 'Estado_Cliente': 'Estado',
                        'Cidade_Cliente': 'Cidade'})

app = Dash(__name__)
server = app.server  # usado na hospedagem (PythonAnywhere)


# ---------- Layout ----------
app.layout = html.Div(className='app', children=[
    html.Div('Relatório de Vendas - 2020', className='header'),
])


if __name__ == '__main__':
    app.run(debug=True)
