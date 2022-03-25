import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# sqlite connection
#SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"

# postgres connection
#SQLALCHEMY_DATABASE_URL = "postgresql://postgres:12345@localhost/postgres"

SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL')
print(SQLALCHEMY_DATABASE_URL)
print(type(SQLALCHEMY_DATABASE_URL))

"""if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql:", 1)"""


# mysql connection
#SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:test1234!@127.0.0.1:3306/todoapp"

engine = create_engine(
    #solo para sqlite
    SQLALCHEMY_DATABASE_URL, connect_args = {"check_same_thread": False}
   
    #SQLALCHEMY_DATABASE_URL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
