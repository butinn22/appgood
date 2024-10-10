from fastapi import HTTPException, status,FastAPI, Request
import uvicorn
from pydantic import EmailStr
from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from utils import get_stock_data,hash_string
import uuid
from datetime import datetime,timedelta,timezone
from auth.jwt import create_access_token,get_current_user_by_token, validate_token, TIME_LIFE_TOKEN
from utils import validate_pass, update_users_base,blacklist,users_base
from db.db import MySession
from db.classes import MainBase
from db.classes import Users,Tasks,Stocks
from models.modelsPy import User,UserTasks,Stock,DataRequester


ourapp=FastAPI()



# Инициализация лимитера
limiter = Limiter(key_func=get_remote_address)

# Привязка лимитера к состоянию приложения
ourapp.state.limiter = limiter

@ourapp.get("/{ticker}", response_model= Stock)
def req_data_from_api(ticker: str):
    unique_id=str(uuid.uuid4())
    data_reqer=DataRequester(id_request= unique_id , time=datetime.now(timezone.utc).isoformat())
    data_from_api= {data_reqer.id_request: get_stock_data(ticker)}
    re_stock=Stock(idofrequest=unique_id ,id_stock=hash_string(ticker), ticker=ticker, current_price=get_stock_data(ticker))
    create_stock(MySession,re_stock)
    return re_stock



###############################

@ourapp.post("/register")
def reg_user(un: str, pw: str, email: EmailStr) -> User:
    users_base_state = update_users_base(MySession)
    if users_base_state == {}:
        db = MySession()  
        if validate_pass(pw) == True:
            novel_user=User(id=str(uuid.uuid4()), username=un, pw=pw, email=email,created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
            with db:  
                db_user = Users(username=un, pw=pw, email=email)  
                db.add(db_user)
                db.commit()
                db.refresh(db_user)
            return novel_user 
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Слишком легкий пароль. Учтите правила!")
    else:
        if un not in users_base_state:
            if validate_pass(pw) == True:
                novel_user=User(id=str(uuid.uuid4()), username=un, pw=pw, email=email,created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
                db = MySession()  
                with db:  
                    db_user = Users(username=un, pw=pw,email=email)  
                    db.add(db_user)
                    db.commit()
                    db.refresh(db_user)
                return novel_user
            else:
                raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Слишком легкий пароль. Учтите правила!")
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Такой пользователь уже есть")
        


@ourapp.post("/get_token")
def enter_user_by_login(un: str, pw: str):
        users_base_state=update_users_base(MySession)
        if users_base_state=={}:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="нет такого пользователя")
        elif un not in users_base_state:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="нет такого пользователя")
        else:
            if pw != users_base_state.get(un)[0]:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Введен неверный пароль")
            else:
                access_token = create_access_token(data={"sub": un}, expires_delta= TIME_LIFE_TOKEN)  
                return {"access_token": access_token, "token_type": "bearer", un : "внесён в систему с ключом"}


# Функция Login (проверка токена)
@ourapp.post("/login")
@limiter.limit(limit_value=100)
def login_user(token: str , request: Request):
    username = validate_token(token)
    return {username : "Статус : В сети"}

# Функция Logout (добавление токена в чёрный список)
@ourapp.post("/logout")
def logout_user(token: str):
    username = validate_token(token)
    blacklist.add(token)  # Добавляем токен в чёрный список
    return {username: "Сессия завершена. Статус : не в сети"}



#################################################  Тут пилим таски
# создание новой таски
@ourapp.post("/{username}/tasks", response_model=UserTasks)
def create_new_task(text_of_task: str, token: str):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db=MySession()
    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Создаём новую таску как объект ПД и ниже как пайдентик
    novel_task_id=str(uuid.uuid4())
    new_task = Tasks(
        body=text_of_task,
        user_id=current_user,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        in_prog=True
    )
    new_task_m=UserTasks(id_task=novel_task_id, bodytask=text_of_task, user_id=current_user, created_at=datetime.now(timezone.utc), in_process=True)
    
    with db as session:
        session.add(new_task)
        session.commit()
        session.refresh(new_task)

    return new_task_m



#######################################
# Функция для получения всех задач пользователя
@ourapp.get("/{username}/tasks")
def get_personal_tasks(token: str ):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db=MySession()
    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Получаем все задачи пользователя
    tasks = db.query(Tasks).filter(Tasks.user_id == current_user).all()
    if not tasks:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет задач")
    else:
        existed_tasks = [(i,UserTasks(id_task=it.id, user_id=current_user, bodytask=it.body, created_at=it.created_at, in_process=it.in_prog)) for i, it in enumerate(tasks)]
        return existed_tasks

    # Возвращаем список задач


##################################################
# Функция для получения задачи по её ID
@ourapp.get("/{username}/tasks/{id}", response_model=UserTasks)
def get_task_by_id(id: str, token: str):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db=MySession()
    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Ищем задачу по ID и пользователю
    task = db.query(Tasks).filter(Tasks.id == id, Tasks.user_id == current_user).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    else:
        existed_task=UserTasks(id_task=id, user_id=current_user,bodytask=task.body, created_at=task.created_at, in_process=task.in_prog)  

    return existed_task
############################################

################################################## 
# Функция для получения задачи по её ID
@ourapp.get("/{username}/tasks/{id}", response_model=UserTasks)
def get_task_by_id(id: str, token: str):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db=MySession()
    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Ищем задачу по ID и пользователю
    task = db.query(Tasks).filter(Tasks.id == id, Tasks.user_id == current_user).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    else:
        existed_task=UserTasks(id_task=id, user_id=current_user,bodytask=task.body, created_at=task.created_at, in_process=task.in_prog)

    return existed_task

##########################################################

@ourapp.put("/{username}/tasks/{task_id}", response_model=UserTasks)
def update_task(task_id: str, text_of_task: str, token: str):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db = MySession()

    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Находим задачу по ID и пользователю
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == current_user).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    # Обновляем данные задачи
    task.body = text_of_task
    task.updated_at = datetime.now(timezone.utc)

    with db as session:
        session.commit()
        session.refresh(task)

    updated_task = UserTasks(
        id_task=task_id,
        user_id=current_user,
        bodytask=task.body,
        created_at=task.created_at,
        in_process=task.in_prog
    )
    return updated_task

#####################################

@ourapp.delete("/{username}/tasks/{task_id}")
def delete_task(task_id: str, token: str):
    # Получаем текущего пользователя по токену
    current_user = get_current_user_by_token(token)
    db = MySession()

    # Проверяем наличие пользователя в базе
    user = db.query(Users).filter(Users.username == current_user).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    # Находим задачу по ID и пользователю
    task = db.query(Tasks).filter(Tasks.id == task_id, Tasks.user_id == current_user).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    # Удаляем задачу
    db.delete(task)
    db.commit()

    return {"сообщение": "Задача успешно удалена"}

#############################################



if __name__ == "__main__":
    uvicorn.run("main:ourapp", host="127.0.0.53", port=8080, log_level="info", reload=True)

