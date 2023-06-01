import dash
from dash import Input, Output, html, dcc

import pymongo

import pandas as pd

import plotly.graph_objects as go

from pathlib import Path

import os
from dotenv import load_dotenv

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# MONGODB
mongo_uri = os.environ.get('MONGODB_URI')
client = pymongo.MongoClient(mongo_uri)

# Go into the database created
mongodb_dbname = os.environ.get('MONGODB_DBNAME')
db = client[mongodb_dbname]

# Go into one of database's collection (table)
collections = db.list_collection_names()


##################################################################################################################
##################################################################################################################

# Crear la aplicación Dash
app = dash.Dash(__name__)

styles_css_path = Path(__file__).resolve().parent / 'static' / 'styles.css'

############# COLLECTIONS ACTIVITY ################
# Función para obtener los datos del gráfico de colecciones
def get_Collections_Number():
    colecciones = db.list_collection_names()
    data = [{'x': colecciones, 'y': []}]

    for coleccion in colecciones:
        collection = db[coleccion]
        cantidad_documentos = collection.count_documents({})
        data[0]['y'].append(cantidad_documentos)

    return data


# Función para actualizar el gráfico
@app.callback(
    Output('graph-colecciones', 'figure'),
    Input('interval-colecciones', 'n_intervals')
)
def upddate_Collections_Data(n_intervals):
    data = get_Collections_Number()

    """fig1 = {
        'data': data,
        'layout': {
            'title': 'Colections Activity',
            'xaxis': {'title': ''},
            'yaxis': {'title': 'Transactions'}
        }
    }"""

    fig1 = {
        'data': data,
        'layout': {
            'title': {
                'text': 'Collections Activity',
                'x': 0.5,  # Alinear el título al centro del gráfico
                'font': {'size': 24, 'color': 'black', 'family': 'Arial'}
            },
            'xaxis': {'title': '', 'tickfont': {'size': 14}},
            'yaxis': {'title': 'Transactions', 'tickfont': {'size': 10}},
            'plot_bgcolor': 'lightgray'  # Cambiar el color de fondo del área de trazado a gris claro
        }
    }

    return fig1

############# TOTAL DOCUMENTS ##################
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
fig.update_traces(marker_color='rgb(255, 0, 0)')  # Cambiar el color de las barras a rojo
fig.update_traces(marker_line_width=5)  # Cambiar el grosor de las líneas de las barras a 2
fig.update_traces(marker_line_color='rgb(0, 0, 255)', marker_line_width=1)  # Cambiar el color a azul y el grosor a 1
fig.update_layout(
    title={'text': 'Transactions per day', 'x': 0.5},
    xaxis_title='Date',
    yaxis_title='Transactions',
    title_font=dict(family='Arial', size=24, color='black'),
    xaxis=dict(title_font=dict(family='Arial', size=14, color='rgb(0, 0, 0)')),
    yaxis=dict(title_font=dict(family='Arial', size=14, color='rgb(0, 0, 0)'))
)


#######################################################################################################################
"""# Definir el diseño de la aplicación
app.layout = html.Div(
    children=[
        html.H1('Número de Colecciones en la Base de Datos', style={'textAlign': 'center'}),
        dcc.Graph(id='graph-colecciones'),
        dcc.Interval(id='interval-colecciones', interval=10000, n_intervals=0),

        html.Div([
            html.H1('Gráfica de documentos por día', style={'textAlign': 'center'}),
            dcc.Graph(id='grafica-documentos', figure=fig),
        ])
    ]
)"""


app.layout = html.Div(
    children=[
        html.H1('BlockchainDB ACTIVITY', className='app-title'),
        html.Div(
            className='graphs-container',
            children=[
                dcc.Graph(id='graph-colecciones', className='graph'),
                dcc.Graph(id='grafica-documentos', figure=fig, className='graph')
            ]
        ),
        dcc.Interval(id='interval-colecciones', interval=10000, n_intervals=0),
        html.Link(rel='stylesheet', href='/static/styles.css')
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)
