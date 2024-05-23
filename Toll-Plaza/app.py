from flask import Flask, jsonify, request, render_template,json, redirect, url_for, session, abort, send_file, send_from_directory
from flask_pymongo import PyMongo
from pytz import timezone
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_session import Session
import gridfs
from bson import ObjectId
import json
import io
import pymongo
import os
import pyrebase
from PIL import Image


firebase_config = {
    'apiKey': "AIzaSyAAJ4Cv2d6cSSbRmnWQPll4kG4TvjdF-W8",
    'authDomain': "smooth-sailing-ad0d5.firebaseapp.com",
    'projectId': "smooth-sailing-ad0d5",
    'storageBucket': "smooth-sailing-ad0d5.appspot.com",
    'messagingSenderId': "62968749843",
    'appId': "1:62968749843:web:3bbe8560b1e73c0a3244e6",
    'measurementId': "G-E6EFBYWRML",
    'databaseURL': 'None'
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()


IST = timezone('Asia/Kolkata')

app = Flask(__name__)
database_name = "Users"


mongo_uri_temp = os.environ.get('MONGO_URI')

# Construct the actual MongoDB URI with the specified database name
mongo_uri = mongo_uri_temp.format(database_name=database_name)

# Initialize PyMongo with the constructed URI
mongo = PyMongo(app, uri=mongo_uri)
db = mongo.db

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

app.config["SESSION_TYPE"] = "mongodb"

# Set the MongoDB connection details for sessions
app.config["SESSION_MONGODB"] = pymongo.MongoClient(
   host=os.environ.get('HOST')
)

app.config["SESSION_MONGODB_DB"] = "UserSessions"
app.config["SESSION_MONGODB_COLLECT"] = "sessions"

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)
app.json_encoder = CustomJSONEncoder

Session(app)

CORS(app)


app.config["MONGO_URI_FOR_GRIDFS"] = os.environ.get('GRIDFS')

mongo_for_gridfs = PyMongo(app, uri=app.config["MONGO_URI_FOR_GRIDFS"])
fs = gridfs.GridFS(mongo_for_gridfs.db)


#----------------------- utility functions ----------------------------------------------------------------------

# ----------------------------------------------------------------------------------------------------------------



#-------------------------------------------- User Account -------------------------------------------------------
@app.get('/get_recent_transactions')
def get_recent_transactions():
    email = session.get('email')
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    # Query the UserWallets collection to get the list of transaction IDs
    user_wallet = db.UserWallets.find_one({'Email': email})

    if user_wallet:
        transaction_ids = user_wallet.get('Transactions', [])[-10:]

        # Query the CompletedPayments collection to get transaction details
        recent_transactions = []
        mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
        mongo = PyMongo(app, uri=mongo_uri)
        db = mongo.db
        gmt_to_ist_offset = timedelta(seconds=19800)
        for transaction_id in transaction_ids:
            payment_doc = db.CompletedPayments.find_one(
                {'_id': ObjectId(transaction_id)})
            if payment_doc:
                transaction_data = payment_doc.get('data', {})
                transaction_type = transaction_data.get('Type', 'Unknown')
                transaction_date = payment_doc.get('DateTime', '')
                # Convert the GMT time to IST
                gmt_time = transaction_date + gmt_to_ist_offset
                formatted_date = gmt_time.strftime('%H:%M %d-%m')
                
                transaction_amount = transaction_data.get('Amount', 0)
                gst = transaction_data.get('Gst', 0)
                cupon = transaction_data.get('Cupon', 0)
                disc = transaction_data.get('GlobalDiscount', 0)
                transaction_amount=round(transaction_amount+gst-cupon-disc,2)
                transaction_color = 'green' if transaction_type == 'Add Money' else 'red'
                transaction_sign = '+' if transaction_type == 'Add Money' else '-'

                recent_transactions.append({
                    'type': transaction_type,
                    'date': formatted_date,
                    'amount': transaction_amount,
                    'color': transaction_color,
                    'sign': transaction_sign,
                })

        return render_template('recent_transactions.html', recent_transactions=recent_transactions[::-1])
    else:
        return render_template('recent_transactions.html', recent_transactions=[])


@app.route('/get_image/<image_id>', methods=['GET'])
def get_image(image_id):
    try:
        # Retrieve the image data from GridFS using the provided image_id
        image_data = fs.get(ObjectId(image_id))

        response = send_file(io.BytesIO(image_data.read()),mimetype='image/jpeg')
        return response
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        # Get the uploaded file from the request
        uploaded_file = request.files['image']
        # Check if the file exists and is an allowed file type (e.g., image)
        if uploaded_file and allowed_file(uploaded_file.filename):
            # Read the uploaded file
            remove_profile_image()
            image_bytes = uploaded_file.read()
            # Compress the image to a specific size limit (e.g., 2.5 MB)
            max_file_size = 1 * 1024 * 1024  # 1.5 MB in bytes
            # Function to reduce the image quality while keeping dimensions the same
            def compress_image(image, quality):
                output = io.BytesIO()
                image.save(output, format="JPEG", quality=quality)
                return output.getvalue()

            quality = 87  # You can adjust this value as needed

            while len(image_bytes) > max_file_size:
                image_bytes = compress_image(
                    Image.open(io.BytesIO(image_bytes)), quality)
                quality -= 3  # Reduce the quality in steps

            # Store the compressed file in GridFS
            file_id = fs.put(image_bytes, filename=uploaded_file.filename)

            email = session.get('email')
            db.UserData.update_one(
                {"Email": email}, {"$set": {"image_id": file_id}}
            )

            db.UserData.update_one(
                {"Email": email}, {"$set": {"Defualt_Profile": False}}
            )

            return jsonify({"success": True, "message": "File uploaded and compressed successfully."})
        else:
            return jsonify({"success": False, "message": "Invalid file type or no file provided."})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/get_profile_image', methods=['GET'])
