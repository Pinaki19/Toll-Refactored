from datetime import datetime, timedelta
from pytz import timezone
from random import randint
from __init__ import db
from DB_utils.models import *

def turn_into_num(s:str)->int:
    sum = 0
    for i in s:
        sum += ord(i)
    return sum+randint(999,99999)

def get_user(email:str)->dict:
    return None

def get_cupon_rates()->dict:
    pass


def fetch_toll_rates():
    all_data=db.session.query(TollRate).all()
    response=dict()
    for toll_rate in all_data:
        if toll_rate.vehicle_type not in response:
            response[toll_rate.vehicle_type] = {}

        response[toll_rate.vehicle_type][toll_rate.journey_type] = toll_rate.rate
    
    return response
