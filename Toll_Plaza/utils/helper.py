from flask import session
from random import randint
from DB_utils.helper import *
from DB_utils.helper import *

def check_user(verify_super_user:bool=False)->bool:
    if 'email' not in session or 'user_id' not in session:
        return False
    user = fetch_user(email=session.get('email'),user_id=session.get('user_id',None))
    if verify_super_user and not user.is_super_admin:
        return False
    if not user or not user.is_admin and not user.is_super_admin:
        return False
    return True

def valid_user()->bool:
    if 'email' not in session or 'user_id' not in session:
        return False
    return True

def turn_into_num(s:str)->int:
    sum = 0
    for i in s:
        sum += ord(i)
    return sum


def format_vehicle_type_name(name:str)->str:
    if name.startswith("axel"):
        parts = name.split("_")
        if len(parts) > 2:
            return f"{parts[1]} to {parts[2]} Axel"
        return f"{parts[1]} Axel"
    else:
        return name.capitalize()

def calculate_gst(amount:float)->float:
    rate = fetch_gst_rate()
    return (amount/100)*rate


def calculate_cupon(amount:float, code:str)->float:
    rate = fetch_coupon_rate(code)
    return (amount/100)*rate


def get_Global_discount_amount(amount:float)->float:
    rate =  fetch_global_discount_rate()
    if (rate <= 0 or rate>100):
        return 0
    return (amount/100)*rate



def allowed_file(filename:str)->bool:
    # Define the allowed file extensions (e.g., for images)
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def get_toll_amount(vehicle:str, journey:str)->float:
    Rate_chart = fetch_toll_rates()
    if vehicle in Rate_chart:
        if journey in Rate_chart[vehicle]:
            return Rate_chart[vehicle][journey]
    return 0