def get_profile_image():
    try:
        # Get the user's email from the session
        email = session.get('email')
        # Retrieve the user's profile image URL from the database
        user = db.UserData.find_one({"Email": email})

        if user and 'Profile_Url' in user:
            # Check if the user has a custom profile picture
            if user['Defualt_Profile']:
                # If the user has a default profile picture, use the 'Profile_Url' from the database
                return jsonify({"success": True, 'Default': True, "profile_url": user['Profile_Url']})
            elif 'image_id' not in user:
                return jsonify({"success": True, 'Default': False, "profile_url": user['Profile_Url']})

            else:
                # If the user has a custom profile picture, use their profile image URL as before
                # Convert ObjectId to string
                profile_url = str(user["image_id"])
                return jsonify({"success": True, 'Default': False, "profile_url": profile_url})

        return jsonify({"success": False, "message": "Profile image not found for this user."})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/remove_profile_image', methods=['POST'])
def remove_profile_image():
    print('in')
    try:
        # Get the user's email from the session or request
        email = session.get('email')
        # Check if the user has a profile picture in the database
        user_data = db.UserData.find_one({"Email": email})
        if user_data and "image_id" in user_data:
            # Delete the profile picture from database (MongoDB GridFS, for example)
            file_id = user_data["image_id"]
            fs.delete(file_id)

            # Update the user's data to remove the reference to the profile picture
            db.UserData.update_one(
                {"Email": email},
                {"$unset": {"image_id": ""}}
            )
            if user_data['Gender'] != 'others':
                db.UserData.update_one(
                    {"Email": email}, {"$set": {"Defualt_Profile": True}})
            return jsonify({"success": True, "message": "Profile picture removed successfully."})
        else:
            return jsonify({"success": False, "message": "No profile picture found for the user."})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})



@app.post('/Forgot_wallet_pass')
def change_wallet_pass():
    recieved=request.get_json()
    new_PIN=recieved['New'].strip()
    if len(new_PIN)!=4:
        abort(404)
    try:
        new_PIN=int(new_PIN)
        email = session.get('email')
    except:
        abort(404)
    db.UserWallets.update_one({'Email':email},{'$set':{'PIN':new_PIN^(turn_into_num(email)),'Default':False}})
    return jsonify({'success':True})


@app.route('/Edit_account',methods=['POST'])
def Edit_account():
    received = request.get_json()
    email = received.get('email','').lower()
    collection=db.UserData
    if not 'email' in session:
      abort(404)
    # Search for the user based on email
    user = collection.find_one({'Email': email})

    if user:
        # Update user data
        new_name = received.get('name')
        new_mobile = received.get('mobile')
        new_address = received.get('address')
        if (len(new_name) < 4 or len(new_name) > 40 or len(new_address)>100 or len(new_mobile)>=15):
            abort(404)

        update_data = {}
        if new_name:
            update_data['Name'] = new_name
        if new_mobile:
            update_data['Mobile'] = new_mobile

        update_data['Address'] = new_address

        # Update the user's data
        collection.update_one({'Email': email}, {'$set': update_data})

        return jsonify({'success':True}),200

    else:
        abort(404)

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------

@app.route('/Find_user',methods=['POST'])
def find_user():
  Recieved = request.get_json()
  User=db.UserData.find_one(Recieved)
  if User:
    return jsonify({'success': True}), 200
  abort(404)

@app.route('/Get_user_details',methods=['POST'])
def get_data():
  return find_user()


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').lower()
    password = data.get('Password', '')  # Get the password from the request
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    # Simplified authentication (replace with your authentication logic)
    user = mongo.db.UserData.find_one({"Email": email})
    if email=="dummy@gmail.com" and password=="123456":
        session['email'] = email
        return jsonify({'code': 200, 'message': 'Login Success'}), 200
    if (not user):
        return jsonify({'code': 404, 'message': 'User not Found! Sign Up instead'}), 404
    if (user["Suspended"]):
        return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        # Get user info and check if email is verified
        user_info = auth.get_account_info(user['idToken'])
        email_verified = user_info["users"][0]["emailVerified"]
        if email_verified:
            session['email']=email
            return jsonify({'code': 200, 'message': 'Login Success'}), 200
        else:
            #print("Email is not verified. Requesting a new ID token...")
            #new_id_token = user['idToken']
            return jsonify({'code': 405, 'message':'User Email not verified!'}), 405

    except Exception as e:
        error_message = str(e)
        # Find the start and end positions of the 'error' object
        start_idx = error_message.find('{')
        error_object = error_message[start_idx:]
        error = json.loads(error_object)
        error=error['error']
        error_message = ' '.join(error.get('message', 'Undefined').split('_'))
        return jsonify({'code': error.get('code', '400'), 'message':error_message}),  error.get('code', 400)


