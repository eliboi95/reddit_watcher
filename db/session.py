from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.config import DB_URL
from db.models import Base

engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """
    Function to initiate the DB if it doesnt exist. Only needs to be called once. If DB exists it doesnt do anything
    """
    Base.metadata.create_all(engine)
