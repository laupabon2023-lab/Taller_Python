# Dictamen sobre `ia_propuesta.py` — Parte D

**Integrantes:** Laura Pabon y Lizeth Rodriguez.

---

## Defecto 1

- **Qué ¿está mal?:**
  El validador de campo `redondear_monto` (líneas 26-28) ejecuta `round(v, 2)` pero **no retorna el valor**. Como resultado, el monto no se redondea y el campo termina en None.

- **Por qué es un defecto** (módulo sección):
  M4. 6. Validadores de campo. Un validador de campo **debe retornar** el valor transformado; si no lo hace, la validación no tiene efecto y se pierde la intención del diseño.

- **Cómo lo comprobamos:**

```python
from ia_propuesta import SolicitudPuntuacion

s = SolicitudPuntuacion(
    poliza="POL-2026-0413",
    correo_analista="test@example.com",
    monto=1234.56789,  # Valor con muchos decimales
    antiguedad=3,
    siniestros_previos=1
)
print(f"Monto validado: {s.monto}")
```

```
Monto validado: None 
```

El monto debería haber sido `1234.57` (redondeado a 2 decimales), pero queda el campo como None.

- **Corrección:**
  Añadir `return` antes de `round(v, 2)`:

```python
@field_validator("monto")
@classmethod
def redondear_monto(cls, v: float) -> float:
    """Redondea el monto a dos decimales para evitar ruido de coma flotante."""
    return round(v, 2)  # Se agrega return
```

---

## Defecto 2

- **Qué ¿está mal?:**
  La función `_puntuar` (linea 40) es declarada como `async def` pero usa `time.sleep(0.2)`, que es una llamada **bloqueante**. Esto anula los beneficios de la asincronía porque el event loop se queda esperando sin poder atender otras tareas.

- **Por qué es un defecto**(módulo sección):
  M5. 6. Síncrono frente a asíncrono. En Python, `time.sleep()` bloquea el event loop aunque la función sea async. Esto impide la ejecución concurrente de otras tareas y hace que asyncio.gather() procese las solicitudes prácticamente una por una.

- **Cómo lo comprobamos:**

```python
import asyncio
import time
from ia_propuesta import _puntuar, SolicitudPuntuacion

async def medir_tiempo_lote():
    solicitudes = [
        SolicitudPuntuacion(
            poliza=f"POL-{i:04d}xxxx", 
            correo_analista="test@example.com",
            monto=1000,
            antiguedad=3,
            siniestros_previos=1
        )
        for i in range(5)
    ]
    
    t0 = time.perf_counter()
    from ia_propuesta import evaluar_lote
    await evaluar_lote(solicitudes)
    total = time.perf_counter() - t0
    print(f"Tiempo total para 5 solicitudes: {total:.2f} s")
    print(f"Tiempo esperado si fuera no bloqueante: ~0.2 s")
    print(f"Tiempo real (bloqueante): ~{5 * 0.2} s")

asyncio.run(medir_tiempo_lote())
```

```
Tiempo total para 5 solicitudes: 1.00 s
Tiempo esperado si fuera no bloqueante: ~0.2 s
Tiempo real (bloqueante): ~1.0 s
```

Con 5 solicitudes que deberían tomar 0.2 s cada una en paralelo, el tiempo total debería ser ~0.2 s. En cambio, toma ~1.0 s porque se ejecutan **una tras otra** (5 × 0.2 s = 1.0 s).

- **Corrección:**
  Reemplazar `time.sleep(0.2)` por `await asyncio.sleep(0.2)`:

```python
async def _puntuar(solicitud: SolicitudPuntuacion) -> float:
    """Consulta el servicio externo de scoring y devuelve la probabilidad."""
    await asyncio.sleep(0.2)  # Se cambia time.sleep por asyncio.sleep con await
    base = 0.18 * solicitud.siniestros_previos - 0.01 * solicitud.antiguedad
    return max(0.0, min(1.0, 0.4 + base))
```

---

## Defecto 3

- **Qué ¿está mal?:**
  El patrón de correo en correo_analista usa {2,3} para la longitud del dominio de nivel superior (TLD): r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$". Esto rechaza incorrectamente correos válidos cuyo TLD tiene 4 o más letras, como .info o .online

- **Por qué es un defecto** (módulo sección):
  M4 · 4. El poder de Fiel. Un patrón de validación debe cubrir el rango real de datos válidos y un TLD de más de 3 letras es perfectamente válido, así que restringirlo a {2,3} produce falsos negativos: usuarios con un correo real y correcto quedan bloqueados por el sistema.

- **Cómo lo comprobamos:**

```python
from ia_propuesta import SolicitudPuntuacion

s = SolicitudPuntuacion(
    poliza="POL-2026-0413",
    correo_analista="analista@empresa.info",  # correo válido, TLD de 4 letras
    monto=1000,
    antiguedad=3,
    siniestros_previos=1
)
print(f"Correo aceptado: {s.correo_analista}")
```

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for SolicitudPuntuacion
correo_analista
  String should match pattern '^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,3}$'
```

Un correo válido es rechazado por el patrón.

- **Corrección:**
  Quitar el límite superior del TLD, de {2,3} a {2,}:

```python

EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")```

---

**Archivo con las tres correcciones:** `ia_propuesta_corregida.py`
