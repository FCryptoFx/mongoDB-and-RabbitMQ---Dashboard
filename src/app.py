import dash
from dash import Input, Output, html, dcc

import pymongo

import pandas as pd

import plotly.graph_objects as go

from pathlib import Path

import os
from dotenv import load_dotenv

import requests

from datetime import datetime
from collections import deque


# Load environment variables from the .env file
load_dotenv()

##################################################################################################################
#############################################  CONNECTIONS  ######################################################
##################################################################################################################

# MONGODB
mongo_uri = os.environ.get('MONGODB_URI')
client = pymongo.MongoClient(mongo_uri)

# Go into the database created
mongodb_dbname = os.environ.get('MONGODB_DBNAME').strip()
print(mongodb_dbname)
print(type(mongodb_dbname))

db = client[mongodb_dbname]

# Go into one of database's collection (table)
collections = db.list_collection_names()

# RABBITMQ API
api_url = os.environ.get('RABBITMQ_URL')
auth_username = os.environ.get('RABBITMQ_AUTH_USERNAME')
auth_password = os.environ.get('RABBITMQ_AUTH_PASSWORD')
auth = (auth_username, auth_password)


##################################################################################################################
#############################################  FUNCTIONS  ########################################################
##################################################################################################################

# Create the Dash app
app = dash.Dash(__name__)

# Styles
styles_css_path = Path(__file__).resolve().parent / 'static' / 'styles.css'


############# COLLECTIONS ACTIVITY GRAPH ################
# Función para obtener los datos del gráfico de colecciones
def get_Collections_Number():
    colecciones = db.list_collection_names()
    data = [{'x': colecciones, 'y': []}]

    for coleccion in colecciones:
        collection = db[coleccion]
        cantidad_documentos = collection.count_documents({})
        data[0]['y'].append(cantidad_documentos)

    return data


@app.callback(
    Output('graph-colecciones', 'figure'),
    Input('interval-colecciones', 'n_intervals')
)
def update_Collections_Data(n_intervals):
    data = get_Collections_Number()

    fig1 = {
        'data': data,
        'layout': {
            'title': {
                'text': 'Collections Activity',
                'x': 0.5,  # Alinear el título al centro del gráfico
                'font': {'size': 24, 'color': 'black', 'family': 'Arial'}
            },
            'xaxis': {
                'title': '',
                'tickfont': {'size': 14},
                'linecolor': 'black',  # Color de la línea del eje x
                'linewidth': 1,  # Grosor de la línea del eje x
                'ticks': 'outside',  # Posición de las marcas de los ejes
                'tickcolor': 'black',  # Color de las marcas de los ejes
                'tickwidth': 1,  # Grosor de las marcas de los ejes
                'ticklen': 8  # Longitud de las marcas de los ejes
            },
            'yaxis': {
                'title': 'Transactions',
                'tickfont': {'size': 10},
                'linecolor': 'black',  # Color de la línea del eje y
                'linewidth': 1,  # Grosor de la línea del eje y
                'ticks': 'outside',  # Posición de las marcas de los ejes
                'tickcolor': 'black',  # Color de las marcas de los ejes
                'tickwidth': 1,  # Grosor de las marcas de los ejes
                'ticklen': 8  # Longitud de las marcas de los ejes
            },
            'plot_bgcolor': 'white',  # Cambiar el color de fondo del área de trazado a blanco
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',  # Hacer transparente el color de fondo del área del gráfico
            'margin': {'t': 80, 'b': 80, 'l': 80, 'r': 80}  # Ajustar los márgenes del gráfico
        }
    }

    return fig1


    return fig1


############# TOTAL DOCUMENTS GRAPH ##################
def get_Transactions_Data():
    # Obtiene los datos de todas las colecciones y realiza el cálculo
    # para obtener la cantidad de documentos por día

    # Crea una lista para almacenar los datos
    datos = []

    # Obtiene la lista de nombres de colecciones
    collection_names = db.list_collection_names()

    # Itera sobre las colecciones
    for collection_name in collection_names:
        # Obtiene la colección actual
        collection = db[collection_name]

        # Obtiene los documentos de la colección
        documentos = collection.find()

        # Recorre los documentos y extrae la fecha y hora
        for documento in documentos:
            fecha = documento['createdAt'].date()

            # Verifica si la fecha ya está en la lista de datos
            # Si está, incrementa el contador de documentos para esa fecha
            # Si no está, agrega una nueva entrada a la lista de datos
            encontrado = False
            for dato in datos:
                if dato['Fecha'] == fecha:
                    dato['Documentos'] += 1
                    encontrado = True
                    break
            if not encontrado:
                datos.append({'Fecha': fecha, 'Documentos': 1})

    # Crea un DataFrame de pandas con los datos
    df = pd.DataFrame(datos)

    return df


# Obtener los datos
df = get_Transactions_Data()

# Crear la figura de la gráfica de barras
fig = go.Figure(data=[go.Bar(x=df['Fecha'], y=df['Documentos'])])
fig.update_traces(marker_color='rgb(74, 205,141)')  # Cambiar el color de las barras a rojo
fig.update_traces(marker_line_width=5)  # Cambiar el grosor de las líneas de las barras a 2
fig.update_traces(marker_line_color='rgb(7,20,14)', marker_line_width=1)  # Cambiar el color a azul y el grosor a 1
fig.update_layout(
    title={'text': 'Transactions per day', 'x': 0.5},
    yaxis_title='Transactions',
    title_font=dict(family='Arial', size=24, color='black'),
    xaxis=dict(title_font=dict(family='Arial', size=14, color='rgb(0, 0, 0)')),
    yaxis=dict(title_font=dict(family='Arial', size=14, color='rgb(0, 0, 0)'))
)


