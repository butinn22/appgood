#########################
import requests
from fastapi import HTTPException, status
from db.db import MySession
import hashlib
from models.modelsPy import Stock
from db.classes import Stocks,Users



users_base: dict = {}
blacklist=set()
main_url= "https://api.binance.com/api/v3/ticker/price"




def get_stock_data(ticker: str):
        response = requests.get(main_url + "?symbol=" + ticker)
        if response.status_code == 200:
            data = response.json()
            current_price = float(data['price'])
            return current_price
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stock not found")


def hash_string(input_string: str) -> str:
    hash_object = hashlib.sha256()
    hash_object.update(input_string.encode('utf-8'))
    return hash_object.hexdigest()
    


def create_stock(db: MySession, stock_data: Stock):
    db_stock = Stocks(
        idrequest=stock_data.idofrequest,
        id=hash_string(stock_data.id_stock),
        ticker=stock_data.ticker,
        current_price=stock_data.current_price,
    )
    
    with db() as session:
        session.add(db_stock)
        session.commit()
        session.refresh(db_stock)       



def validate_pass(pw: str) -> bool:
    if len(pw)<8 or pw.isalpha()==True or pw.isdigit()==True or pw.isspace()==True:
        return False
    else:
        return True
    
def update_users_base(db: MySession):
    with db() as conn:
        listof_users=conn.query(Users.username,Users.pw, Users.email).all()
        for i in listof_users:
            users_base[i.username]=(i.pw,i.email)
    return users_base


