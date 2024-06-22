from flask import Flask, jsonify, request, render_template,json, redirect, url_for, session, abort, send_file, send_from_directory
from pytz import timezone
from flask_cors import CORS
from datetime import datetime, timedelta
from flask_session import Session
import json
import io
import os
from PIL import Image
from utils.helper import *
from DB_utils.helper import *
from Auth.helper import *
from jinja2 import Environment
IST = timezone('Asia/Kolkata')
from __init__ import create_app,db
import psycopg2

app = create_app()

CORS(app)

# Define the custom filter function
def format_ist(datetime_str):
    # Parse the datetime string to a datetime object
    utc_time = datetime.fromisoformat(datetime_str)
    ist_timezone = IST
    # Convert the datetime to IST
    ist_time = utc_time.astimezone(ist_timezone)
    # Format the datetime as "DD-MM-YYYY HH:MM:SS"
    formatted_time = ist_time.strftime('%d-%m-%Y %H:%M:%S')
    return formatted_time

app.jinja_env.filters['format_ist'] = format_ist
#-------------------------------------------- User Account -------------------------------------------------------
@app.get('/get_recent_transactions')
def get_recent_transactions():
    email = session.get('email')
    wallet=fetch_wallet(email,session.get('user_id',None))
    recent_transactions=wallet.wallet_transactions if wallet else []
    recent_transactions=serialize(recent_transactions)
    result=[]
    for transaction in recent_transactions:
        transaction_amount = transaction.get('amount', 0)
        gst = transaction.get('gst_applied', 0)
        cupon = transaction.get('coupon_disc', 0)
        disc = transaction.get('global_disc', 0)
        transaction_amount=round(transaction_amount+gst-cupon-disc,2)
        transaction_color = 'green' if transaction['type'] == 'add money' else 'red'
        transaction_sign = '+' if transaction['type'] == 'add money' else '-'
        result.append({
            'amount':transaction_amount,
            'type':transaction['type'],
            'sign':transaction_sign,
            'color':transaction_color,
            'complete_time':str(transaction['expire_time'])
        })
            
    return render_template('recent_transactions.html', recent_transactions=result[::-1])

