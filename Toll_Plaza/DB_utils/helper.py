from datetime import datetime, timedelta
from pytz import timezone
from random import randint
from __init__ import db
from DB_utils.models import *
from sqlalchemy.inspection import inspect
from flask_session import Session
from sqlalchemy.orm import  joinedload
from sqlalchemy import delete
from flask import session
from sqlalchemy.sql import func
import os
from PIL import Image
import io
from werkzeug.utils import secure_filename


def extract_file_path_from_url(url):
    """Extract the file path from the Supabase storage URL."""
    file_path_index = url.rfind('/')  # Find the last '/'
    if file_path_index != -1:
        file_path = url[file_path_index + 1:]  # Extract the file path
        return file_path
    return None

def model_to_dict(model_instance):
    """Converts a SQLAlchemy model instance into a dictionary."""
    return {c.key: getattr(model_instance, c.key) for c in inspect(model_instance).mapper.column_attrs}

def serialize(model_list,get_list:bool=True):
    """Converts a list of SQLAlchemy model instances to a list of dictionaries."""
    if not model_list:
        return [] if get_list else None
    response=[model_to_dict(model_instance) for model_instance in model_list]
    if len(response)==0:
        return None
    if get_list:
        return response
    return response[0]


def turn_into_num(s:str)->int:
    sum = 0
    for i in s:
        sum += ord(i)
    return sum

def fetch_user(email:str,user_id:uuid=None)->User:
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
    
def fetch_wallet(email:str,user_id:uuid=None,user:User=None)->Wallet:
    if user:
        return user.wallet
    #TODO
    if user_id:
        response=db.session.query(Wallet).filter_by(
            id=user_id
        ).first()
        return response
    return None

def compress_image(file, max_size_mb):
    max_size = max_size_mb * 1024 * 1024  # Convert MB to bytes
    image_bytes = file.read()
    def compress(image, quality):
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality)
        return output.getvalue()

    quality = 85 # You can adjust this value as needed

    while len(image_bytes) > max_size:
        image_bytes = compress(
            Image.open(io.BytesIO(image_bytes)), quality)
        quality -= 4
    return image_bytes

def upload_to_bucket(file, supabase,user_id:uuid) -> bool:
    if not user_id:
        return False
    filename = secure_filename(file.filename)
    try:
        # Compress the image
        compressed_image= compress_image(file, max_size_mb=1.25)
        
        # Upload to Supabase storage
        bucket_name = 'profile-pics'
        upload_path = f"uploads/{filename}"
        
        image_data = compressed_image

        # Ensure the image data is not empty
        if len(image_data) == 0:
            print('empty compression')
            return False
        
        response = supabase.storage.from_(bucket_name).upload(
            upload_path, image_data, {"content-type": file.mimetype}
        )
        # Check if upload was successful
        if response.status_code == 200:
            return update_user_pic_url('https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/'\
                +upload_path,user_id,False,supabase)
        return False
    except Exception as e:
        error_message = str(e)
        if 'Duplicate' in error_message:
            return update_user_pic_url('https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/'\
                +upload_path,user_id,False,supabase)
        return False
   
   
def update_user_pic_url(url:str='',user_id:uuid=None,unset:bool=False,supabase=None)->bool:
    if not user_id:
        return False
    user=fetch_user('',user_id)
    if unset:
        url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Generic.png?t=2024-06-19T20%3A04%3A55.450Z'
        gender=user.gender
        if gender=="male":
            url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Male.avif?t=2024-06-19T20%3A05%3A18.030Z'
        elif gender=='female':
            url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Female.avif?t=2024-06-19T20%3A05%3A47.617Z'
    file_path = extract_file_path_from_url(user.pic_url)
    # Delete the file from Supabase storage
    try:
        supabase.storage.from_('profile-pics').remove('uploads/'+file_path)
    except Exception as e:
        pass
    try:
        user.pic_url=url
        db.session.commit()
        return True
    except:
        db.session.rollback()
        return False
     
    
def fetch_user_queries(email: str, user_id: uuid = None) -> tuple:
    try:
        data=db.session.query(Query).filter(
            Query.user_id==user_id,Query.solved==True
        ).order_by(Query.query_time.desc()).all()
        return serialize(data)
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

def set_user_id(user:User):
    try:
        session.modified = True
        user_session = db.session.query(ExtendedSession).filter(
            ExtendedSession.session_id==session.sid
        ).first()
        if user_session:
            user_session.user_id = user.id
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print('Error: ',e)

def fetch_coupon_rate(code:str)->float:
    code=code.lower()
    if(code=='global'):
        return 0
    data=db.session.query(Discounts).filter(
        Discounts.name==code
    ).first()
    return data.rate if data else 0

def fetch_global_discount_rate()->float:
    disc=db.session.query(Discounts).filter(
        Discounts.name=='global'
    ).first()
    return disc.rate if disc else 0

