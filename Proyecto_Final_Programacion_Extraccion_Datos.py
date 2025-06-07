'''
Proyecto Final - Programacion para Extraccion de Datos
integrantes:
    -- De La Cruz Ramirez Jeremy Yael
    -- Ramirez Cardenas Luis Armando
Grupo: 951
Fecha: 08/06/2025
Profesor: Josue Miguel Flores Parra
'''

import logging
import os
import re
import sys
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import mysql.connector
from sqlalchemy import create_engine
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.express as px
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy.exc import OperationalError
from mysql.connector import Error
from tkinter import *
from tkinter import simpledialog, messagebox
root = Tk()
root.withdraw()
import re

# ----------- Aquí van tus funciones originales sin modificar -----------
"""
En la siguiente seccion del codigo la actividad a realizar es la extraccion de datos, 
la cual es ingresar a la pagina, navegar por el menu de IMDB e ingresar a la seccion de 
las 250 peliculas mejor valoradas, en donde los datos a extraer son la fecha, la duracion, 
el nombre de la pelicula, el año de realizacion y el puntaje y todos estos datos se ingresan en un dataframe
para su respectiva limpieza
"""
def extraccion():
    driver = ChromeDriverManager().install()
    s = Service(driver)
    opc = Options()
    opc.add_argument("--window-size=1020,1200")
    navegador = webdriver.Chrome(options=opc, service=s)
    navegador.get("https://www.imdb.com/es-es/")
    wait = WebDriverWait(navegador, 10)
    time.sleep(15)

    menu_btn = navegador.find_element(By.CSS_SELECTOR, "label[aria-label='Abrir panel de navegación']")
    menu_btn.click()
    time.sleep(5)

    menu_peliculas = navegador.find_element(By.CSS_SELECTOR, "label[aria-label='Desplegar enlaces de navegación de Películas']")
    menu_peliculas.click()
    time.sleep(2)

    mejores_250_btn = navegador.find_element(By.LINK_TEXT, "Las 250 películas mejor valoradas")
    mejores_250_btn.click()
    time.sleep(5)

    movies_data = {"name_movie": [], "year_movie": [],
                   "score_movie": [], "time_movie": []}

    soup = BeautifulSoup(navegador.page_source, "html.parser")
    datos_paginas = soup.find_all("div", attrs={"class": "sc-4b408797-0 eFrxXF cli-children"})
    if datos_paginas:
        for item in datos_paginas:
            nombre = item.find("h3", attrs={"class": "ipc-title__text"})
            if nombre:
                movies_data["name_movie"].append(f"Pelicula: [{nombre.text.strip()}]")
            else:
                movies_data["name_movie"].append("Nombre de la película no encontrado")

            metadatos = item.find_all("span", attrs={"class": "sc-4b408797-8 iurwGb cli-title-metadata-item"})
            if len(metadatos) >= 1:
                movies_data["year_movie"].append(f"Año: {metadatos[0].text.strip()}")
            else:
                movies_data["year_movie"].append("Año no encontrado")

            if len(metadatos) >= 2:
                movies_data["time_movie"].append(f"Tiempo: {metadatos[1].text.strip()}")
            else:
                movies_data["time_movie"].append("Tiempo no encontrado")

            puntuacion = item.find("span", attrs={"class": "ipc-rating-star--rating"})
            if puntuacion:
                movies_data["score_movie"].append(f"Puntaje: {puntuacion.text.strip()}")
            else:
                movies_data["score_movie"].append("No se encontró puntuación")
    time.sleep(3)
    navegador.close()
    print(movies_data)

    ruta_actual = os.path.dirname(os.path.abspath(__file__))
    nombre_carpeta = "Extraccion de datos"
    ruta_carpeta = os.path.join(ruta_actual, nombre_carpeta)
    os.makedirs(ruta_carpeta, exist_ok=True)
    print(f"Carpeta creada en: {ruta_carpeta}")
    df = pd.DataFrame(movies_data)
    print(df.sample(5))
    df.to_csv("Extraccion de datos/movies.csv")


