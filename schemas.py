"""Esquemas de entrada y salida (validación declarativa con Pydantic)."""
from pydantic import BaseModel, Field, field_validator


class ScorePayload(BaseModel):
    """Entrada de POST /score."""

    poliza: str
    monto: float = Field(gt=0, description="Monto reclamado; debe ser positivo")
    antiguedad: int = Field(ge=0, description="Antigüedad de la póliza en años")
    siniestros_previos: int = Field(ge=0, description="Número de siniestros previos")

    @field_validator("poliza")
    @classmethod
    def poliza_no_vacia(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("poliza no puede estar vacía")
        return v


class PuntuacionOut(BaseModel):
    """Salida de POST /score."""

    poliza: str
    puntaje: float
    alto_riesgo: bool