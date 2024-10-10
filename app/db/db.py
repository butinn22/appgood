from sqlalchemy.orm import sessionmaker,declarative_base
from sqlalchemy import create_engine,MetaData


##########################################

eng=create_engine("postgresql://postgres:Prosoft22@localhost/Stocks")

MySession=sessionmaker(autoflush=False,expire_on_commit=False,bind=eng)

MainBase=declarative_base()

md=MetaData()
