"""
Propuesta corregida para riesgo-api-v0.

Correcciones aplicadas respecto a ia_propuesta.py:
1. El validador redondear_monto ahora retorna el valor (return round(v, 2))
2. _puntuar usa await asyncio.sleep() en vez de time.sleep()
3. El patrón de email ya no limita el TLD a 2-3 letras ({2,3} -> {2,})
"""
import asyncio
import re
from typing import Optional
 
from pydantic import BaseModel, Field, field_validator
 
# Patrón de email a nivel de módulo (no dentro de la clase, para que Pydantic
# no lo trate como un campo del modelo). TLD sin límite superior de longitud.
EMAIL_PATTERN = re.compile(r"^[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}$")
 
 
class SolicitudPuntuacion(BaseModel):
    """Datos de entrada para puntuar una póliza."""
 
    poliza: str = Field(min_length=8, max_length=20)
    correo_analista: str  # Se valida con field_validator, no con pattern en Field()
    monto: float = Field(gt=0)
    antiguedad: int = Field(ge=0, le=60)
    siniestros_previos: int = Field(ge=0)
    observaciones: Optional[str] = Field(default=None, max_length=200)
 
    @field_validator("correo_analista")
    @classmethod
    def validar_email(cls, v: str) -> str:
        """Valida que el correo tenga formato de email válido."""
        if not EMAIL_PATTERN.match(v):
            raise ValueError(f"correo_analista '{v}' no tiene formato de email válido")
        return v
 
    @field_validator("monto")
    @classmethod
    def redondear_monto(cls, v: float) -> float:
        """Redondea el monto a dos decimales para evitar ruido de coma flotante."""
        return round(v, 2)  # CORRECCIÓN 1: se añade el return
 
 
class RespuestaPuntuacion(BaseModel):
    """Resultado de la evaluación."""
 
    poliza: str
    puntaje: float = Field(ge=0.0, le=1.0)
    alto_riesgo: bool
 
 
async def _puntuar(solicitud: SolicitudPuntuacion) -> float:
    """Consulta el servicio externo de scoring y devuelve la probabilidad."""
    await asyncio.sleep(0.2)  # CORRECCIÓN 2: ya no bloquea el event loop
    base = 0.18 * solicitud.siniestros_previos - 0.01 * solicitud.antiguedad
    return max(0.0, min(1.0, 0.4 + base))
 
 
async def evaluar_lote(solicitudes) -> list:
    """Evalúa un lote de solicitudes de forma concurrente."""
    return await asyncio.gather(*[_puntuar(s) for s in solicitudes])
 
 
if __name__ == "__main__":
    import time as tm
 
    print("Test 1: Validador de monto")
    s1 = SolicitudPuntuacion(
        poliza="POL-2026-0413",
        correo_analista="test@example.com",
        monto=1234.56789,
        antiguedad=3,
        siniestros_previos=1
    )
    print(f"  monto validado: {s1.monto}")
    assert s1.monto == 1234.57, "El monto debe estar redondeado a 2 decimales"
    print("  Test 1 pasa\n")
 
    print("Test 2: Email inválido (formato incorrecto) es rechazado")
    try:
        SolicitudPuntuacion(
            poliza="POL-2026-0413", correo_analista="no-es-un-email",
            monto=1000.0, antiguedad=3, siniestros_previos=1
        )
        print("  FALLA: email inválido fue aceptado")
    except ValueError as e:
        print(f"  Rechazado correctamente: {e}")
        print("  Test 2 pasa\n")
 
    print("Test 3: Email válido con TLD largo (.info) es aceptado")
    s3 = SolicitudPuntuacion(
        poliza="POL-2026-0413", correo_analista="analista@empresa.info",
        monto=1000.0, antiguedad=3, siniestros_previos=1
    )
    print(f"  correo aceptado: {s3.correo_analista}")
    print("  Test 3 pasa\n")
 
    print("Test 4: Concurrencia asíncrona real")
 
    async def test_concurrencia():
        t0 = tm.perf_counter()
        await asyncio.gather(*[_puntuar(s1) for _ in range(5)])
        return tm.perf_counter() - t0
 
    tiempo = asyncio.run(test_concurrencia())
    print(f"  Tiempo total para 5 tareas de 0.2 s: {tiempo:.2f} s")
    assert tiempo < 0.5, "Deben completarse en ~0.2 s, no 1.0 s"
    print("  Test 4 pasa\n")
 
    print("Todos los tests pasan")