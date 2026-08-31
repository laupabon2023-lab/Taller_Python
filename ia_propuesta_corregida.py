"""
Propuesta corregida para riesgo-api-v0.

Correcciones aplicadas respecto a ia_propuesta.py:
1. El validador redondear_monto ahora retorna el valor (return round(v, 2))
2. _puntuar usa await asyncio.sleep() en vez de time.sleep()
3. correo_analista se valida con @field_validator en vez de pattern en Field()
"""
import asyncio
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SolicitudPuntuacion(BaseModel):
    """Datos de entrada para puntuar una pÓ·liza."""

    poliza: str = Field(min_length=8, max_length=20)
    correo_analista: str  # Se valida con field_validator, no con pattern en Field()
    monto: float = Field(gt=0)
    antiguedad: int = Field(ge=0, le=60)
    siniestros_previos: int = Field(ge=0)
    observaciones: Optional[str] = Field(default=None, max_length=200)

    # PatrÓ·n de email compilado para reutilizar
    EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")

    @field_validator("correo_analista")
    @classmethod
    def validar_email(cls, v: str) -> str:
        """Valida que el correo tenga formato de email vÁ·lido."""
        if not cls.EMAIL_PATTERN.match(v):
            raise ValueError(f"correo_analista '{v}' no tiene formato de email vÁ·lido")
        return v

    @field_validator("monto")
    @classmethod
    def redondear_monto(cls, v: float) -> float:
        """Redondea el monto a dos decimales para evitar ruido de coma flotante."""
        return round(v, 2)  # CORRECCIÓ·N 1: se aÑ·`return`


class RespuestaPuntuacion(BaseModel):
    """Resultado de la evaluació·¿·n."""

    poliza: str
    puntaje: float = Field(ge=0.0, le=1.0)
    alto_riesgo: bool


async def _puntuar(solicitud: SolicitudPuntuacion) -> float:
    """Consulta el servicio externo de scoring y devuelve la probabilidad."""
    await asyncio.sleep(0.2)  # CORRECCIÓ·N 2: no bloquea el event loop
    base = 0.18 * solicitud.siniestros_previos - 0.01 * solicitud.antiguedad
    return max(0.0, min(1.0, 0.4 + base))


async def evaluar_lote(solicitudes) -> list:
    """EvalÓ·a un lote de solicitudes de forma concurrente."""
    return await asyncio.gather(*[_puntuar(s) for s in solicitudes])


# --- Demo de que las correcciones funcionan ---

if __name__ == "__main__":
    import asyncio

    # Test 1: El validador de monto ahora retorna el valor
    print("Test 1: Validador de monto")
    s1 = SolicitudPuntuacion(
        poliza="POL-2026-0413",
        correo_analista="test@example.com",
        monto=1000.567,
        antiguedad=3,
        siniestros_previos=1
    )
    print(f"  monto original: 1000.567")
    print(f"  monto después de validació·¿·n: {s1.monto}")
    print(f"  tipo: {type(s1.monto)}")
    assert s1.monto == 1000.57, "El monto debe estar redondeado a 2 decimales"
    print("  ✓ Test 1 pasa\n")

    # Test 2: Email invÁ·lido es rechazado
    print("Test 2: Validació·¿·n de email")
    try:
        s2 = SolicitudPuntuacion(
            poliza="POL-2026-0413",
            correo_analista="no-es-un-email",  # InvÁ·lido
            monto=1000.0,
            antiguedad=3,
            siniestros_previos=1
        )
        print("  ✗ Test 2 falla: email invÁ·lido fue aceptado")
    except ValueError as e:
        print(f"  Email invÁ·lido rechazado correctamente: {e}")
        print("  ✓ Test 2 pasa\n")

    # Test 3: La funció·¿·n async no bloquea el event loop
    print("Test 3: Concurrencia asíncrona")
    async def test_concurrencia():
        import time as tm
        t0 = tm.perf_counter()
        # 5 tareas que cada una espera 0.2 s
        await asyncio.gather(*[_puntuar(s1) for _ in range(5)])
        t1 = tm.perf_counter()
        total = t1 - t0
        print(f"  Tiempo total para 5 tareas de 0.2 s: {total:.2f} s")
        if total < 0.5:
            print("  ✓ Las tareas se ejecutaron concurrentemente (no bloqueante)")
        else:
            print("  ✗ Las tareas se ejecutaron secuencialmente (bloqueante)")
        return total

    tiempo = asyncio.run(test_concurrencia())
    assert tiempo < 0.5, "La concurrencia asíncrona debe completar 5 tareas de 0.2 s en ~0.2 s"
    print("  ✓ Test 3 pasa\n")

    print("Todos los tests pasan ✓")