'''
En esta seccion del codigo lo que se va a hacer es trabajar con el scv movies
y limpiar los datos para dejar las columnas que necesitamos, con estos datos limpio
migraremos a mysql para trabajar en el futuro con ellos
'''
def limpieza_de_los_datos():

    ruta_csv_original = "Extraccion de datos/movies.csv"
    df = pd.read_csv(ruta_csv_original)

    print("Datos originales:")
    print(df.head())

    print("Columnas:", df.columns)

    # Extraer nombre de la película limpio
    df["name_movie"] = df["name_movie"].str.extract(r'Pelicula: \[\d+\. (.+)\]')

    # Reemplazamos valores "Desconocido" por NaN
    df["year_movie"] = df["year_movie"].replace("Desconocido", pd.NA)
    df["score_movie"] = df["score_movie"].replace("Desconocido", pd.NA)
    df["time_movie"] = df["time_movie"].replace("Desconocido", pd.NA)

    # Limpiamos etiquetas
    df["year_movie"] = df["year_movie"].str.replace("Año: ", "", regex=False)
    df["time_movie"] = df["time_movie"].str.replace("Tiempo: ", "", regex=False)
    df["score_movie"] = df["score_movie"].str.replace("Puntaje: ", "", regex=False)

    # Convertimos año y score a número
    df["year_movie"] = pd.to_numeric(df["year_movie"], errors="coerce")
    df["score_movie"] = pd.to_numeric(df["score_movie"].str.replace(',', '.'), errors="coerce")  # Reemplaza coma

    # Función para convertir "2h 30m" en minutos
    def convertir_duracion(duracion):
        try:
            duracion = duracion.lower()
            minutos = 0
            if "h" in duracion:
                partes = duracion.split("h")
                horas = int(partes[0].strip())
                minutos += horas * 60
                if len(partes) > 1 and ("min" in partes[1] or "m" in partes[1]):
                    mins_str = partes[1].strip().replace("min", "").replace("m", "").strip()
                    if mins_str.isdigit():
                        minutos += int(mins_str)
            elif "min" in duracion or "m" in duracion:
                mins_str = duracion.replace("min", "").replace("m", "").strip()
                if mins_str.isdigit():
                    minutos = int(mins_str)
            return minutos
        except Exception as e:
            print(f"Error al convertir duración: {duracion} -> {e}")
            return None

    df["time_movie"] = df["time_movie"].apply(convertir_duracion)

    print(f"Filas antes de limpiar NaNs: {len(df)}")
    df = df[df["year_movie"].notna()]
    df = df[df["score_movie"].notna()]
    df = df[df["time_movie"].notna()]
    print(f"Filas después de limpiar NaNs: {len(df)}")

    ruta_csv_limpio = "Extraccion de datos/movies_limpio.csv"
    df.to_csv(ruta_csv_limpio, index=False)

    print(f"Datos limpios guardados en: {ruta_csv_limpio}")
    print(df.head())


"""
En esta seccion del codigo se tomara el dataframe movies ya con su respectiva limpieza y normalizada y
se migrara como parte del proyecto al programa de MYSQL Workbench, (no si antes hacer conexion) donde el usuario ingresara
su contraseña de su aplicacion para que se realize la conexion directa sin necesidad de tener abierta
la aplicacion, en dado caso de que la contreña sea incorrecta, retornara de nuevo a la seccion de ingresar 
codigo hasta que se ingrese la contraseña correcta
"""
def migrar_a_mysql():
    def convertir_duracion(duracion):
        """Convierte texto como '2h 22min' en minutos (int)"""
        try:
            duracion = duracion.lower()
            total = 0
            horas = re.search(r"(\d+)h", duracion)
            minutos = re.search(r"(\d+)(?:min|m)", duracion)
            if horas:
                total += int(horas.group(1)) * 60
            if minutos:
                total += int(minutos.group(1))
            return total
        except:
            return None

    # Pedir contraseña hasta que sea válida o se cancele
    while True:
        contraseña = simpledialog.askstring("Conexión a MySQL",
                                            "Favor de ingresar la contraseña de su aplicación MySQL (Workbench)")
        if contraseña is None:
            messagebox.showwarning("Cancelado", "Operación cancelada por el usuario.")
            break

        try:
            # Verificar conexión con mysql.connector
            conexion_mysql = mysql.connector.connect(
                host="localhost",
                port=3306,
                user="root",
                password=contraseña
            )
            cursor = conexion_mysql.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS Extraccion_de_datos_Movies;")
            cursor.close()
            conexion_mysql.close()
            break  # Salir del ciclo si fue exitoso
        except Error:
            messagebox.showerror("Error de conexión",
                                 "❌ Contraseña incorrecta o fallo de conexión. Inténtalo de nuevo.")

    # Si se proporcionó una contraseña válida, continuar
    if contraseña:
        # Leer CSV original
        df = pd.read_csv("Extraccion de datos/movies.csv")

        # Eliminar columna extra si existe
        if 'Unnamed: 0' in df.columns:
            df.drop(columns=['Unnamed: 0'], inplace=True)

        # Limpiar columnas
        df["name_movie"] = df["name_movie"].str.replace(r"Pelicula: \[|\]", "", regex=True)
        df["year_movie"] = df["year_movie"].str.replace("Año: ", "", regex=False)
        df["time_movie"] = df["time_movie"].str.replace("Tiempo: ", "", regex=False)
        df["score_movie"] = df["score_movie"].str.replace("Puntaje: ", "", regex=False)

        df["year_movie"] = pd.to_numeric(df["year_movie"], errors="coerce")
        df["score_movie"] = pd.to_numeric(df["score_movie"].str.replace(",", "."), errors="coerce")
        df["time_movie"] = df["time_movie"].apply(convertir_duracion)

        # Eliminar filas con valores nulos
        df.dropna(inplace=True)

        # Conexión SQLAlchemy
        try:
            engine = create_engine(f"mysql+pymysql://root:{contraseña}@localhost:3306/Extraccion_de_datos_Movies")
            df.to_sql(name='data_movies', con=engine, if_exists='append', index=False)
            print("✅ Migración completada correctamente.")
        except OperationalError as e:
            messagebox.showerror("Error", f"❌ No se pudo migrar a MySQL: {e}")


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
df_dashboard = None

SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background": "linear-gradient(to bottom, #A9DFBF, #58D68D)",
    "color": "white",
    "boxShadow": "2px 0 5px rgba(0,0,0,0.1)",
    "textShadow": "1px 1px 2px rgba(0,0,0,0.3)"
}

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 2rem",
    "backgroundColor": "white",
    "borderRadius": "12px",
    "boxShadow": "0 8px 24px rgba(0,0,0,0.1)",
    "minHeight": "100vh"
}

sidebar = html.Div(
    [
        html.H2("IMDb Movies", className="display-4", style={"color": "white", "textShadow": "2px 2px 4px rgba(0,0,0,0.5)"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.3)"}),
        html.P("Proyecto final - Dashboard", className="lead", style={"color": "white", "textShadow": "1px 1px 2px rgba(0,0,0,0.3)"}),
        dbc.Nav(
            [
                dbc.NavLink("Hogar", href="/", active="exact", style={"color": "white"}),
                dbc.NavLink("Distribución por Puntajes", href="/dash1", active="exact", style={"color": "white"}),
                dbc.NavLink("Distribución por Duración", href="/dash2", active="exact", style={"color": "white"}),
                dbc.NavLink("Datos Origen", href="https://www.imdb.com/es-es/", target="_blank", style={"color": "white"}),
                dbc.NavLink("Trabajo en Github", href="https://github.com/ArmandoRamirez951/Proyecto_Final_Programacion_Extraccion_Datos", target="_blank", style={"color": "white"})
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

content = html.Div(id="page-content", style=CONTENT_STYLE)

# Aquí va el layout general, antes de iniciar el servidor
app.layout = html.Div([
    dcc.Location(id="url"),  # Necesario para navegación entre páginas
    sidebar,
    content
])

"""
Con esta  seccion empezamos a crear lo que sera la presentacion
de nuestra pagina, sera la interfaz principal que el usuario podra ver,
contendra titulo, nombre de materia, colaboradores e incluso el nonmbre y logo del maestro
"""
def pagina_hogar():
        return html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "Proyecto Final - Programación para Extracción de Datos",
                            className="mb-4",
                            style={
                                "fontSize": "2.5rem",
                                "fontWeight": "bold",
                                "color": "#145A32",
                                "marginBottom": "1.5rem",
                                "textShadow": "1px 1px 2px #D5F5E3"
                            }
                        ),
                        html.H4(
                            "Integrantes:",
                            className="mb-2",
                            style={
                                "fontWeight": "bold",
                                "marginTop": "1rem",
                                "marginBottom": "0.5rem",
                                "color": "#1B4F72"
                            }
                        ),
                        html.Ul(
                            [
                                html.Li("De La Cruz Ramirez Jeremy Yael"),
                                html.Li("Ramirez Cardenas Luis Armando"),
                            ],
                            className="mb-4",
                            style={
                                "listStyleType": "none",
                                "padding": 0,
                                "marginBottom": "1.5rem",
                                "fontSize": "1.1rem",
                                "color": "#2C3E50"
                            }
                        ),
                        html.P("Grupo: 951", className="mb-2",
                               style={"fontSize": "1rem", "marginBottom": "0.5rem", "color": "#2C3E50"}),
                        html.P("Fecha:", className="mb-2",
                               style={"fontSize": "1rem", "marginBottom": "1rem", "color": "#2C3E50"}),
                        html.H5(
                            "Profesor: Josue Miguel Flores Parra",
                            className="mb-4",
                            style={"fontWeight": "bold", "color": "#1A5276", "marginBottom": "1.5rem"}
                        ),
                        html.Img(
                            src="https://comunicacioninstitucional.uabc.mx/wp-content/uploads/2024/03/escudo-actualizado-2022-w1000px-751x1024.png",
                            style={
                                "width": "200px",
                                "height": "auto",
                                "margin": "auto",
                                "display": "block",
                                "marginBottom": "1.5rem",
                                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
                                "borderRadius": "8px"
                            }
                        ),
                        html.P(
                            "Bienvenidos al proyecto final de programación para la extracción de datos. "
                            "Aquí analizamos y visualizamos datos con Dash.",
                            className="mt-4",
                            style={
                                "fontSize": "1.1rem",
                                "lineHeight": "1.6",
                                "marginTop": "1.5rem",
                                "color": "#333",
                                "padding": "0 1rem"
                            }
                        )
                    ],
                    style={
                        "textAlign": "center",
                        "padding": "2.5rem",
                        "maxWidth": "850px",
                        "margin": "auto",
                        "backgroundColor": "rgba(255, 255, 255, 0.95)",
                        "borderRadius": "18px",
                        "boxShadow": "0 8px 24px rgba(0, 0, 0, 0.2)"
                    }
                )
            ],
            style={
                "backgroundImage": "linear-gradient(to right top, #A9DFBF, #82E0AA, #58D68D, #45B39D, #3498DB)",
                "minHeight": "100vh",
                "backgroundSize": "cover",
                "backgroundRepeat": "no-repeat",
                "padding": "4rem",
                "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
            }
        )

