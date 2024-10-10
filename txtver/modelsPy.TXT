from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime, timezone

########### Models (Classes)



class User(BaseModel):
    id: str  
    pw: str
    username: str
    email: EmailStr
    real_name: Optional [str]
    real_surname: Optional [str]
    is_active: Optional [bool] = True

    def create_unique_ID(self):
        if self.id is None:
            self.id= str(uuid.uuid4())
            return self.id
        else:
            return self.id


class Stock(BaseModel):
    idofrequest: str
    id_stock: str
    ticker: str
    current_price: float

class UserTasks(BaseModel):
    id_task: str
    user_id: str
    bodytask: str
    created_at: datetime
    in_process: bool


class DataRequester(BaseModel):
    id_request: str
    time: str = datetime.now(timezone.utc).isoformat()  

