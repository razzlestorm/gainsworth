from sqlalchemy import (Column, Date, ForeignKey,
                        Integer, String)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    exercises = relationship('Exercise')
    date_created = Column(Date)

    def __repr__(self):
        return (f"<User(name='{self.name}', date_created='{self.date_created}')>\n"
                f"Exercises: {self.exercises}")


class Exercise(Base):
    __tablename__ = 'exercises'
    name = Column(String, primary_key=True, nullable=False)
    unit = Column(String)
    reps = Column(Integer)
    latest_date = Column(Date)
    user_id = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return (f"<Exercise(name='{self.name}', "
                f"unit='{self.unit}', latest_date='{self.latest_date}')>")
