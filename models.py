from sqlalchemy import Column, Float, Integer, DateTime
from db import Base
from datetime import datetime

class SensorData(Base):

    __tablename__ = 'SensorData'

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    carbondioxide = Column(Integer)
    voc = Column(Integer)

    def __init__(self, temperature, humidity, carbondioxide, voc):
        self.humidity = humidity
        self.temperature = temperature
        self.carbondioxide = carbondioxide
        self.voc = voc