@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('name')
    mobile= data.get('mobile','')
    gender =data.get('gender',)
    if not (email and password and username and gender):
        return jsonify({'message':'Provide all the Fields!'}), 404
    try:
        res=Register_user(username, email, gender,mobile)
        # Create a new user in Firebase Authentication
        user = auth.create_user_with_email_and_password(email, password)
        # Send email verification
        auth.send_email_verification(user['idToken'])
        response_data = {
            'message': 'User registration successful. Email verification sent.',
        }
        
        if(res)
            return jsonify(response_data), 200

    except Exception as e:
       error_message = str(e)
       # Find the start and end positions of the 'error' object
       start_idx = error_message.find('{')
       error_object = error_message[start_idx:]
       error = json.loads(error_object)
       error = error['error']
       #print(error)
       error_message = ' '.join(error.get('message', 'Undefined').split('_'))
       return jsonify({'code': error.get('code', '400'), 'message': error_message}),  error.get('code', 400)


@app.route("/reset_password", methods=["POST"])
def reset_password():
    try:
        data = request.get_json()
        email = data.get("Email")

        if not email:
            return jsonify({"message": "Email is required"}), 400

        auth = firebase.auth()
        user = auth.send_password_reset_email(email)

        return jsonify({"message": "Password reset email sent successfully"}), 200
    except Exception as e:
       error_message = str(e)
       # Find the start and end positions of the 'error' object
       start_idx = error_message.find('{')
       error_object = error_message[start_idx:]
       error = json.loads(error_object)
       error = error['error']
       #print(error)
       error_message = ' '.join(error.get('message', 'Undefined').split('_'))
       return jsonify({'code': error.get('code', '400'), 'message': error_message}),  error.get('code', 400)



@app.route('/Log_out')
def Logout():
  session.pop('email',default=None)
  return redirect(url_for('index'))


@app.route('/profile', methods=['GET'])
def profile():
    #print(session)
    if 'email' in session:
        # Retrieve the user's email from the session
        email = session.get('email')
        user = db.UserData.find_one({"Email": email})
        wallet = db.UserWallets.find_one(
        {'Email': session.get('email')}, {'_id': False})
        if not user or not wallet:
            session.pop('email','')
            abort(404)
        if user['Suspended']:
            return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401
        if user:
            # Render the profile template with user data
            return render_template('Account.html', user=user,wallet=wallet)
        else:
            return jsonify("User not found")
    else:
        print("session empty")
        return redirect(url_for('index'))



@app.route('/Check_login', methods=['GET'])
def check_login():
    if 'email' not in session:
        return jsonify({'message': "Not Found!"}), 404
    else:
        projection = {
            "_id": 0,          # Exclude _id field
            "Gender": 0,
            "Mobile": 0, "Defualt_Profile": 0, "Profile_Url": 0, "Queries": 0, 'Email': 0,
            "RegistrationDate": 0, "Address": 0, "image_id": 0, "transactions": 0,
        }
        user = db.UserData.find_one({"Email": session.get('email')},projection)
        if(not user):
            abort(404)
        if user['Suspended']:
            session.pop('email')
            return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401
        else:
            return jsonify({'message': session.get('email'),"User":user}), 200
   
@app.route('/get_toll_rate')
def get_rate():
    mongo_uri = mongo_uri_temp.format(database_name='Toll_Rate')
    mongo2 = PyMongo(app, uri=mongo_uri)
    db=mongo2.db
    object_id = ObjectId("6510916ca24f1f9870537d5f")
    return jsonify(db.Rate.find_one({"_id": object_id},{"_id":False}))

@app.get('/verify_user')
def verify():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    return 'ok',200


@app.route('/discounts')
def get_discounts():
    rate = find_global_discount_rate()
    if(rate>0):
        return jsonify({'rate':rate})
    else:
        abort(404)


