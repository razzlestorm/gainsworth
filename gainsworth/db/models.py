from sqlalchemy import Boolean, BigInteger, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    name = Column(String, nullable=False)
    exercises = relationship('Exercise', cascade="all, delete")
    date_created = Column(DateTime)
    last_active = Column(DateTime)
    auto_remove = Column(Boolean, default=True, nullable=False)
    reminder_interval = Column(Integer)

    def __repr__(self):
        return (f"<User(name='{self.name}', date_created='{self.date_created}')>\n"
                f"Exercises: {self.exercises}")


class Exercise(Base):
    __tablename__ = 'exercises'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    unit = Column(String)
    reps = Column(Numeric(precision=12, scale=2))
    date = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"))

    def __repr__(self):
        return (f"<Exercise(name='{self.name}', unit='{self.unit}', "
                f"reps='{self.reps}', date='{self.date}')>")
