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