############# RABBITMQ QUEUE DATA ##################
def get_queue_info():
    url = api_url + 'api/queues'
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        queues = response.json()
        return queues
    else:
        return []


@app.callback(Output('queue-info-output', 'children'), [Input('interval-component', 'n_intervals')])
def update_queue_info(n):
    queue_info = get_queue_info()
    if queue_info:
        table_header = [html.Tr([html.Th('Queue name', style={'font-size': '25px'}), html.Th('Queued messages', style={'font-size': '25px'})], style={'text-align': 'center'})]
        table_rows = [html.Tr([html.Td(queue['name'], style={'font-size': '40px'}), html.Td(queue['messages'], style={'font-size': '40px'})], style={'text-align': 'center'}) for queue in queue_info]
        table = html.Table(table_header + table_rows, style={'margin': 'auto'})
        return table
    else:
        return html.Div("No se pudo obtener información de las colas.", style={'text-align': 'center'})

############# RABBITMQ QUEUE DATA GRAPH MONITORING ##################
# Establecer el tamaño máximo del histórico de datos
max_data_points = 100

# Crear deque para almacenar los datos históricos
data_points = deque(maxlen=max_data_points)

# Crear la figura inicial del gráfico lineal
fig2 = go.Figure()

# Definir la función para obtener información general
def get_overview_info():
    url = api_url + 'api/overview'
    response = requests.get(url, auth=auth)
    if response.status_code == 200:
        overview = response.json()
        return overview
    else:
        return []

# Definir la función de actualización del gráfico en tiempo real
@app.callback(
    Output('graph-component', 'figure'),
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # Obtener los datos de estado de las colas
    overview_info = get_overview_info()
    if overview_info:
        queue_totals = overview_info.get('queue_totals', {})
        messages = queue_totals.get('messages', 0)
        timestamp = datetime.now()

        # Agregar el punto de datos actual a la lista
        data_points.append((timestamp, messages))

        # Actualizar los datos en el gráfico
        fig2 = go.Figure(data=go.Scatter(
            x=[dp[0] for dp in data_points],
            y=[dp[1] for dp in data_points],
            mode='lines',
            name='Queued messages'
        ))

        # Obtener el máximo valor de mensajes encolados
        max_messages = max([dp[1] for dp in data_points])

        # Ajustar el rango del eje y
        y_axis_range = [0, max_messages * 1.5]  # Ajustar el factor multiplicativo según tus necesidades

        # Establecer el layout del gráfico
        fig2.update_layout(
            title={
                'text': 'Queue Status',
                'x': 0.5,  # Centrar el título horizontalmente
                'y': 0.95  # Posición vertical del título
            },
            yaxis={
                'title': 'Queued Messages',
                'title_standoff': 20,  # Ajustar la separación entre el título y el eje y
                'tickfont': {'size': 12},  # Ajustar el tamaño de las etiquetas del eje y
                'range': y_axis_range # Establecer el rango del eje y
            },
            template='plotly_dark',
            margin={'t': 35, 'b': 10}
        )

        return fig2



"""@app.callback(Output('overview-info-output', 'children'), [Input('interval-component', 'n_intervals')])
def update_overview_info(n):
    overview_info = get_overview_info()
    if overview_info:
        queue_totals = overview_info.get('queue_totals', {})
        children = []
        for key, value in queue_totals.items():
            if isinstance(value, (int, float)):
                formatted_value = "{:,}".format(value)  # Formatear el valor numérico con separadores de miles
                div = html.Div([html.Strong(f"{key}: "), formatted_value], style={'text-align': 'center', 'margin-bottom': '10px'})
            else:
                div = html.Div([html.Strong(f"{key}: "), str(value)], style={'text-align': 'center', 'margin-bottom': '10px'})
            children.append(div)
        return children
    else:
        return html.Div("No se pudo obtener información general.", style={'text-align': 'center'})"""


##################################################################################################################
#############################################  APP LAYOUT  #######################################################
##################################################################################################################


app.layout = html.Div(
    children=[
        html.H1('BlockchainDB ACTIVITY', className='app-title'),
        html.Div(
            className='graphs-container',
            children=[
                dcc.Graph(id='graph-colecciones', className='graph', style={'height': '500px'}),
                dcc.Graph(id='grafica-documentos', figure=fig, className='graph', style={'height': '500px'})
            ]
        ),
        html.Div(
            className='info-container',
            children=[
                html.Div(
                    className='info-column',
                    children=[
                        html.Div(id='queue-info-output', className='info-item', style={'height': '250px'}),
                        dcc.Graph(id='graph-component', className='info-item', style={'height': '250px', 'width': '600px'})
                    ]
                ),
            ]
        ),
        dcc.Interval(id='interval-colecciones', interval=1000, n_intervals=0),
        dcc.Interval(id='interval-component', interval=1000, n_intervals=0),
        html.Link(rel='stylesheet', href='../static/styles.css')
    ]
)


if __name__ == '__main__':
    app.run_server(debug=True)