def fetch_coupons()->list:
    all_data=db.session.query(Discounts).all()
    return serialize(all_data)

def check_passcode(passcode:str)->tuple[bool,str]:
    passcode=str(passcode)
    admin_key=db.session.query(AccessKey).filter(
        AccessKey.name=='admin_key'
    ).first()
    super_key=db.session.query(AccessKey).filter(
        AccessKey.name=='super_key'
    ).first()
    user=fetch_user(session.get('email'),session.get('user_id'))
    if not user or (not user.is_admin and not user.is_super_admin):
        return False,'Unauthorized Access!!'
    if passcode !=admin_key.value and passcode!=super_key.value:
        return False,'Wrong access key provided.'
    if passcode==super_key.value and not user.is_super_admin:
        return False,'Wrong access key provided.'
    return True,'ok'

def update_discount_coupons(data:dict)->tuple[bool,str]:
    try:
        passcode = data.get('Password')
        check,reason=check_passcode(passcode)
        if not check:
            return check,reason

        GlobalDiscount=float(data.get('Global'))
        Newcupon=data.get('NewCupon').lower()
        Newrate = float(data.get('NewRate'))
        Coupons=data.get('discountRate')
        print(data)
        if GlobalDiscount>=0 and GlobalDiscount<100:
            data=db.session.query(Discounts).filter(
               Discounts.name=='global'
            ).first()
            if data:
                data.rate=GlobalDiscount
                
            
        if len(Newcupon) > 8 and not Newcupon.isalnum():
            return False,'New Coupon should be atmost 8 characters and Alphanumeric.'
        elif len(Newcupon)>0 and len(Newcupon)<10 and Newrate>0 and Newrate<=100:
            new_coupon=Discounts(
                name=Newcupon,rate=Newrate
            )
            db.session.add(new_coupon)
        for coupon in Coupons :
            key=coupon['name']
            value=coupon['rate']
            if key=='global':
                continue
            if not key.isalnum():
                continue
            elif float(value)<=0:
                db.session.query(Discounts).filter(
                    Discounts.name==key.lower()
                ).delete()
            else:
                rate=float(value)
                Coupon=db.session.query(Discounts).filter(Discounts.name==key.lower()).first()
                if Coupon:
                    Coupon.rate=rate
        db.session.commit()
        return True,"Changes made successfully!"
    except Exception as e:
        print(e)
        db.session.rollback()
        return False,"Something went wrong internally! "


def fetch_toll_rates()->dict[dict]:
    all_data=db.session.query(TollRate).all()
    response=dict()
    for toll_rate in all_data:
        if toll_rate.vehicle_type not in response:
            response[toll_rate.vehicle_type] = {}

        response[toll_rate.vehicle_type][toll_rate.journey_type] = toll_rate.rate
    
    return response

def update_toll_rate(data:dict)->tuple[bool,str]:
    password=data.get('Password')
    result,reason=check_passcode(password)
    if not result:
        return result,reason
    toll_data=data.get('dataArray')
    try:
        for toll_detail in toll_data:
            vehicle=toll_detail.get('vehicleType','').strip().lower()
            for type in ['single','return','monthly']:
                rate=float(toll_detail.get(type))
                entry=db.session.query(TollRate).filter(
                    TollRate.vehicle_type==vehicle,
                    TollRate.journey_type==type
                ).first()
                if entry:
                    entry.rate=rate
                    
        db.session.commit()
        return True,'Toll details updated successfully! '
    except Exception as e:
        print(e)
        db.session.rollback()
        return False,"Internal error! "


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

def update_coupon_amount(payment_data:PaymentData,discount:float)->bool:
    if not payment_data or payment_data.type=='add money':
        return False
    try:
        payment_data.coupon_disc=discount
        db.session.commit()
        return True
    except:
        db.session.rollback()
        return False