"""
En esta seccion del codigo empieza la creacion del primer dashoboard en el cual se tomaran los datos de puntajes
de las peliculas para crear los datos que se requieran en el dashboard, para su manipulacion y analisis respectivo, separando por categorias 
diferentes alineamientos de puntos, dependiendo de los datos que el usuario quiera saber o analizar
"""
def dashboart1():
    if df_dashboard is None or df_dashboard.empty:
        return html.P("No hay datos cargados. Por favor extrae y limpia los datos primero.")

    df_dashboard["decada"] = (df_dashboard["year_movie"] // 10) * 10
    decadas_disponibles = sorted(df_dashboard["decada"].unique())

    # Agregar opción "Todo" con valor -1
    opciones_dropdown = [{"label": "Todo", "value": -1}] + [{"label": f"{decada}s", "value": decada} for decada in decadas_disponibles]

    return html.Div([
        html.H3("Gráficas de Puntajes", style={"color": "#145A32", "marginBottom": "1rem"}),

        html.Label("Selecciona una década:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="dropdown-decada",
            options=opciones_dropdown,
            value=-1,  # Valor por defecto: "Todo"
            clearable=False,
            style={"marginBottom": "2rem"}
        ),

        dbc.Row([
            dbc.Col(dcc.Graph(id="grafica-hist"), md=6),
            dbc.Col(dcc.Graph(id="grafica-barras"), md=6),
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="grafica-pie"), md=6),
            dbc.Col(dcc.Graph(id="grafica-linea"), md=6),
        ]),

        html.H4("Top 10 películas mejor puntuadas", style={"marginTop": "2rem", "color": "#1A5276"}),
        dcc.Graph(id="grafica-top10")
    ],
        style={
            "backgroundColor": "rgba(255, 255, 255, 0.95)",
            "padding": "1.5rem",
            "borderRadius": "12px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "maxWidth": "900px",
            "margin": "auto",
            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        })


@app.callback(
    Output("grafica-hist", "figure"),
    Output("grafica-barras", "figure"),
    Output("grafica-pie", "figure"),
    Output("grafica-linea", "figure"),
    Output("grafica-top10", "figure"),
    Input("dropdown-decada", "value")
)

