from __init__ import db
from sqlalchemy import BigInteger, Text, TIMESTAMP,String, Integer,Double,DateTime,Boolean,CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy
from flask.sessions import SessionInterface, SessionMixin
import uuid
import pickle
from flask import session

class ExtendedSession(db.Model):
    __tablename__ = 'useressions'
    __table_args__ = {'extend_existing':True}

    id=db.Column(Integer,primary_key=True)
    session_id = db.Column(db.String(50))
    data = db.Column(db.LargeBinary, nullable=False)
    expiry = db.Column(DateTime, nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True,default=None)

    def __repr__(self):
        return f"<ExtendedSession(session_id={self.session_id}, user_id={self.user_id})>"

    def __init__(self, session_id, data, expiry, user_id=None):
        self.session_id = session_id
        self.data = data
        self.expiry = expiry
        self.user_id = user_id    

    
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    name = db.Column(String(35),nullable=False)
    email = db.Column(String(50),nullable=False, index=True, unique=True)
    pic_url= db.Column(String(255),nullable=False)
    address = db.Column(String(100))
    gender = db.Column(String(10),default=None)
    mobile = db.Column(String(15),default='+91 0000000000')
    is_admin =db.Column(Boolean,default=False)
    is_super_admin=db.Column(Boolean,default=False)
    registered_on= db.Column(DateTime(timezone=True),default=func.now())
    suspended=db.Column(Boolean,default=False)
    
    transactions= db.relationship('PaymentData',back_populates='user')
    wallet=db.relationship('Wallet',back_populates='user',uselist=False)
    queries = db.relationship('Query', back_populates='user', foreign_keys='Query.user_id')
    def __repr__(self):
        return f'<User {self.name}>'

class Query(db.Model):
    __tablename__ = 'queries'
    query_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    user_id = db.Column(UUID,db.ForeignKey('users.id'),nullable=True,default=None)
    message = db.Column(Text,nullable=False)
    response = db.Column(Text,nullable=True,default=None)
    solved= db.Column(Boolean,default=False)
    answer_by= db.Column(UUID,db.ForeignKey('users.id'),nullable=True,default=None)
    seen= db.Column(Boolean,default=False)
    query_time= db.Column(DateTime(timezone=True),default=func.now())
    solved_on= db.Column(DateTime(timezone=True),default=None)
    
    user= db.relationship('User',back_populates='queries',uselist=False,foreign_keys=[user_id])
   
    
        
class Wallet(db.Model):
    __tablename__='wallets'
    id = db.Column(UUID(as_uuid=True), primary_key=True)
    pin= db.Column(Integer,nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), unique=True, nullable=False)
    balance= db.Column(Double,nullable=False,default=0.0)
    added= db.Column(Double,nullable=False,default=0.0)
    spent= db.Column(Double,nullable=False,default=0.0)

    default = db.Column(Boolean,default=True)
    user = db.relationship('User', back_populates='wallet', uselist=False,foreign_keys=[user_id])
    wallet_transactions=db.relationship('PaymentData',back_populates='wallet',foreign_keys='PaymentData.wallet_id')
    
    def __repr__(self):
        return f'<Wallet for User {self.user_id}>'
    
class Discounts(db.Model):
    __tablename__= 'discounts'
    name= db.Column(String(20),primary_key=True)
    rate=db.Column(Double,CheckConstraint('rate<=100'),nullable=False,unique=True)
    def __repr__(self):
        return f"<Discount(name={self.name},rate={self.rate})>"

class Gst(db.Model):
    __tablename__ ='gst'
    name = db.Column(String(20),primary_key=True)
    rate= db.Column(Double,CheckConstraint('rate>=0'),nullable=False)
    
    def __repr__(self):
        return f"<Gst(name={self.name},rate={self.rate})>"
    
class TollRate(db.Model):
    __tablename__ = 'toll_rates'
    vehicle_type = db.Column(String(30),nullable=False)
    journey_type= db.Column(String(20),nullable=False)
    rate = db.Column(Double,CheckConstraint('rate>=0'),nullable=False)
    __table_args__ = (
        db.PrimaryKeyConstraint('vehicle_type','journey_type'),
    )
    def __repr__(self):
        return f"<TollRate(vehicle_type={self.vehicle_type}, journey_type={self.journey_type}, rate={self.rate})>"
    
class PaymentData(db.Model):
    __tablename__= 'payment_data'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4())
    wallet_id = db.Column(UUID,db.ForeignKey('wallets.id'),nullable=True)
    amount=db.Column(Double,nullable=False)
    coupon_disc=db.Column(Double,nullable=False)
    global_disc=db.Column(Double,nullable=False)
    gst_applied=db.Column(Double,nullable=False)
    vehicle_number=db.Column(String(20),nullable=True)
    type=db.Column(String(30),nullable=False)
    user_id=db.Column(UUID, db.ForeignKey('users.id'),nullable=True)
    created_at=db.Column(DateTime(timezone=True),default=func.now())
    expire_time=db.Column(DateTime(timezone=True),nullable=False,default=func.now() + func.text("'5 minutes'"))
    completed = db.Column(Boolean,nullable=False,default=False)
    user=db.relationship('User',back_populates='transactions',uselist=False)
    wallet=db.relationship('Wallet',back_populates='wallet_transactions',foreign_keys=[wallet_id])
    

class AccessKey(db.Model):
    __tablename__ = 'keys'
    
    name = db.Column(String(20), primary_key=True)
    value = db.Column(String(25),nullable=False)
    