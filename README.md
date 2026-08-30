# riesgo-api-v0

Servicio de puntuación de siniestros de la Aseguradora Santo Tomás.
Recibe los datos de una póliza y devuelve la probabilidad de que el siniestro
declarado termine en un pago alto.

## Instalación

```bash
pip install -r requirements.txt
```

El modelo entrenado (`modelo.pkl`) viene en el repositorio.

Antes de arrancar, exporta las variables de entorno necesarias (pedir los
valores reales al equipo; aquí solo se muestra el formato esperado):
```bash
export API_KEY="clave_personal"
export CLAVE_FIRMA="clave_firma"
```

## Puesta en marcha

### Desarrollo (con recarga automática)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El arranque de producción **no usa `--reload`**: esa bandera vigila cambios
en disco y reinicia el servidor, lo cual es útil en desarrollo pero añade
sobrecarga y comportamiento no determinista en producción.

## Endpoints

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | Comprobación de salud del servicio |ñ
| POST | `/score` | Puntúa una póliza |
| GET | `/historial` | Evaluaciones hechas |
| GET | `/siniestros/{id}` | Consulta un siniestro |
| GET | `/exportar` | Exporta el histórico para el equipo de actuaría |
| GET | `/ping` | Comprobación rápida |
| GET | `/consulta-archivo` | Cuenta los registros del archivo de siniestros |
| GET | `/servicio-externo` | Consulta la tarifa de referencia del reasegurador |
| GET | `/calculo-pesado` | Recalcula la reserva agregada |

### Ejemplo

```bash
curl -X POST localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"poliza": "POL-2026-0413", "monto": 4200000, "antiguedad": 3, "siniestros_previos": 1}'
```

```json
{"poliza": "POL-2026-0413", "puntaje": 0.61, "alto_riesgo": false}
```

## Notas

- LaLa clave de la API se lee desde la variable de entorno `API_KEY`, nunca se
  versiona en el código (ver `config.py`).
- El histórico se exporta como JSON (`GET /exportar`); no se usa `pickle`
  para nada que salga hacia un cliente externo.