@app.route('/upload_image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['image']
    if file and allowed_file(file.filename):
        result=upload_to_bucket(file,app.supabase,session.get('user_id',None))
        if result:
            return jsonify({"success": True, "message": "File uploaded and compressed successfully."})
        else:
            return jsonify({"message": "Failed to upload file"}), 500
    else:
        return jsonify({"message": "Failed to upload file"}), 500


@app.get('/remove_profile_image')
def remove_profile_image():
    result=update_user_pic_url('',session.get('user_id',None),True,app.supabase)
    if result:
        return jsonify({"success": True, "message": "Profile picture removed successfully."})
    else:
        return jsonify({"success": False, "message": "No profile picture found for the user."})


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
    if not valid_user() or email!=session.get('email',''):
        abort(404)
    result=update_user(email,session.get('user_id',None),received)
    if result:
        return jsonify({'success':True}),200
    else:
        abort(404)

#-------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------


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
        set_user_id(user)
        return jsonify({'code': 200, 'message': 'Login Success'}), 200

    if not user:
        return jsonify({'code': 404, 'message': 'User not Found! Sign Up instead'}), 404

    if user.suspended:
        return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401

    result, message, code = sign_in_with_mail(email, password)
    if result:
        session['email'] = email
        session['user_id']=user.id
        set_user_id(user)

    return jsonify(message), code
    

@app.route('/sign_up', methods=['POST'])
def sign_up():
    data = request.get_json()
    email = data.get('email').lower()
    password = data.get('password')
    username = data.get('name')
    mobile= data.get('mobile','')
    gender =data.get('gender','others').lower()
    if not (email and password and username and gender):
        return jsonify({'message':'Provide all the Fields!'}), 404
    try:
        res=store_new_user({'name':username,'email':email,'gender':gender,'mobile':mobile})
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
        wallet = fetch_wallet(session.get('email',''),session.get('user_id',None),user)
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
    if not valid_user():
        return jsonify({'message': "User Not Found!"}), 404
    else:
        user=fetch_user(email=session.get('email'),user_id=session.get('user_id',None))
        if(not user):
            abort(404)
        if user.suspended:
            delete_session()
            return jsonify({'code': 401, 'message': 'User Account is Suspended. Contact Us for more Info.'}), 401
        else:
            data={'email': session.get('email'),'is_admin':user.is_admin,'is_super_admin':user.is_super_admin}
            return jsonify({'message':data}), 200
   
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
    coupon=data['cupon'].strip().lower()
    if(len(coupon)>=10 or coupon==''):
        abort(404)
    else:
        # Check if payment is requested
        payment_requested = session.get('PaymentRequested')
        if not payment_requested:
            # Handle the case where payment is not requested (e.g., redirect to a different page)
            session.pop('PaymentID', '')
            return abort(404)

        # Retrieve the payment ID from the session
        payment_id = session.get('PaymentID',None)
        if not payment_id:
            # Handle the case where payment ID is not found (e.g., redirect to a different page)
            return abort(404)

        payment_data=fetch_payment_data(payment_id)
        if(payment_data.type=='add money'):
            abort(404)
        gross_amount = payment_data.amount-payment_data.global_disc
        discount = round(calculate_cupon(gross_amount, coupon), 2)
        if(discount>0 and discount<=payment_data.amount):
            update_coupon_amount(payment_data,discount)
        return jsonify({'success': True, 'Data':serialize([payment_data],False)})

#----------------------------------------------------------------------------------------------------------------
#--------------------------------------------Payment Handler ----------------------------------------------------

@app.route('/pay', methods=['POST'])
def pay():
    PaymentInfo = request.get_json()
    print(PaymentInfo)
    Type = PaymentInfo['Type'].lower()
    Data={}
    if (Type == 'toll pay'):
        Vehicle = PaymentInfo['Vehicle_Type'].strip().lower()
        Journey = PaymentInfo['Journey'].strip().lower()
        Number = PaymentInfo['Vehicle_Number'].strip()
        Amount = get_toll_amount(Vehicle, Journey)
        print(Amount)
        if Amount <= 0:
            abort(404)
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
            'Number': Number,
        }
    elif (Type=='add money'):
        Amount=PaymentInfo['Amount']
        if(Amount<=0):
            abort(404)
        Data = {
            'Type': Type,
            'Amount': round(float(Amount), 2),
            "Gst": 0,
            "Cupon": 0,
            'GlobalDiscount': 0,
            'Number':None,
        }
    
    user_id=session.get('user_id',None)
    payment_ref=PaymentData(amount=Data['Amount'],coupon_disc=Data['Cupon'],\
        global_disc=Data['GlobalDiscount'], gst_applied=Data['Gst'],\
        vehicle_number=Data['Number'],user_id=user_id,\
            type=Data['Type'].lower()\
    )
    # Set session variables
    session['PaymentRequested'] = True
    # Convert ObjectId to str for storage
    if store_payment_data(payment_ref):
        session['PaymentID'] = payment_ref.id
        return redirect(url_for('complete_payment'))
    abort(404)

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
    payment_requested = session.get('PaymentRequested',False)
    if not payment_requested:
        # Handle the case where payment is not requested (e.g., redirect to a different page)
        session.pop('PaymentID', '')
        abort(404)

    # Retrieve the payment ID from the session
    payment_id = session.get('PaymentID',None)
    if not payment_id:
        session.pop('PaymentRequested', '')
        # Handle the case where payment ID is not found (e.g., redirect to a different page)
        abort(404)

    payment_doc = fetch_payment_data(payment_id)
    if not payment_doc:
        session.pop('PaymentRequested', '')
        session.pop('PaymentID', '')
        # Handle the case where payment data is not found (e.g., redirect to a different page)
        abort(404)

    # Check if the payment data has expired
    expiration_time = payment_doc.expire_time
    created_at = payment_doc.created_at
    if expiration_time-created_at>timedelta(minutes=5):
        session.pop('PaymentRequested', '')
        session.pop('PaymentID', '')
        # Payment data has expired, delete the document and abort 404
        delete_payment_data(payment_doc)
        abort(404)
    
    wallet = fetch_wallet(session.get('email',None),session.get('user_id',None))
    if not wallet:
        wallet={'Logged_in':False,'Balance':0}
    else:
        wallet=serialize([wallet],False)
        wallet.update({'Logged_in':True})
    return render_template('Payment.html', PaymentInfo=serialize([payment_doc],False),wallet=wallet)



@app.get('/get_payment_id')
def get_payment_id():
    if 'PaymentID' in session and 'PaymentRequested' in session:
        session.pop('PaymentRequested', '')
        payment_id = session.pop('PaymentID', '')
        payment_data=mark_payment_completed(payment_id)
        
        if payment_data.type=='add money':
            if payment_data.amount > 5000 or payment_data.amount<=0:
                return jsonify({'success': False}), 400
            result=update_wallet(payment_data.amount,payment_data)
            print("Res",result)
            if not result:
                return jsonify({'success':False,'message':'something went wrong!'}),500
        
        return jsonify({"success": True, "message": str(payment_id),"data":serialize([payment_data],False),"Login":'email' in session,'email':session.get('email')})
    else:
        return jsonify({"success": False, "message": "Payment data not found", "data": {}, "Login": 'email' in session,'email':session.get('email')})


