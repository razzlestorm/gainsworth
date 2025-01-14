from datetime import datetime

from .models import Base, Exercise, User

from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


if __name__ == "__main__":
    url = config("DATABASE_URL")
    if url:
        if "postgresql" not in url:
            url = url.replace("postgres", "postgresql")
    engine = create_engine(url)
    Session = sessionmaker(bind=engine)

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
