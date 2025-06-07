'''
Proyecto Final - Programacion para Extraccion de Datos
integrantes:
    -- De La Cruz Ramirez Jeremy Yael
    -- Ramirez Cardenas Luis Armando
Grupo: 951
Fecha:
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