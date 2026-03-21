"""
Middleware de autenticación y autorización RBAC — NutriVet.IA.
Provee dependencias FastAPI: get_current_user y require_role.
El JWTService es inyectable para facilitar tests.
"""
from __future__ import annotations

import os
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.domain.exceptions.domain_errors import DomainError
from backend.infrastructure.auth.jwt_service import JWTService, TokenPayload

_bearer_scheme = HTTPBearer(auto_error=False)


def get_jwt_service() -> JWTService:
    """
    Proveedor del JWTService — sobreescribible en tests via app.dependency_overrides.

    Lee la clave secreta desde variables de entorno.
    Constitution REGLA 6: JWT nunca sin secret seguro — falla ruidosamente si no está configurado.
    """
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError(
            "JWT_SECRET_KEY no está configurado. "
            "Define la variable de entorno con un secret seguro (≥32 caracteres). "
            "Ejemplo: openssl rand -hex 32"
        )
    algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
    return JWTService(secret_key=secret, algorithm=algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    jwt_service: JWTService = Depends(get_jwt_service),
) -> TokenPayload:
    """
    Dependencia FastAPI que extrae y valida el JWT del header Authorization.

    Returns:
        TokenPayload con datos del usuario autenticado.

    Raises:
        HTTPException 401: Si no hay token, es inválido o ha expirado.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación. Incluye un Bearer token válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt_service.verify_access_token(credentials.credentials)
    except DomainError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return payload


def require_role(*roles: str) -> Callable:
    """
    Factory de dependencia FastAPI que verifica el rol del usuario autenticado.

    Args:
        *roles: Roles permitidos (e.g., "owner", "vet").

    Returns:
        Dependencia FastAPI que valida el rol y retorna el TokenPayload.

    Raises:
        HTTPException 403: Si el usuario no tiene el rol requerido.
    """

    async def _check_role(
        user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        if user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {', '.join(roles)}.",
            )
        return user

    return _check_role
