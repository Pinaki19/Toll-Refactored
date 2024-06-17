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
from PIL import Image
from utils.helper import *
from DB_utils.helper import *
from Auth.helper import *
IST = timezone('Asia/Kolkata')
from __init__ import create_app,db

app = create_app()

CORS(app)

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
        email = session.get('email','')
    except:
        abort(404)
    result=update_wallet_password(email,new_PIN)
    if result:
        abort(404)
    return jsonify({'success':result}),200


@app.route('/Edit_account',methods=['POST'])
def Edit_account():
    received = request.get_json()
    email = received.get('email','').lower()
    if 'email' not in session or not session.get('user_id',None) or email!=session.get('email',''):
        abort(404)
    result=update_user(email,session.get('user_id',None),received)
    if result:
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
    # Assuming fetch_user is a function that retrieves the user object based on email
    user = fetch_user(email)
    if email == "dummy@gmail.com" and password == "123456":
        session['email'] = email
        session['user_id']=user.id
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
        return jsonify({'code': 200, 'message': 'Login Success'}), 200

    if not user:
        return jsonify({'code': 404, 'message': 'User not Found! Sign Up instead'}), 404

    if user.suspended:
        return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401

    result, message, code = sign_in_with_mail(email, password)
    if result:
        session['email'] = email
        session['user_id']=user.id
        try:
            session.modified = True
            user_session = db.session.query(ExtendedSession).filter(
                ExtendedSession.session_id==session.sid
            ).first()
            if user_session:
                user_session.user_id= user.id
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print('Error: ',e)

    return jsonify(message), code
    

@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    username = data.get('name')
    mobile= data.get('mobile','')
    gender =data.get('gender','Others')
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
        if(res):
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
  delete_session()
  return redirect(url_for('index'))


@app.route('/profile', methods=['GET'])
def profile():
    if 'email' in session:
        user = fetch_user(session.get('email',''),session.get('user_id',None))
        wallet = user.wallet
        if not user or not wallet:
            delete_session()
            abort(404)
        if user.suspended:
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
    if 'email' not in session or not session.get('user_id',None):
        return jsonify({'message': "User Not Found!"}), 404
    else:
        user=fetch_user(email=session.get('email'),user_id=session.get('user_id',None))
        if(not user):
            abort(404)
        if user.suspended:
            delete_session()
            return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401
        else:
            return jsonify({'message': session.get('email')}), 200
   
@app.route('/get_toll_rate')
def get_rate():
    toll_rates=fetch_toll_rates()
    return jsonify(toll_rates)

@app.get('/verify_user')
def verify():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    return 'ok',200

@app.post('/Apply_coupon')
def apply_cupon():
    data=request.get_json()
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
    data=fetch_coupons()
    return jsonify({'success':True,'data':data})


@app.get('/load_recent_transactions')
def load_recent_transactions():
    # Check if the user is logged in and their email is stored in the session
    if session.get('user_id',None):
        user=fetch_user(session.get('email'),session.get('user_id'))
        transactions=fetch_recent_transactions(session.get('user_id'))
        return jsonify({'success': True, 'transactions': transactions})
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
    users ={} #TODO
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
    '''
    user1 = {
        "email": "pinakibanerjee2001@gmail.com",
        "name": "Pinaki Banerjee",
        "pic_url": "https://img.freepik.com/free-psd/3d-illustration-person-with-sunglasses_23-2149436188.jpg",
        "address": "Bahadurpur, Abhirampur, Purba Burdwan, West Bengal, India",
        "gender": "male",
        "mobile": "+91 8900539211",
        "suspended": False,
        "default_profile": False,
        "is_admin": False,
        "is_super_admin": True,
    }
    user2 = {
        "email": "dummy@gmail.com",
        "name": "Dummy User",
        "pic_url": "https://img.freepik.com/free-psd/3d-illustration-person-with-sunglasses_23-2149436188.jpg",
        "address": "Kolkata, 700098, West Bengal, India",
        "gender": "female",
    }
    store_new_user(user1)
    store_new_user(user2)
    '''
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
    app.run(port=8000)