@app.post('/Apply_coupon')
def apply_cupon():
    data=request.get_json()
    print(data)
    cupon=data['cupon'].strip().lower()
    if(len(cupon)>=10 or cupon==''):
        abort(404)
    else:
        # Check if payment is requested
        payment_requested = session.get('PaymentRequested')
        if not payment_requested:
            # Handle the case where payment is not requested (e.g., redirect to a different page)
            session.pop('PaymentID', '')
            return abort(404)

        # Retrieve the payment ID from the session
        payment_id = session.get('PaymentID')
        if not payment_id:
            # Handle the case where payment ID is not found (e.g., redirect to a different page)
            return abort(404)

        # Retrieve payment data from MongoDB using the payment ID
        mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
        mongo = PyMongo(app, uri=mongo_uri)

        db = mongo.db
        collection = db.PaymentReferences
        payment_doc = collection.find_one({'_id': ObjectId(payment_id)})
        if not payment_doc:
            session.pop('PaymentRequested', '')
            session.pop('PaymentID', '')
            # Handle the case where payment data is not found (e.g., redirect to a different page)
            return abort(404)

        # Extract payment data from the document
        
        payment_data = payment_doc['data']
        if(payment_data['Type']=='Add Money'):
            abort(404)
        gross_amount = payment_data['Amount']-payment_data['GlobalDiscount']
        discount = round(calculate_cupon(gross_amount, cupon), 2)
        if(discount>0):
            payment_data['Cupon'] = discount
            collection.update_one(
                {'_id': ObjectId(payment_id)},
                {"$set": {"data.Cupon": discount}}
            )
        return jsonify({'success': True, 'Data':payment_data})

#----------------------------------------------------------------------------------------------------------------
#--------------------------------------------Payment Handler ----------------------------------------------------

@app.route('/pay', methods=['POST'])
def pay():
    PaymentInfo = request.get_json()
    Type = PaymentInfo['Type']
    mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    if (Type == 'Toll Payment'):
        Vehicle = PaymentInfo['Vehicle_Type'].strip().lower()
        Journey = PaymentInfo['Journey'].strip().lower()
        Number = PaymentInfo['Vehicle_Number'].strip()
        Amount = get_toll_amount(Vehicle, Journey)
        if Amount == 0:
            abort(404)
        Type = PaymentInfo['Type']
        Gst = round(calculate_gst(Amount), 2)
        if 'Cupon' in PaymentInfo:
            cupon_applied = PaymentInfo['Cupon'].strip()
        else:
            cupon_applied = 'None'
        Global_disc = round(get_Global_discount_amount(Amount), 2)
        cupon_discount = round(calculate_cupon(Amount, cupon_applied), 2)

        Data = {
            'Type': Type,
            'Amount': round(float(Amount), 2),
            "Gst": Gst,
            "Cupon": cupon_discount,
            'GlobalDiscount': Global_disc,
            'Number': Number
        }
    elif (Type=='Add Money'):
        Amount=PaymentInfo['Amount']
        if(Amount<=0):
            abort(404)
        Data = {
            'Type': Type,
            'Amount': round(float(Amount), 2),
            "Gst": 0,
            "Cupon": 0,
            'GlobalDiscount': 0,
        }
    # Store the payment data in MongoDB
    expiration_time = datetime.now() + timedelta(minutes=5)
    payment_doc = {
        'data': Data,
        'expiration_time': expiration_time
    }
    result = db.PaymentReferences.insert_one(payment_doc)

    # Set session variables
    session['PaymentRequested'] = True
    # Convert ObjectId to str for storage
    session['PaymentID'] = str(result.inserted_id)
    return redirect(url_for('complete_payment'))

@app.post('/store_pin')
def set_pin():
    recieved=request.get_json()
    PIN=recieved["user_pin"]
    try:
        PIN=int(PIN)
    except:
        abort(404)
    session['PIN']=PIN
    return jsonify({'success':True})

@app.route('/complete_payment', methods=['GET'])
def complete_payment():
    # Check if payment is requested
    payment_requested = session.get('PaymentRequested')
    if not payment_requested:
        # Handle the case where payment is not requested (e.g., redirect to a different page)
        session.pop('PaymentID', '')
        return abort(404)

    # Retrieve the payment ID from the session
    payment_id = session.get('PaymentID')
    if not payment_id:
        session.pop('PaymentRequested', '')
        # Handle the case where payment ID is not found (e.g., redirect to a different page)
        return abort(404)

    # Retrieve payment data from MongoDB using the payment ID
    mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    collection=db.PaymentReferences
    payment_doc = collection.find_one({'_id': ObjectId(payment_id)})
    if not payment_doc:
        session.pop('PaymentRequested', '')
        session.pop('PaymentID', '')
        # Handle the case where payment data is not found (e.g., redirect to a different page)
        return abort(404)

    # Extract payment data from the document
    payment_data = payment_doc['data']

    # Check if the payment data has expired
    expiration_time = payment_doc['expiration_time']
    current_time = datetime.now()
    if current_time > expiration_time:
        session.pop('PaymentRequested', '')
        session.pop('PaymentID', '')
        # Payment data has expired, delete the document and abort 404
        collection.delete_one({'_id': ObjectId(payment_id)})
        return abort(404)
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    wallet = db.UserWallets.find_one({'Email': session.get('email')},{'_id':False})
    if not wallet:
        wallet={'Logged_in':False,'Balance':0}
    else:
        wallet.update({'Logged_in':True})
    return render_template('Payment.html', PaymentInfo=payment_data,wallet=wallet)



