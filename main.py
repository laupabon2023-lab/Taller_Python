"""
riesgo-api-v0 — Servicio de puntuación de siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import pickle
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException

import config
from dominio import EvaluadorRiesgo, buscar_siniestro, cargar_siniestros, repositorio_evaluaciones
from schemas import PuntuacionOut, ScorePayload

BASE = Path(__file__).parent
app = FastAPI(title="Riesgo API", version="0.1.0")

# El modelo se carga UNA sola vez, al importar el módulo (es decir, al
# arrancar el servicio) — no dentro de cada petición.
with open(BASE / config.RUTA_MODELO, "rb") as _fh:
    MODELO = pickle.load(_fh)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/score", response_model=PuntuacionOut)
async def score(payload: ScorePayload):
    evaluador = EvaluadorRiesgo(payload.poliza)
    puntaje = evaluador.puntuar(MODELO, payload.model_dump())
    evaluador.anotar(puntaje)

    return PuntuacionOut(
        poliza=payload.poliza,
        puntaje=puntaje,
        alto_riesgo=evaluador.es_alto_riesgo(puntaje),
    )


@app.get("/historial")
async def historial():
    return {"evaluaciones": repositorio_evaluaciones.todas()}


@app.get("/siniestros/{id_siniestro}")
async def siniestro(id_siniestro: int):
    fila = buscar_siniestro(id_siniestro)
    if fila is None:
        raise HTTPException(status_code=404, detail=f"no existe el siniestro {id_siniestro}")
    return fila


@app.get("/exportar")
async def exportar():
    return cargar_siniestros()


# --- Endpoints de perfil de carga -----------------------------------------

@app.get("/ping")
async def ping():
    return {"pong": True}


@app.get("/consulta-archivo")
async def consulta_archivo():
    contenido = (BASE / config.RUTA_DATOS).read_text(encoding="utf-8")
    return {"lineas": len(contenido.splitlines())}


@app.get("/servicio-externo")
async def servicio_externo():
    time.sleep(0.3)
    return {"tarifa_referencia": 1.18}


@app.get("/calculo-pesado")
async def calculo_pesado():
    total = 0.0
    for i in range(3_000_000):
        total += (i % 7) ** 0.5
    return {"total": round(total, 2)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)