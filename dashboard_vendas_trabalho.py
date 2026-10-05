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


def tema(fig):
    """Fundo transparente, sem legenda e valores em R$."""
    fig.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    fig.update_yaxes(tickprefix='R$ ')
    return fig


# ---------- Item 1: gráficos gerais (sem filtro) ----------
fig_mes = px.area(df.groupby('Mês', observed=True)['Total de Vendas'].sum().reset_index(),
                  x='Mês', y='Total de Vendas', title='Total de Vendas por Mês')

fig_rep = px.bar(df.groupby('Representante')['Total de Vendas'].sum().reset_index(),
                 x='Representante', y='Total de Vendas', title='Total de Vendas por Representante')

fig_regional = px.pie(df.groupby('Regional')['Total de Vendas'].sum().reset_index(),
                      names='Regional', values='Total de Vendas', title='Total de Vendas por Regional')

fig_estado = px.bar(df.groupby('Estado')['Total de Vendas'].sum().reset_index(),
                    x='Estado', y='Total de Vendas', title='Total de Vendas por Estado')

vendas_produto = df.groupby('Produto')['Total de Vendas'].sum().reset_index()
vendas_produto['Total de Vendas'] = vendas_produto['Total de Vendas'].map(lambda v: f'R$ {v:,.0f}'.replace(',', '.'))
tabela_produto = dash_table.DataTable(vendas_produto.to_dict('records'))

# ---------- Layout ----------
app.layout = html.Div(className='app', children=[
    html.Div('Relatório de Vendas - 2020', className='header'),

    # Item 1
    html.Div(className='card', children=[dcc.Graph(figure=tema(fig_mes))]),
    html.Div(className='card', children=[dcc.Graph(figure=tema(fig_rep))]),
    html.Div(className='card', children=[dcc.Graph(figure=fig_regional)]),
    html.Div(className='card', children=[dcc.Graph(figure=tema(fig_estado))]),
    html.Div(className='card', children=[html.H4('Total de Vendas por Produto'), tabela_produto]),

    # Item 2: três gráficos com filtro
    html.Div(className='card', children=[
        dcc.Dropdown(id='filtro-regional', options=sorted(df['Regional'].unique()),
                     placeholder='Filtrar por Regional'),
        dcc.Graph(id='grafico-regional'),
    ]),
    html.Div(className='card', children=[
        dcc.Dropdown(id='filtro-mes', options=meses, placeholder='Filtrar por Mês'),
        dcc.Graph(id='grafico-mes'),
    ]),
    html.Div(className='card', children=[
        dcc.Dropdown(id='filtro-produto', options=sorted(df['Produto'].unique()),
                     placeholder='Filtrar por Produto'),
        dcc.Graph(id='grafico-produto'),
    ]),

    # Item 3: Estado -> Cidade
    html.Div(className='card', children=[
        dcc.Dropdown(id='filtro-estado', options=sorted(df['Estado'].unique()),
                     placeholder='Selecione o Estado'),
        dcc.Dropdown(id='filtro-cidade', placeholder='Selecione a Cidade'),
        dcc.Graph(id='grafico-cidade'),
    ]),
])


# ---------- Item 2: callbacks ----------
@app.callback(Output('grafico-regional', 'figure'), Input('filtro-regional', 'value'))
def grafico_por_regional(regional):
    dados = df if regional is None else df[df['Regional'] == regional]
    dados = dados.groupby('Mês', observed=True)['Total de Vendas'].sum().reset_index()
    return tema(px.line(dados, x='Mês', y='Total de Vendas', title='Vendas por Mês (filtro: Regional)'))


@app.callback(Output('grafico-mes', 'figure'), Input('filtro-mes', 'value'))
def grafico_por_mes(mes):
    dados = df if mes is None else df[df['Mês'] == mes]
    dados = dados.groupby('Representante')['Total de Vendas'].sum().reset_index()
    return tema(px.bar(dados, x='Representante', y='Total de Vendas', title='Vendas por Representante (filtro: Mês)'))


@app.callback(Output('grafico-produto', 'figure'), Input('filtro-produto', 'value'))
def grafico_por_produto(produto):
    dados = df if produto is None else df[df['Produto'] == produto]
    dados = dados.groupby('Cliente')['Total de Vendas'].sum().reset_index()
    return tema(px.bar(dados, x='Cliente', y='Total de Vendas', title='Vendas por Cliente (filtro: Produto)'))


# ---------- Item 3: Estado -> Cidade ----------
@app.callback(Output('filtro-cidade', 'options'), Input('filtro-estado', 'value'))
def atualiza_cidades(estado):
    return sorted(df[df['Estado'] == estado]['Cidade'].unique())


@app.callback(Output('grafico-cidade', 'figure'),
              Input('filtro-estado', 'value'), Input('filtro-cidade', 'value'))
def grafico_cidade(estado, cidade):
    dados = df
    if estado is not None:
        dados = dados[dados['Estado'] == estado]
    if cidade is not None:
        dados = dados[dados['Cidade'] == cidade]
    dados = dados.groupby('Produto')['Total de Vendas'].sum().reset_index()
    return tema(px.bar(dados, x='Produto', y='Total de Vendas', title='Vendas por Produto (filtro: Estado e Cidade)'))


if __name__ == '__main__':
    app.run(debug=True)