@app.get('/get_payment_id')
def get_payment_id():
    if 'PaymentID' in session and 'PaymentRequested' in session:
        session.pop('PaymentRequested', '')
        payment_id = session.pop('PaymentID', '')
        # Create a MongoDB connection
        mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
        mongo = PyMongo(app, uri=mongo_uri)

        db = mongo.db
        # Get the payment data from PaymentReferences
        payment_doc = db.PaymentReferences.find_one(
            {'_id': ObjectId(payment_id)})

        if payment_doc:
            # Add the payment data to CompletedPayments with a reference number field set to the ID
            payment_doc['ReferenceNumber'] = str(payment_id)
            if 'email' in session:
                email = session.get('email')
                payment_doc['email']=email
                payment_doc['DateTime'] = datetime.now()
                insert_payment_id(email, str(payment_id))
            db.CompletedPayments.insert_one(payment_doc)

            # Delete the payment data from PaymentReferences
            db.PaymentReferences.delete_one({'_id': ObjectId(payment_id)})

        payment_data = payment_doc['data']
        if payment_data['Type']=='Add Money':
            mongo_uri = mongo_uri_temp.format(database_name='Users')
            mongo = PyMongo(app, uri=mongo_uri)

            db = mongo.db
            email = session.get('email')
            user_wallet = db.UserWallets.find_one({'Email': email})
            if payment_data['Amount'] > 5000 or payment_data['Amount']<=0:
                return jsonify({'success': False}), 400
            if user_wallet:
                # Update the user's wallet balance by adding payment_data['Amount']
                new_balance = round(user_wallet['Balance'] + payment_data['Amount'],2)
                new_added = user_wallet['Added']+payment_data['Amount']
                l = user_wallet['Transactions']
                l.append(str(payment_id))
                db.UserWallets.update_one(
                    {'Email': email}, {"$set": {"Balance": new_balance, 'Added': new_added, 'Transactions': l}})
            else:
                # Handle the case where the user's wallet document is not found
                print("User not found")
        del payment_doc["expiration_time"]
        payment_doc["ReferenceNumber"] = str(payment_doc["_id"])
        del payment_doc["_id"]
        payment_doc['email']=" Not Provided "
        payment_doc['DateTime'] = datetime.now()
        ist_offset = timedelta(minutes=330)
        payment_doc['DateTime'] += ist_offset
        return jsonify({"success": True, "message": str(payment_id),"data":payment_doc,"Login":'email' in session})
    else:
        return jsonify({"success": False, "message": "Payment data not found", "data": {}, "Login": 'email' in session})


@app.get('/update_user_wallet')
def update_wallet():
    payment_id = session.get('PaymentID')
    PIN=session.get('PIN')
    if not PIN or not payment_id:
        return jsonify({'success': False, 'message': "Payment Id not found!"}),400
    # Create a MongoDB connection
    mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    # Get the payment data from PaymentReferences
    payment_doc = db.PaymentReferences.find_one(
        {'_id': ObjectId(payment_id)})
    payment_data = payment_doc['data']
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo2 = PyMongo(app, uri=mongo_uri)
    db = mongo2.db
    email = session.get('email')
    user_wallet = db.UserWallets.find_one({'Email': email})
    stored_PIN=user_wallet['PIN']
    if(stored_PIN^(turn_into_num(email))!=PIN):
        print('No match')
        return jsonify({'failure': True,'message':"Wrong wallet PIN"}),400
    if user_wallet:
        Amount = payment_data['Amount']+payment_data['Gst'] - \
            payment_data['Cupon']-payment_data['GlobalDiscount']
        if (Amount > user_wallet['Balance']):
            return jsonify({'success': False, 'message': "Low wallet Balance"}),400
        # Update the user's wallet balance by adding payment_data['Amount']
        new_balance = round(user_wallet['Balance'] - Amount,2)
        new_spent = round(user_wallet['Spent'] + Amount,2)
        l=user_wallet['Transactions']
        l.append(str(payment_id))
        db.UserWallets.update_one(
            {'Email': email}, {"$set": {"Balance": new_balance, 'Spent': new_spent, 'Transactions':l}})
        return jsonify({'success':True})
    return jsonify({'success': False, 'message': "Unable to find user wallet"}),400

#---------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------

@app.get('/get_cupons')
def get_cupon_names():
    mongo_uri = mongo_uri_temp.format(database_name='Global_Discounts')
    mongo3 = PyMongo(app, uri=mongo_uri)
    db = mongo3.db
    obj = db.Cupons.find()
    for item in obj:
        del item['_id']
        data=list(item.items())
        data.sort(key=lambda a:a[0],reverse=True)
        break

    return jsonify({'success':True,'data':data})


@app.get('/load_recent_transactions')
def load_recent_transactions():
    # Check if the user is logged in and their email is stored in the session
    if 'email' in session:
        user_email = session['email']
        db_users = db
        # Find the user document by their email
        user_data = db_users.UserData.find_one({'Email': user_email})

        if user_data and 'transactions' in user_data:
            # Get the list of transactions from the user's data
            transactions = user_data['transactions']

            mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
            mongo4 = PyMongo(app, uri=mongo_uri)
            db_payment = mongo4.db

            # Find the recent 5 transactions based on ReferenceNumber
            projection = {'_id': 0}

            # Find the recent 5 transactions based on ReferenceNumber
            recent_transactions = list(
                db_payment.CompletedPayments.find(
                    {'ReferenceNumber': {'$in': transactions}},
                    projection=projection
                ).limit(30).sort([('ReferenceNumber', -1)])
            )

            # 5 hours 30 minutes in minutes
            ist_offset = timedelta(minutes=330)

            # Add the IST offset to each transaction's DateTime field
            for transaction in recent_transactions:
                if 'DateTime' in transaction:
                    transaction['DateTime'] += ist_offset

            # You now have the recent transactions with IST-adjusted DateTime
            return jsonify({'success': True, 'transactions': recent_transactions})
        else:
            return jsonify({'success': False})
    else:
        return jsonify({'success': False, 'message': 'User not logged in'})
