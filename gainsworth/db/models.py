import enum

from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Enum, Integer, String, Date

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    date_created = Column(Date)

    def __repr__(self):
        return f"<User(name='{self.name}', date_created='{self.date_created}')>"


class ResultType(enum.Enum):
    time = 'time'
    quantity = 'quantity'


class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    reps = Column(Integer)
    result = Column(Enum(ResultType))
    latest_date = Column(Date)

    def __repr__(self):
        return (f"<Exercise(name='{self.name}', reps='{self.reps}', 
                result='{self.result}', latest_date='{self.latest_date}')>")




