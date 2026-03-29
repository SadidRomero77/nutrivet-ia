"""
Rate Limiter compartido — instancia única para toda la app.

Todos los routers deben importar `limiter` desde este módulo
en vez de crear su propia instancia.

slowapi requiere que el decorador @limiter.limit() use la MISMA
instancia registrada en app.state.limiter.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
