import jwt
from datetime import datetime, timedelta,timezone
from typing import Optional
import secrets
from fastapi import HTTPException, status
from utils import update_users_base,blacklist,users_base
from db.db import MySession

#####################

#### JWT PART

# Настройки JWT

SECRET_KEY = secrets.token_urlsafe(32)
ALG = "HS256"  
TIME_LIFE_TOKEN = 30.0



def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + timedelta(minutes=TIME_LIFE_TOKEN)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALG)
        return encoded_jwt
    else:
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALG)
        return encoded_jwt



def get_current_user_by_token(token: str):
    users_base_state = update_users_base(MySession)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALG])
        username: str = payload.get("sub")
        if username is None or username not in users_base_state:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Что-то не так с именем пользователя")
        else:
            return username
    except EOFError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"У вас нет доступа по JWT, инфо {e}")

            
def validate_token(token: str):
    if token in blacklist:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен недействителен, выполните повторный вход")
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALG])
        username: str = payload.get("sub")
        expire = payload.get("exp")
        
        # Проверяем время жизни токена
        if datetime.fromtimestamp(expire, timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Токен истёк")
        
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен")
        
        return username
    except EOFError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный токен или истек срок действия")
