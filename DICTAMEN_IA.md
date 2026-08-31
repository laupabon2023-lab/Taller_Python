# Dictamen sobre `ia_propuesta.py` — Parte D

**Grupo:** <number> · **Integrantes:** Laura Pabon y Lizeth Rodriguez.

---

## Defecto 1

- **Qué ¿está mal?:**
  El validador de campo `redondear_monto` (líneas 26-28) ejecuta `round(v, 2)` pero **no retorna el valor**. Como resultado, el monto no se redondea y Pydantic usa el valor original sin modificaci—n.

- **Por qué es un defecto** (módulo · sección):
  M4 · 3. Validación declarativa con Pydantic. Un validador de campo **debe retornar** el valor transformado; si no lo hace, la validación no tiene efecto y se pierde la intención del diseño.

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
Monto validado: 1234.56789
```

El monto deber’a haber sido `1234.57` (redondeado a 2 decimales), pero quedo como `1234.56789`.

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
  La función `_puntuar` (l’nea 40) es declarada como `async def` pero usa `time.sleep(0.2)`, que es una llamada **bloqueante**. Esto anula los beneficios de la asincronía porque el event loop se queda esperando sin poder atender otras tareas.

- **Por qué es un defecto**(módulo · sección):
  M5 · 4. Concurrencia asíncrona. En Python, `time.sleep()` bloquea el hilo completo, mientras que `await asyncio.sleep()` libera el event loop para que pueda procesar otras coroutines concurrentes. Usar `sleep` síncrono dentro de `async def` es un anti-patrón que degrada el rendimiento bajo concurrencia.

- **Cómo lo comprobamos:**

```python
import asyncio
import time
from ia_propuesta import _puntuar, SolicitudPuntuacion

async def medir_tiempo_lote():
    solicitudes = [
        SolicitudPuntuacion(
            poliza=f"POL-{i}",
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

Con 5 solicitudes que deber’an tomar 0.2 s cada una en paralelo, el tiempo total deber’a ser ~0.2 s. En cambio, toma ~1.0 s porque se ejecutan **una tras otra** (5 × 0.2 s = 1.0 s).

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
  El campo `correo_analista` (líneas 17-19) usa `pattern=...` directamente en `Field()`. En **Pydantic v2**, esta sintaxis **no es v‡lida**: las restricciones de patrón regex deben aplicarse mediante `Annotated` con `StringConstraints`, no como argumento directo de `Field()`.

- **Por qué es un defecto** (módulo · sección):
  M4 · 3. Validación declarativa con Pydantic. Pydantic v2 cambiá la API de validación de strings: `Field(pattern=...)` fue reemplazado por `Annotated[str, StringConstraints(pattern=...)]`. Usar la sintaxis de v1 en v2 genera un `TypeError` o ignora la validación.

- **Cómo lo comprobamos:**

```python
from ia_propuesta import SolicitudPuntuacion

# Intentar crear una instancia con un correo inv‡lido
try:
    s = SolicitudPuntuacion(
        poliza="POL-2026-0413",
        correo_analista="correo_invalido",  # Sin @ ni dominio
        monto=1000,
        antiguedad=3,
        siniestros_previos=1
    )
    print(f"Correo aceptado (ERROR): {s.correo_analista}")
except Exception as e:
    print(f"Excepci—n: {type(e).__name__}: {e}")
```

```
Correo aceptado (ERROR): correo_invalido
```

El correo inv‡lido **debería generar un ValidationError**, pero es aceptado porque el patrón regex no se est‡ aplicando correctamente.

- **Corrección:**
  Usar `Annotated` con `StringConstraints` (requiere importar `from pydantic import StringConstraints` y `from typing import Annotated`):

```python
from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator, StringConstraints

class SolicitudPuntuacion(BaseModel):
    """Datos de entrada para puntuar una p—liza."""

    poliza: str = Field(min_length=8, max_length=20)
    correo_analista: Annotated[
        str,
        StringConstraints(pattern=r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")
    ]
    monto: float = Field(gt=0)
    antiguedad: int = Field(ge=0, le=60)
    siniestros_previos: int = Field(ge=0)
    observaciones: Optional[str] = Field(default=None, max_length=200)

    @field_validator("monto")
    @classmethod
    def redondear_monto(cls, v: float) -> float:
        """Redondea el monto a dos decimales para evitar ruido de coma flotante."""
        return round(v, 2)
```

---

## Resumen de correcciones aplicadas

| Defecto | Archivo corregido | L’neas afectadas |
|---------|-------------------|------------------|
| 1. Validador sin return | `ia_propuesta_corregida.py` | 26-28 |
| 2. `time.sleep` en async | `ia_propuesta_corregida.py` | 40 |
| 3. `pattern` en Field (v1) | `ia_propuesta_corregida.py` | 17-19 |

**Archivo con las tres correcciones:** `ia_propuesta_corregida.py`
