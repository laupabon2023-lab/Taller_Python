"""Lógica de dominio: evaluación de riesgo de pólizas."""
import csv
from pathlib import Path

import config
from utilidades import con_registro

BASE = Path(__file__).parent

class RepositorioEvaluaciones:
    """Colección de evaluaciones registradas.

    Es un colaborador aparte (no un atributo de clase de EvaluadorRiesgo)
    para que el historial no quede compartido implícitamente entre
    instancias: cada EvaluadorRiesgo recibe una referencia explícita a un
    repositorio, y por defecto todos comparten el mismo, pero la
    responsabilidad de guardar vive aquí, no en el evaluador.
    """

    def __init__(self):
        self._evaluaciones = []

    def agregar(self, poliza, puntaje):
        self._evaluaciones.append({"poliza": poliza, "puntaje": puntaje})

    def todas(self):
        return list(self._evaluaciones)


repositorio_evaluaciones = RepositorioEvaluaciones()


class EvaluadorRiesgo:
    """Evalúa el riesgo de una póliza y registra lo que ha evaluado."""

    umbral = config.UMBRAL_ALTO_RIESGO

    def __init__(self, poliza, repositorio=None):
        self.poliza = poliza
        self.repositorio = repositorio if repositorio is not None else repositorio_evaluaciones

    @con_registro
    def puntuar(self, modelo, payload):
        rasgos = [[
            payload["monto"],
            payload["antiguedad"],
            payload["siniestros_previos"],
        ]]
        return float(modelo.predict_proba(rasgos)[0][1])

    def anotar(self, puntaje):
        self.repositorio.agregar(self.poliza, puntaje)

    def es_alto_riesgo(self, puntaje):
        return puntaje is not None and puntaje > self.umbral


def cargar_siniestros():
    with open(BASE / config.RUTA_DATOS, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def buscar_siniestro(id_siniestro):
    for fila in cargar_siniestros():
        if fila["id"] == str(id_siniestro):
            return fila
    return None