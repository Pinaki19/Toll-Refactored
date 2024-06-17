from datetime import datetime, timedelta
from pytz import timezone
from random import randint
from __init__ import db
from DB_utils.models import *
from sqlalchemy.inspection import inspect
from flask_session import Session
from sqlalchemy.orm import  joinedload
from sqlalchemy import delete

def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance into a dictionary."""
    return {c.key: getattr(model_instance, c.key) for c in inspect(model_instance).mapper.column_attrs}
def serialize(model_list):
    """Converts a list of SQLAlchemy model instances to a list of dictionaries."""
    response=[model_to_dict(model_instance) for model_instance in model_list]
    if len(response)==0:
        return None
    if len(response)>1:
        return response
    return response[0]


def turn_into_num(s:str)->int:
    sum = 0
    for i in s:
        sum += ord(i)
    return sum

def fetch_user(email:str,user_id:uuid=None)->object:
    if user_id:
        response=db.session.query(User).filter(
            User.id == user_id
        ).first()
        return response
    else:
        response=db.session.query(User).filter(
            User.email== email
        ).first()
        return response

def fetch_coupon_rate(code:str)->float:
    code=code.lower()
    if(code=='global'):
        return 0
    rate=db.session.query(Discounts.rate).filter(
        Discounts.name==code
    ).first()
    return rate if rate else 0

def fetch_global_discount_rate()->float:
    rate=db.session.query(Discounts.rate).filter(
        Discounts.name=='global'
    ).first()
    return rate if rate else 0

def fetch_coupons()->list:
    all_data=db.session.query(Discounts).all()
    return serialize(all_data)


def fetch_toll_rates()->dict[dict]:
    all_data=db.session.query(TollRate).all()
    response=dict()
    for toll_rate in all_data:
        if toll_rate.vehicle_type not in response:
            response[toll_rate.vehicle_type] = {}

        response[toll_rate.vehicle_type][toll_rate.journey_type] = toll_rate.rate
    
    return response

def store_cupon(name:str,rate:float)->bool:
    if(rate<=0 or rate>100):
        return False
    try:
        coupon=db.session.query(Discounts).filter(
            Discounts.name==name
        ).first()
        if coupon:
            coupon.rate=rate
        else:  
            new_coupon=Discounts(name=name.lower(),rate=rate)
            db.session.add(new_coupon)
        db.session.commit()
        return True
    except:
        db.session.rollback()
        return False


def store_new_user(user:dict)->bool:
    try:
        # Create a new User instance
        dummy_user = User(
            name=user["name"],
            email=user["email"],
            pic_url=user["pic_url"],
            address=user.get('address',''),
            gender=user["gender"],
            mobile=user.get('mobile','')
        )

        # Add the user to the session
        db.session.add(dummy_user)
        db.session.flush()  # Ensure user is added and has an ID assigned

        # Create a new Wallet instance with user's ID and a new UUID for Wallet's ID
        new_wallet = Wallet(
            id=dummy_user.id,
            user_id=dummy_user.id,
            pin= 1234^(turn_into_num(dummy_user.email))
        )

        # Add the wallet to the session
        db.session.add(new_wallet)

        # Commit the session to persist changes
        db.session.commit()

        return True, dummy_user.id
    except Exception as e:
        print(f"Error storing new user and wallet: {e}")
        db.session.rollback()
        return False, None
    
    
def fetch_gst_rate(code:str='gst')->float:
    try:
        rate=db.session.query(Gst).filter(
            Gst.name==code
        ).first()
        return rate if rate else 0
    except:
        db.session.rollback()
        return 0
    
    
def update_wallet_password(email:str,new_pass:int)->bool:
    email=email.lower()
    try:
        user=db.session.query(User).filter(
            User.email==email
        ).first()
        if not user:
            return False
        user.wallet.pin=new_pass^(turn_into_num(email))
        user.wallet.default=False
        db.session.commit()
    except:
        db.session.rollback()
        return False
    
def update_user(email:str,user_id:uuid,received:dict)->bool:
    user=fetch_user(email,user_id)
    if user:
        # Update user data
        try:
            if 'name' in received:
                user.name = received.get('name')
            if 'mobile' in received:
                user.mobile = received.get('mobile')
            if 'address' in received:
                user.address = received.get('address')
            db.session.commit()
            return True
        except:
            return False
    return False


def delete_session():
    try:
        session.clear()
        db.session.query(ExtendedSession).filter(
            ExtendedSession.session_id==session.sid
        ).delete()
        db.session.commit()
    except:
        print('Unable to delete session')
        db.session.rollback()
        
def get_all_transactions_by_user(user_id:uuid) -> list:
    transactions = db.session.query(PaymentData) \
                        .filter_by(user_id=user_id) \
                        .options(joinedload(PaymentData.user)) \
                        .order_by(PaymentData.created_at.desc()) \
                        .all()
    
    delta=timedelta(minutes=5)
    expired_transactions = [transaction for transaction in transactions if not transaction.completed and (transaction.expire_time-transaction.created_at)>delta]
    try:
        db.session.delete(expired_transactions)
        db.session.commit()
    except:
        db.session.rollback()
    return transactions


def fetch_recent_transactions(user_id,n:int=10) -> list:
  # Use eager loading, filter by completed transactions, and order by created_at descending
  transactions = db.session.query(PaymentData) \
                         .filter_by(user_id=user_id, completed=True) \
                         .order_by(PaymentData.created_at.desc()) \
                         .limit(n) \
                         .all()

  return transactions
