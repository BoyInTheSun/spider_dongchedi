from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, BigInteger, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

engine = create_engine('sqlite:///commets.sqlite')


class Review(Base):
    __tablename__ = 'REVIEWS'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger)
    user_name = Column(String(255))
    brand_id = Column(BigInteger)
    brand_name = Column(String(255))
    car_id = Column(BigInteger)
    car_name = Column(String(255))
    create_time = Column(DateTime)
    series_id = Column(BigInteger)
    series_name = Column(String(255))
    content = Column(Text)
    bought_time = Column(DateTime)


if __name__ == '__main__':
    Base.metadata.create_all(engine)
    