#----------------------------------------- super admin------------------------------------------------------------

@app.route('/users', methods=['GET'])
def get_users():
    if 'email' not in session:
        abort(401)
    user=db.UserData.find_one({'Email':session.get('email')})
    if not user['IsSuperAdmin']:
        return jsonify({'message':'Unauthorized Access!!'}),401
    users = l())
    return render_template('Create_Admin.html',users=users)


@app.route('/admins', methods=['GET'])
def get_admins():
    if 'email' not in session:
        abort(401)
    user = db.UserData.find_one({'Email': session.get('email')})
    if not user['IsSuperAdmin']:
        return jsonify({'message': 'Unauthorized Access!!'}), 401
    users = get_admins_from_db()
    return render_template('Delete_Admin.html', users=users)



# Define a route to make new admins
@app.route('/make_admin', methods=['POST'])
def make_admins():
    if 'email' not in session:
        abort(401)
    user = db.UserData.find_one({'Email': session.get('email')})
    if not user['IsSuperAdmin']:
        abort(401)
    data = request.get_json()
    if not data or 'data' not in data or 'Password' not in data:
        return jsonify({"error": "Invalid JSON data"}), 400
    email_list = data['data']
    if len(data['Password']) !=4:
        return jsonify({'message': "Provide Passcode"}), 400
    try:
        password=int(data['Password'])
    except:
        return jsonify({'message':"Wrong Passcode"}),401

    object_id = ObjectId("6521104419f8ab8aac121d6e")
    key= db.SuperAdminKey.find_one({"_id": object_id})['key']
    if(password!=key):
        return jsonify({'message': "Wrong Passcode"}), 400

    current_user_data = db.UserData.find_one({'Email': session.get('email')})
    if not current_user_data or not current_user_data.get("IsSuperAdmin"):
        return jsonify({"message": "Unauthorized Access"}), 401

    suspend=data.get('suspend')
    activate=data.get('activate')
    collection=db.UserData
    for email in suspend:
        collection.update_one(
            {"Email": email.lower()}, {"$set": {"Suspended": True}})
    for email in activate:
        collection.update_one(
            {"Email": email.lower()}, {"$set": {"Suspended": False}})
    for email in email_list:
        if email not in suspend:
            collection.update_one(
                {"Email": email.lower()}, {"$set": {"IsAdmin": True}})

    return jsonify({"message": "Users updated successfully"})


# Define a route to delete admin privileges
@app.route('/delete_admin', methods=['POST'])
def delete_admin():
    # Check if the user is authenticated
    if 'email' not in session:
        abort(401)
    # Check if the user is a super admin
    user = db.UserData.find_one({'Email': session.get('email')})
    if not user or not user['IsSuperAdmin']:
        abort(401)

    # Get the data from the POST request
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Invalid JSON data"}), 400

    email_list = data['data']
    if len(email_list) == 0:
        return jsonify({'message': "Bad request"}), 400
    if len(data['Password']) !=4:
        return jsonify({'message': "Provide Passcode"}), 400
    try:
        password=int(data['Password'])
    except:
        return jsonify({'message':"Wrong Passcode"}),401

    object_id = ObjectId("6521104419f8ab8aac121d6e")
    key = db.SuperAdminKey.find_one({"_id": object_id})['key']
    if (password != key):
        return jsonify({'message': "Wrong Passcode"}), 400
    # Update the IsAdmin field for the specified emails to False
    collection = db.UserData
    for email in email_list:
        collection.update_one({"Email": email.lower()}, {
                              "$set": {"IsAdmin": False}})

    return jsonify({"message": "Admin privileges removed successfully"})


#----------------------------------------------------Admin---------------------------------------------------

