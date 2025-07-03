from typing import Annotated, Optional
from fastapi import HTTPException, Header, status, Depends
from jose import JWTError, jwt
from pydantic import BaseModel
from core.config import logger, jwt_config
                

class TokenData(BaseModel):
    """Data model for JWT token payload."""
    user_id: Optional[str] = None
    username: Optional[str] = None

def _create_unauthorized_exception(detail: str) -> HTTPException:
    """Create a standardized HTTP 401 Unauthorized exception.

    Args:
        detail: Description of the error.

    Returns:
        HTTPException: Unauthorized exception with WWW-Authenticate header.
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(token: Annotated[Optional[str], Header(alias="Authorization")] = None) -> TokenData:
    """Validate JWT token and extract user data.

    Args:
        token: Authorization header containing Bearer token.

    Returns:
        TokenData: Parsed token data with user_id and username.

    Raises:
        HTTPException: If token is missing, invalid, or cannot be validated.
    """
    if not token:
        logger.warning("Authorization header missing")
        raise _create_unauthorized_exception("Not authenticated: Authorization header missing")

    parts = token.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning(f"Invalid authorization header format: {token}")
        raise _create_unauthorized_exception("Invalid authorization header format")

    token_value = parts[1]
    try:
        payload = jwt.decode(token_value, jwt_config.secret_key, algorithms=[jwt_config.algorithm])
        user_id: Optional[str] = payload.get("user_id")
        username: Optional[str] = payload.get("username")
        if user_id is None:
            logger.warning(f"JWT missing 'user_id' claim. Payload: {payload}")
            raise _create_unauthorized_exception("Could not validate credentials")
        token_data = TokenData(user_id=user_id, username=username)
        logger.debug(f"Token validated for user_id: {user_id}, username: {username}")
        return token_data
    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise _create_unauthorized_exception("Could not validate credentials")
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {str(e)}")
        raise _create_unauthorized_exception("Could not validate credentials")

CurrentUser = Annotated[TokenData, Depends(get_current_user)]
