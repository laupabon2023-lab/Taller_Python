"""Configuración del servicio."""

import os

# Se crea un entorno environ para ocultar estas claves

API_KEY = os.environ.get("API_KEY", "")
CLAVE_FIRMA = os.environ.get("CLAVE_FIRMA", "")

UMBRAL_ALTO_RIESGO = 0.7
RUTA_MODELO = "modelo.pkl"
RUTA_DATOS = "datos/siniestros.csv"