@app.route('/update_toll_rate', methods=['POST'])
def update_toll_rate():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    try:
        # Get the JSON data from the request
        data = request.json
        mongo_uri = mongo_uri_temp.format(database_name='Users')
        mongo3 = PyMongo(app, uri=mongo_uri)
        
        db = mongo3.db
        object_id = ObjectId("6521102ce322c40be74694b2")
        key = db.AdminKey.find_one({"_id": object_id})['key']
        key2 = db.SuperAdminKey.find_one(
            {"_id": ObjectId("6521104419f8ab8aac121d6e")})['key']
        # Check if the provided password is correct (replace 'your_password' with your actual password)
        user = db.UserData.find_one({'Email': session.get('email')})

        passcode = int(data.get('Password'))
        if passcode == key2 and not user['IsSuperAdmin']:
            return jsonify({"message": "Wrong Passcode"}), 401
        if passcode != key and passcode!=key2:
            return jsonify({"message": "Wrong Passcode"}), 401

        dataArray = data.get('dataArray')
        # Validate dataArray to ensure no negative values
        for item in dataArray:
            for category in ["single", "return", "monthly"]:
                if item.get(category) is not None and item[category] < 0:
                    return jsonify({"message": f"Negative value in {category} for {format_vehicle_type_name(item['vehicleType'])}. Please enter a non-negative value."}), 400
            if item['single'] >= item['return'] :
                return jsonify({"message": f"Invalid rate values for {format_vehicle_type_name(item['vehicleType'])}. Please ensure that single rate is less than return rate."}), 400
            if item['return'] >= item['monthly']:
                return jsonify({"message": f"Invalid rate values for {format_vehicle_type_name(item['vehicleType'])}. Please ensure that return rate is less than monthly rate."}), 400
        mongo_uri = mongo_uri_temp.format(database_name='Toll_Rate')
        mongo2 = PyMongo(app, uri=mongo_uri)
        db = mongo2.db
        collection=db.Rate
        # Update the MongoDB document based on the dataArray
        # Assuming you have a document with a specific ObjectId you want to update (replace 'your_object_id' with the actual ObjectId)
        object_id = ObjectId("6510916ca24f1f9870537d5f")
        for item in dataArray:
            vehicle_type = item['vehicleType']
            update_data = {
                'single': float(item['single']), 'return': float(item['return']), 'monthly': float(item['monthly'])
            }
            # Update the specific vehicle type data in the MongoDB collection
            collection.update_one({'_id': ObjectId(object_id)}, {
                                '$set': {vehicle_type: update_data}})
            update_data.clear()
        return jsonify({"message": "Toll Rate updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"message": "Internal Server Error"}),500


@app.post("/modify_discounts")
def modify_discounts():
    data=request.get_json()
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    
    db = mongo.db
    user = db.UserData.find_one({'Email': session.get('email')})
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    try:
        # Get the JSON data from the request
        data = request.json
        object_id = ObjectId("6521102ce322c40be74694b2")
        key = db.AdminKey.find_one({"_id": object_id})['key']
        key2 = db.SuperAdminKey.find_one(
            {"_id": ObjectId("6521104419f8ab8aac121d6e")})['key']
        passcode = int(data.get('Password'))
        if passcode == key2 and not user['IsSuperAdmin']:
            return jsonify({"message": "Wrong Passcode"}), 401
        if passcode != key and passcode != key2:
            return jsonify({"message": "Wrong Passcode"}), 401
        mongo_uri = mongo_uri_temp.format(database_name='Global_Discounts')
        mongo3 = PyMongo(app, uri=mongo_uri)
        
        db = mongo3.db
        GlobalDiscount=data.get('Global')
        Newcupon=data.get('NewCupon').lower()
        Newrate = data.get('NewRate')
        Tollrate=data.get('TollRate')

        if GlobalDiscount>=0 and GlobalDiscount<100:
            db.Discount.update_one({"_id": ObjectId('6510a31f5c761cfa640a15f0')}, {
                '$set': {'discountRate':int(GlobalDiscount)}})
        if len(Newcupon) > 8 and not Newcupon.isalnum():
            return jsonify({'message': 'Coupon should be atmost 8 characters and Alphanumeric.'}), 400
        elif len(Newcupon)>0 and len(Newcupon)<10 and Newrate>0 and Newrate<=100:
            db.Cupons.update_one({"_id": ObjectId('6511c1e74b3276cf2afcf700')},
                {'$set':{Newcupon:int(Newrate)}})

        for key in Tollrate :
            if not key.isalnum():
                continue
            elif int(Tollrate[key])<=0:
                db.Cupons.update_one(
                    {"_id": ObjectId('6511c1e74b3276cf2afcf700')},
                    {'$unset': {key: ""}} )
            else:
                db.Cupons.update_one({"_id": ObjectId('6511c1e74b3276cf2afcf700')},
                                     {'$set': {key: int(Tollrate[key])}})

        return jsonify({'message': 'Updates Sucessfull'}), 200

    except Exception as e:
        return jsonify({"message": "Internal Server Error"}), 500



@app.route('/make_query', methods=['POST'])
def make_query():
    data = request.get_json()
    email = data.get('email', '').lower()
    if 'email' in session and email!=session.get('email'):
        return jsonify({'message': 'Email Ids do not match! '}),400

    mongo_uri = mongo_uri_temp.format(database_name='Queries')
    mongo = PyMongo(app, uri=mongo_uri)
    db = mongo.db
    collection = db['User_Queries']
    data['Pending']=True
    data['Resolved']=False
    data['Query_Time'] = datetime.now()
    # Insert the data into the MongoDB collection
    result = collection.insert_one(data)
    inserted_id = str(result.inserted_id)  # Convert the ObjectId to a string
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    
    db = mongo.db
    print(data)
    user = db.UserData.find_one({'Email': email})
    if user:
        if 'Queries' not in user:
                # Create 'transactions' field as a list with the first ID
            user['Queries'] = [inserted_id]
        else:
            user['Queries'].append(inserted_id)
            # Update the user document in the database
        db.UserData.update_one({'Email': email}, {
            '$set': {'Queries': user['Queries']}})

    return jsonify({'message': f'Query submitted successfully. Reference Id: {inserted_id}'}),200


@app.route('/get_queries', methods=['GET'])
def get_queries():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    mongo_uri = mongo_uri_temp.format(database_name='Queries')
    mongo = PyMongo(app, uri=mongo_uri)
    
    collection = mongo.db.User_Queries
    queries = list(collection.find({'Pending': True}))
    serialized_queries = []
    for query in queries:
        query['_id'] = str(query['_id'])  # Convert ObjectId to string
        serialized_queries.append(query)
    return jsonify({'queries': serialized_queries[::-1]})


@app.route('/resolve_queries', methods=['POST'])
def resolve_query():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    mongo_uri = mongo_uri_temp.format(database_name='Queries')
    mongo = PyMongo(app, uri=mongo_uri)
   
    db = mongo.db
    collection = db['User_Queries']
    try:
        data = request.get_json()
        query_id = data.get('queryId')
        input_text = data.get('inputText')

        # Update the query in the MongoDB collection
        query = collection.find_one({"_id": ObjectId(query_id)})
        if query:
            # Mark the query as resolved
            collection.update_one({"_id": ObjectId(query_id)}, {
                                  "$set": {"Pending": False, "Resolved": True, "Resolve_Time": datetime.now(), "Response": input_text}})
            return jsonify({'message': 'Query resolved successfully!'})

        return jsonify({'error': 'Query not found'}, 404)

    except Exception as e:
        return jsonify({'message': 'Error resolving query', 'details': str(e)}), 500


@app.route('/get_user_queries', methods=['GET'])
def get_user_queries():
    if 'email' not in session:
        return jsonify({'queries':[], 'visited': True})
    mongo_uri = mongo_uri_temp.format(database_name='Users')
    mongo = PyMongo(app, uri=mongo_uri)
    
    collection = mongo.db.UserData
    # Replace with how you retrieve the session email
    session_email = session.get('email','')
    # Find the user by session email
    mongo_uri = mongo_uri_temp.format(database_name='Queries')
    mongo2 = PyMongo(app, uri=mongo_uri)
    
    queries_collection = mongo2.db.User_Queries
    user = collection.find_one({"Email": session_email})
    ist_offset = timedelta(minutes=330)
    if user:
        User_Queries = user.get('Queries', [])[::-1]
        visited=True
        user_queries = []
        for query_id in User_Queries:
            query = queries_collection.find_one({"_id": ObjectId(query_id)})
            if visited and query['Resolved'] and 'visited' not in query:
                visited=False
            if query and query.get('Resolved'):
                user_queries.append({
                    "_id":str(query.get('_id')),
                    "Time":query.get('Resolve_Time')+ist_offset,
                    "Message": query.get('message'),
                    "Response": query.get('Response')
                })

        return jsonify({'queries':user_queries,'visited':visited})

    return jsonify({'queries': [], 'visited':True}), 404


@app.get('/mark_visited')
def mark_visited():
   mongo_uri = mongo_uri_temp.format(database_name='Users')
   mongo = PyMongo(app, uri=mongo_uri)
   
   collection = mongo.db.UserData
   session_email = session.get('email', '')
   mongo_uri = mongo_uri_temp.format(database_name='Queries')
   mongo2 = PyMongo(app, uri=mongo_uri)
   
   queries_collection = mongo2.db.User_Queries
   user = collection.find_one({"Email": session_email})
   if user:
        Queries = user.get('Queries', [])[::-1]
        for last_query in Queries:
            query=queries_collection.find_one({"_id": ObjectId(last_query)})
            if query['Resolved'] :
                if 'visited' not in query:
                    queries_collection.update_one({"_id": ObjectId(last_query)}, {'$set': {'visited': True}})
                else:
                    break
   return jsonify({"message": "success"}),200


@app.route('/', methods=['GET'])
def index():
  return render_template("Home.html")


@app.get('/favicon.ico')
def favicon():
    return send_from_directory('./static',
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
    

@app.route('/favicon.png')
def favicon_png():
    return send_from_directory('./static', 'favicon.png', mimetype='image/png')

# -------------------------------------------------------------------------------------------------------------------
# ---------------------------------admin only request--------------------------------------------------------------
@app.get('/get/<string:id>')
def get_user(id):
    if not check_user():
        return jsonify({"message":"Unauthorized access!!"}),401
    mongo_uri = mongo_uri_temp.format(database_name='PaymentDetails')
    mongo = PyMongo(app, uri=mongo_uri)
    collection = mongo.db.CompletedPayments
    data = collection.find_one({"_id": ObjectId(id)}, {"_id": False, "expiration_time":False})
    if not data:
        return jsonify({"message":"No Records Found!!"})
    return jsonify(data)

if __name__ == "__main__":

    app.run(port=8080)

