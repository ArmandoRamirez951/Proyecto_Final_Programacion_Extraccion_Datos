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