@app.get('/update_user_wallet')
def update_user_wallet():
    if not valid_user():
        return jsonify({'success': False, 'message': "User not logged in"}),400
    payment_id = session.get('PaymentID')
    PIN=session.get('PIN',0)
    if not payment_id:
        return jsonify({'success': False, 'message': "Payment request not found!"}),400
    
    payment_data = fetch_payment_data(payment_id)
    email = session.get('email')
    user_id=session.get('user_id',None)
    user_wallet = fetch_wallet(email,user_id)
    if not user_wallet:
        return jsonify({'success': False, 'message': "User wallet not found!"}),400
    stored_PIN=user_wallet.pin
    if(stored_PIN^(turn_into_num(email))!=PIN):
        return jsonify({'failure': True,'message':"Wrong wallet PIN"}),400

    Amount = round(payment_data.amount+payment_data.gst_applied - \
        payment_data.coupon_disc-payment_data.global_disc,2)
    if (Amount > user_wallet.balance):
        return jsonify({'success': False, 'message': "Low wallet Balance"}),400
    add_wallet_id_to_transaction(payment_data,user_wallet)
    # Update the user's wallet balance by adding payment_data['Amount']
    update_wallet(Amount,payment_data,True)
    return jsonify({'success':True})
    

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
        transactions=fetch_recent_transactions(session.get('email'),session.get('user_id'))
        return jsonify({'success': True, 'transactions': transactions,'email':session.get('email')})
    else:
        return jsonify({'success': False, 'message': 'User not logged in'})
#----------------------------------------- super admin------------------------------------------------------------

@app.route('/users', methods=['GET'])
def get_users():
    if not check_user(True):
        return jsonify({'message':'Unauthorized Access!!'}),401
    users =fetch_all_users()
    return render_template('Create_Admin.html',users=users)


@app.route('/admins', methods=['GET'])
def get_admins():
    if not valid_user():
        abort(401)
    admins = fetch_admins()
    return render_template('Delete_Admin.html', users=admins)



# Define a route to make new admins
@app.route('/make_admin', methods=['POST'])
def make_admins():
    if not check_user():
        return jsonify({"message": "Unauthorized Access"}), 401
   
    data = request.get_json()
    if not data or 'data' not in data or 'Password' not in data:
        return jsonify({"error": "Invalid data"}), 400
    result,reason=update_users(data)
    if result:
        return jsonify({"message": reason}),200
    return jsonify({"message": reason}),500


# Define a route to delete admin privileges
@app.route('/delete_admin', methods=['POST'])
def delete_admin():
    if not check_user():
        return jsonify({"message": "Unauthorized Access"}), 401

    # Get the data from the POST request
    data = request.get_json()
    if not data or 'data' not in data:
        return jsonify({"error": "Invalid JSON data"}), 400
    
    result,reason=remove_admin_privilage(data)
    if result:
         return jsonify({"message": "Admin privileges removed successfully"})
    return jsonify({"message": reason}),400
   


#----------------------------------------------------Admin---------------------------------------------------

@app.route('/update_toll_rate', methods=['POST'])
def update_toll_rates():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    data=request.get_json()
    result,reason=update_toll_rate(data)
    if result:
        return jsonify({"message": reason}), 200
    return jsonify({"message": reason}), 400


@app.post("/modify_discounts")
def modify_discounts():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    data=request.get_json()
    result,reason=update_discount_coupons(data)
    if result:
        return jsonify({'message': reason}), 200
    return jsonify({'message':reason}),500



@app.route('/make_query', methods=['POST'])
def make_query():
    data = request.get_json()
    email = data.get('email', '').lower()
    if 'email' in session and email!=session.get('email'):
        return jsonify({'message': 'Email Ids do not match! '}),400
    id=store_query(email,data['message'],session.get('user_id',None))
    if not id:
        return jsonify({'message': f'Some error occured! Try again..'}),500
    return jsonify({'message': f'Query submitted successfully. Reference Id: {id}'}),200


@app.route('/get_queries', methods=['GET'])
def get_queries():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    queries=fetch_unresolved_queries()
    return jsonify({'queries':queries})





#TODO
@app.route('/resolve_queries', methods=['POST'])
def resolve_user_queries():
    if not check_user():
        return jsonify({"message": "Unauthorized Access!!"}), 401
    data=request.get_json()
    result=resolve_query(data,session.get('user_id'))
    if result:
        return jsonify({'message': 'Query resolved successfully!'})
    else:
        return jsonify({'error': 'Query not found'}, 404)




@app.route('/get_user_queries', methods=['GET'])
def get_user_queries():
    if not valid_user():
        return jsonify([]),500
    queries=fetch_user_queries(session.get('email',None),session.get('user_id',None))
    seen=True
    for query in queries:
        if query['solved'] and not query['seen']:
            seen=False
            break
    return jsonify({'queries':queries,'visited':seen}),200


@app.get('/mark_visited')
def mark_visited():
   mark_queries_seen(session.get('user_id'))
   return jsonify({"message": "success"}),200


@app.route('/', methods=['GET'])
def index():
    return render_template("Home.html")

@app.get('/favicon.ico')
def favicon():
    return send_from_directory('./static','favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.png')
def favicon_png():
    return send_from_directory('./static', 'favicon.png', mimetype='image/png')

# -------------------------------------------------------------------------------------------------------------------
# ---------------------------------admin only request--------------------------------------------------------------
@app.get('/get/<string:id>')
def get_user(id):
    if not check_user():
        return jsonify({"message":"Unauthorized access!!"}),401
    data=fetch_payment_data(id)
    if not data:
        return jsonify({"message":"No such Record Found!!"})
    return jsonify(serialize(data,False))

if __name__ == "__main__":
    app.run(port=8000)

