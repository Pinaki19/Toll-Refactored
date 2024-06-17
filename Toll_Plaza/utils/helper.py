from flask import session
from random import randint
from DB_utils.helper import *
from DB_utils.helper import *

def check_user():
    if 'email' not in session:
        return False
    user = get_user(email=session.get('email'))
    if not user or not user['IsAdmin'] and not user['IsSuperAdmin']:
        return False
    return True

def turn_into_num(s:str)->int:
    sum = 0
    for i in s:
        sum += ord(i)
    return sum+randint(999,99999)


def format_vehicle_type_name(name:str)->str:
    if name.startswith("axel"):
        parts = name.split("_")

        if len(parts) > 2:
            return f"{parts[1]} to {parts[2]} Axel"
        return f"{parts[1]} Axel"
    else:
        return name.capitalize()

def get_cupon_discount_rate(code:str)->int:
    obj=get_cupon_rates()
    return obj.get(code,0)


def calculate_gst(amount:float)->float:
    rate = get_gst_rate()
    return (amount/100)*rate


def calculate_cupon(amount:float, code:str)->float:
    rate = get_cupon_discount_rate(code)
    return (amount/100)*rate


def get_Global_discount_amount(amount:float)->float:
    rate = get_global_discount_rate()
    if (rate <= 0 or rate>100):
        return 0
    return (amount/100)*rate



def allowed_file(filename:str)->bool:
    # Define the allowed file extensions (e.g., for images)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions




def get_toll_amount(vehicle:str, journey:str)->float:
    Rate_chart = get_rate_chart()
    if vehicle in Rate_chart:
        if journey in Rate_chart[vehicle]:
            return Rate_chart[vehicle][journey]
    return 0