def actualizar_graficas(decada):
    if decada == -1:
        df_filtrado = df_dashboard.copy()  # Todos los datos
    else:
        df_filtrado = df_dashboard[df_dashboard["decada"] == decada]

    # Histograma
    fig_hist = px.histogram(df_filtrado, x="score_movie", nbins=20, title="Histograma de Puntajes")

    # Barras
    conteo = df_filtrado["score_movie"].value_counts().sort_index()
    fig_barras = px.bar(
        x=conteo.index, y=conteo.values,
        labels={"x": "Puntaje", "y": "Cantidad"},
        title="Conteo de Puntajes"
    )

    # Pie
    fig_pie = px.pie(
        names=conteo.index, values=conteo.values,
        title="Distribución de Puntajes"
    )

    # Línea
    promedio_por_año = df_filtrado.groupby("year_movie")["score_movie"].mean().reset_index()
    fig_linea = px.line(
        promedio_por_año, x="year_movie", y="score_movie",
        title="Promedio de Puntajes por Año",
        labels={"year_movie": "Año", "score_movie": "Puntaje Promedio"},
        markers=True
    )

    # Top 10
    top10 = df_filtrado.sort_values("score_movie", ascending=False).head(10)
    fig_top10 = px.bar(
        top10,
        x="name_movie",
        y="score_movie",
        title="Top 10 películas mejor puntuadas",
        labels={"name_movie": "Película", "score_movie": "Puntaje"}
    )

    return fig_hist, fig_barras, fig_pie, fig_linea, fig_top10


"""
En esta seccion utilizamos los datos limpios,
utilizamos espesificamente los datos de tiempos que se limpiaron a minutos
se crearon un total de 4 tablas y otra seccion a lo ultimo
que muestra las 10 peliculas mas largas
"""
def dashboart2():
    if df_dashboard is None or df_dashboard.empty:
        return html.P("No hay datos cargados. Por favor extrae y limpia los datos primero.")

    def rango_duracion(minutos):
        if minutos < 60:
            return "0-59 min"
        elif minutos < 120:
            return "60-119 min"
        elif minutos < 180:
            return "120-179 min"
        elif minutos < 240:
            return "180-239 min"
        else:
            return "240+ min"

    df_dashboard["rango_duracion"] = df_dashboard["time_movie"].apply(rango_duracion)

    def ordenar_rangos(rango):
        if '+' in rango:
            return int(rango.split('+')[0])
        else:
            return int(rango.split('-')[0])

    rangos_disponibles = sorted(df_dashboard["rango_duracion"].unique(), key=ordenar_rangos)

    opciones_dropdown = [{"label": "Todo", "value": "Todo"}] + [{"label": r, "value": r} for r in rangos_disponibles]

    return html.Div([
        html.H3("Gráficas de Duración", style={"color": "#145A32", "marginBottom": "1rem"}),

        html.Label("Selecciona un rango de duración:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="dropdown-duracion",
            options=opciones_dropdown,
            value="Todo",
            clearable=False,
            style={"marginBottom": "2rem"}
        ),

        dbc.Row([
            dbc.Col(dcc.Graph(id="grafica-hist-duracion"), md=6),
            dbc.Col(dcc.Graph(id="grafica-dispersion-duracion"), md=6),  # Nombre cambiado correctamente
        ], className="mb-4"),

        dbc.Row([
            dbc.Col(dcc.Graph(id="grafica-pie-duracion"), md=6),
            dbc.Col(dcc.Graph(id="grafica-linea-duracion"), md=6),
        ]),

        html.H4("Top 10 películas más largas", style={"marginTop": "2rem", "color": "#1A5276"}),
        dcc.Graph(id="grafica-top10-duracion")
    ],
    style={
        "backgroundColor": "rgba(255, 255, 255, 0.95)",
        "padding": "1.5rem",
        "borderRadius": "12px",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "maxWidth": "900px",
        "margin": "auto",
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    })

