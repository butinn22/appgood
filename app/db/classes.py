from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from db.db import MainBase,eng
#### DB SCHEMAS
#Блок подключения БД





class Users(MainBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(256), nullable=False, unique=True)
    pw = Column(String(256), nullable=False)
    email = Column(String(256), nullable=False, unique=True)
    real_name = Column(String(50))
    real_surname = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    


class Stocks(MainBase):
    __tablename__ = 'stocks'

    
    id=Column(String, primary_key=True, unique=True)
    ticker=Column(String,nullable=False,unique=True)
    current_price=Column(Float, nullable=False)
    created_at=Column(DateTime,unique=False)
    updated_at=Column(DateTime, unique=False)
    idrequest=Column(String, unique=True)


class Tasks(MainBase):
    __tablename__='tasks'
    id=Column(Integer, primary_key=True, nullable=False, unique=True)
    body=Column(String(500), nullable=False)
    created_at=Column(DateTime, unique=False)
    updated_at=Column(DateTime, unique=False)
    user_id=Column(String)
    in_prog=Column(Boolean, default=False)

    

MainBase.metadata.create_all(bind=eng)# Создание базы данных Postgres при старте
