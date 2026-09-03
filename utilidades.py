"""Utilidades transversales del servicio."""
import functools

def con_registro(func):
    """Registra la llamada y deja que cualquier fallo se propague."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            print(f"[registro] {func.__name__} falló: {exc}")
            raise
    return envoltura
