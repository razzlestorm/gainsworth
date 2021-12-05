from datetime import datetime

from .models import Base, Exercise, User

from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def recreate_database():
    engine = create_engine(config("DATABASE_URL"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    engine = create_engine(config("DATABASE_URL"))
    Session = sessionmaker(bind=engine)

    recreate_database()
    ses = Session()
    name = User(name="Razzlestorm", date_created=datetime.utcnow())
    exercise = Exercise(name="push-ups",
                        reps=0,
                        date=datetime.utcnow())
    ses.add(name)
    ses.add(exercise)
    ses.commit()
    print("checking if connection creates user: ")
    print(ses.query(User).first().name, ses.query(User).first().date_created)
    print("checking if connection creates exercise: ")
    print(ses.query(Exercise).first().name, ses.query(Exercise).first().reps)
    ses.close_all()
    recreate_database()