@app.callback(
    Output("grafica-hist-duracion", "figure"),
    Output("grafica-dispersion-duracion", "figure"),  # <- nuevo ID aquí también
    Output("grafica-pie-duracion", "figure"),
    Output("grafica-linea-duracion", "figure"),
    Output("grafica-top10-duracion", "figure"),
    Input("dropdown-duracion", "value")
)
def actualizar_graficas_duracion(rango):
    if rango == "Todo":
        df_filtrado = df_dashboard.copy()
    else:
        df_filtrado = df_dashboard[df_dashboard["rango_duracion"] == rango]

    # Histograma
    fig_hist = px.histogram(df_filtrado, x="time_movie", nbins=20, title="Histograma de Duración (minutos)")

    # Dispersión
    fig_dispersion = px.scatter(
        df_filtrado,
        x="time_movie",
        y="score_movie",
        title="Duración vs Puntaje",
        labels={"time_movie": "Duración (minutos)", "score_movie": "Puntaje"},
        hover_data=["name_movie", "year_movie"],
        color="score_movie",
        color_continuous_scale=px.colors.sequential.Viridis,
    )

    # Pie
    conteo_rango = df_filtrado["rango_duracion"].value_counts().sort_index()
    fig_pie = px.pie(
        names=conteo_rango.index, values=conteo_rango.values,
        title="Distribución de Películas por Rango de Duración"
    )

    # Línea
    promedio_por_año = df_filtrado.groupby("year_movie")["time_movie"].mean().reset_index()
    fig_linea = px.line(
        promedio_por_año, x="year_movie", y="time_movie",
        title="Promedio de Duración por Año",
        labels={"year_movie": "Año", "time_movie": "Duración Promedio (minutos)"},
        markers=True
    )

    # Top 10
    top10 = df_filtrado.sort_values("time_movie", ascending=False).head(10)
    fig_top10 = px.bar(
        top10,
        x="name_movie",
        y="time_movie",
        title="Top 10 películas más largas",
        labels={"name_movie": "Película", "time_movie": "Duración (minutos)"}
    )

    return fig_hist, fig_dispersion, fig_pie, fig_linea, fig_top10

"""
En esta seccion del codigo se manda a llamar a los dashboard que se crearon y que funcionen de manera correcta
"""
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page_content(pathname):
    if pathname == "/":
        return pagina_hogar()
    elif pathname == "/dash1":
        return dashboart1()
    elif pathname == "/dash2":
        return dashboart2()
    return html.Div([
        html.H1("404: Not found", className="text-danger"),
        html.P(f"La página '{pathname}' no existe.")
    ])



"""
En esta seccion se inicia el dashboart, para que
funcione correctamente ya que manda a llamar los archivos
que emos creado para trabajar correctamente
"""
def iniciar_dashboard():
    messagebox.showwarning("Regresar al Menu", "Cuando requiera volver al menú presione el botón stop del programa")
    global df_dashboard
    ruta_csv_limpio = "Extraccion de datos/movies_limpio.csv"

    if os.path.isfile(ruta_csv_limpio):
        df_dashboard = pd.read_csv(ruta_csv_limpio)
    else:
        print("Archivo limpio no encontrado. Por favor limpia los datos primero.")
        return

    print("\n>>> Primeras filas del DataFrame limpio:")
    print(df_dashboard.head())

    print("\n>>> Tipos de datos:")
    print(df_dashboard.dtypes)

    print("\n>>> Valores nulos en cada columna:")
    print(df_dashboard.isnull().sum())

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(debug=False)

# ----------- Menú -----------
"""
En esta seccion del codigo se presenta el menu interactivo del codigo, para su manipulacion
a gusto del encargado de revisar el proyecto
"""
def menu():
    opc = 0
    while (opc != 5):
        opc = simpledialog.askinteger(" Proyecto Final - Programacio para Extraccion de Datos ",
                                      "                             MENU                        \n"
                                      "1) Extraer datos de la pagina de IMDB "
                                      "\n2) Realizar limpieza de los datos extraidos "
                                      "\n3) Migrar los datos a MYSQL "
                                      "\n4) Abrir los dashboard "
                                      "\n5) Salir del programa")
        if opc == 1:
            extraccion()
        elif opc == 2:
            limpieza_de_los_datos()
        elif opc == 3:
            migrar_a_mysql()
        elif opc == 4:
            iniciar_dashboard()
            root.withdraw()
        elif opc == 5:
            messagebox.showinfo("SAlIENDO", "Gracias Vuelva Pronto")
            root.destroy()
        else:
            messagebox.showerror("Error", "Ingrese un numero valido")

"""
Con el siguiente if se buscara mandar a llamar el menu
"""
if __name__ == "__main__":
    menu()