def store_new_user(user:dict)->bool:
    try:
        # Create a new User instance
        url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Generic.png?t=2024-06-19T20%3A04%3A55.450Z'
        gender=user.get('gender','')
        if gender=="male":
            url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Male.avif?t=2024-06-19T20%3A05%3A18.030Z'
        elif gender=='female':
            url='https://rcikbpsmkgltabgfmcpd.supabase.co/storage/v1/object/public/profile-pics/Female.avif?t=2024-06-19T20%3A05%3A47.617Z'
        dummy_user = User(
            name=user["name"],
            email=user["email"],
            pic_url=url,
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
        Gst_row=db.session.query(Gst).filter(
            Gst.name==code
        ).first()
        return Gst_row.rate if Gst_row else 0
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
        
def get_all_transactions_by_user(email:str,user_id:uuid=None) -> list:
    fetch_recent_transactions(email,user_id,1000)


def fetch_recent_transactions(email:str,user_id:uuid=None,n:int=10) -> list:
  # Use eager loading, filter by completed transactions, and order by created_at descending
  #TODO implement query find with email
  if not user_id:
      return []
  transactions = db.session.query(PaymentData) \
                         .filter_by(user_id=user_id, completed=True) \
                         .order_by(PaymentData.created_at.desc()) \
                         .limit(n) \
                         .all()
  return serialize(transactions)


def store_payment_data(data:PaymentData)->bool:
    try:
        db.session.add(data)
        db.session.commit()
        return True
    except:
        db.session.rollback()
        return False
    
def fetch_payment_data(payment_id:uuid)->PaymentData:
    try:
        data=db.session.query(PaymentData).filter_by(
            id=payment_id
        ).first()
        return data
    except:
        return None
    
def delete_payment_data(payment_id:uuid):
    try:
        db.session.query(PaymentData).filter_by(
            id=payment_id
        ).delete()
    except:
        pass
    
def mark_payment_completed(payment_id:uuid)->PaymentData:
    try:
        data=db.session.query(PaymentData).filter_by(
            id=payment_id
        ).first()
        data.completed=True
        data.expire_time=func.now()
        db.session.commit()
        return data
    except:
        db.session.rollback()
        return None
    
def add_wallet_id_to_transaction(payment_data:PaymentData,user_wallet:Wallet)->bool:
    if not user_wallet or not payment_data:
        return False
    try:
        payment_data.wallet_id=user_wallet.id
        db.session.commit()
        return True
    except:
        db.sessison.rollback()
        return False
    
def update_wallet(amount:float,payment_data:PaymentData,spent:bool=False)->bool:
    payment_data.wallet_id=session.get('user_id',None)
    if not payment_data.wallet_id:
        print(payment_data.wallet_id)
        return False
    try:
        wallet=fetch_wallet('',session.get('user_id',None))
        if spent:
            if(round(amount,2) >wallet.balance):
                return False
            wallet.balance-=round(amount,2) 
            wallet.spent+=round(amount,2)
        else: 
            wallet.balance+=round(amount,2) 
            wallet.added+=round(amount,2)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        db.session.rollback()
        return False
    
    
def fetch_unresolved_queries()->list:
    try:
        queries=db.session.query(Query).filter_by(
            solved=False
        ).order_by(Query.query_time.asc()).all()
        return serialize(queries) if queries else []
    except:
        return []
    
def store_query(email:str,message:str,user_id:uuid=None)->uuid:
    try:
       new_query=Query(
           user_id=user_id,message=message,email=email )
       db.session.add(new_query)
       db.session.commit()
       return new_query.query_id
    except Exception as e:
        print(e)
        return None

def fetch_all_users()->list[User]:
    try:
        users=db.session.query(User).filter(
            User.is_admin==False,User.is_super_admin==False
        ).order_by(User.name.asc()).all()
        return serialize(users)
    except:
        return []
    
    
def update_users(data:dict)->tuple[bool,str]:
    make_admins=data.get('data',[])
    suspend=data.get('suspend',[])
    activate=data.get('activate',[])
    password=data.get('Password','')
    result,reason=check_passcode(password)
    if not result:
        return result,reason
    make_admins=[email for email in make_admins if email not in suspend]
    try:
        for email in make_admins:
            user=fetch_user(email.lower())
            user.is_admin=True
        for email in activate:
            user=fetch_user(email.lower())
            user.suspended=False
        for email in suspend:
            user=fetch_user(email.lower())
            user.suspended=True
        db.session.commit()
        return True,"Users modified successfully."
    except:
        db.session.rollback()
        return False,'Invalid data'
    
def remove_admin_privilage(data:dict)->tuple[bool,str]:
    password=data.get('Password','')
    result,reason=check_passcode(password)
    if not result:
        return result,reason
    email_list = data.get('data',[])
    try:
        for email in email_list:
            user=fetch_user(email.lower())
            user.is_admin=False

        db.session.commit()
        return True,'ok'
    except:
        db.session.rollback()
        return False,'Something went wrong! '
    
    
def fetch_admins()->list[User]:
    try:
        admins=db.session.query(User).filter(
            User.is_admin==True,User.is_super_admin==False
        ).order_by(User.name.asc())\
        .all()
        return serialize(admins)
    except:
        return []

def resolve_query(data:dict,answer_by:uuid=None)->bool:
    try:
        query:Query=db.session.query(Query).filter(
            Query.query_id==data.get('queryId','')
        ).first()
        if query and not query.solved:
            query.response=data.get('inputText')
            query.answer_by=answer_by
            query.solved=True
            query.solved_on=func.now()
            query.seen=False

            db.session.commit()
            return True
    except:
        db.session.rollback()
        return False
    
def mark_queries_seen(user_id:uuid=None):
    try:
        queries=db.session.query(Query).filter(
            Query.solved==True,Query.seen==False,Query.user_id==user_id
        ).all()
        for query in queries:
            query.seen=True
        
        db.session.commit()
    except:
        db.session.rollback()