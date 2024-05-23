from datetime import datetime, timedelta
from pytz import timezone

from utils.helper import turn_into_num

def get_user(email:str)->dict:
    return None

def get_cupon_rates()->dict:
    pass

def insert_payment_id(email:str, id):
    # Find the user by email
    user = db.UserData.find_one({'Email': email})
    if user:
        # Check if the 'transactions' field exists
        if 'transactions' not in user:
            # Create 'transactions' field as a list with the first ID
            user['transactions'] = [id]
        else:
            # Append the ID to the existing list
            user['transactions'].append(id)
        # Update the user document in the database
        db.UserData.update_one({'Email': email}, {
            '$set': {'transactions': user['transactions']}})
    else:
        return
    
def get_gst_rate()->float:
    mongo_uri = mongo_uri_temp.format(database_name='Toll_Rate')
    mongo2 = PyMongo(app, uri=mongo_uri)
    db = mongo2.db
    object_id = ObjectId("6511be0f6cae5e50b4f30e34")
    return db.GST.find_one({"_id": object_id}, {"_id": False})['rate']

def get_global_discount_rate()->float:
    pass

def get_rate_chart()->dict:
    pass




def Register_user(name:str, email:str, gender:str, mobile:str)->bool:
  Recieved = {'Email': email.lower(), 'Name': name,
              'Gender': gender, 'Mobile': mobile}
  if (len(name) < 4 or len(name) > 30):
    return False
  if gender == 'male':
    Recieved.update(
        {"Defualt_Profile": True, 'Profile_Url': 'Male.avif'})
  elif gender == 'female':
    Recieved.update({"Defualt_Profile": True,
                    'Profile_Url': 'Female.avif'})
  else:
    Recieved.update({"Defualt_Profile": False,
                    'Profile_Url': 'Generic.png'})

  Recieved.update(
      {'IsAdmin': False, "IsSuperAdmin": False,"Suspended":False, 'RegistrationDate': datetime.now(), 'Address': ' '})
  Wallet = {'Name': name, 'Email': Recieved['Email'], 'Default': True, 'PIN': 1234 ^ (
      turn_into_num(email)), 'Balance': 0.00, 'Added': 0.00, 'Spent': 0.00, 'Transactions': []}
  if(create_user(Recieved) and create_wallet(Wallet)):
      return True
  return False
  

  
def create_user(Received:dict)->bool:
    pass

def create_wallet(Wallet:dict)->bool:
    pass


def get_users_from_db()->list:
    collection=db.UserData
    # Projection to include only specific fields
    projection = {
        "_id": 0,          # Exclude _id field
        "Gender": 0,
        "Mobile": 0, "Defualt_Profile": 0, "Profile_Url": 0,
        "RegistrationDate": 0, "Address": 0, "image_id": 0, "transactions": 0,
    }

    # Fetch documents with the specified projection
    users = list(collection.find({}, projection))
    l=[]
    for user in users:
        if not (user['IsAdmin'] or user['IsSuperAdmin']):
            l.append(user)
    return l


def get_admins_from_db()->list:
    collection = db.UserData
    # Projection to include only specific fields
    projection = {
        "_id": 0,          # Exclude _id field
        "Gender": 0,
        "Mobile": 0, "Defualt_Profile": 0, "Profile_Url": 0,'Queries':0,
        "RegistrationDate": 0, "Address": 0, "image_id": 0, "transactions": 0,
    }

    # Fetch documents with the specified projection
    users = list(collection.find({}, projection))
    l=[]
    for user in users:
        if user['IsAdmin']:
            l.append(user)
    return l
