import pyrebase
from flask import json
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

def sign_in_with_mail(email:str,password:str) ->tuple:
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        # Get user info and check if email is verified
        user_info = auth.get_account_info(user['idToken'])
        email_verified = user_info["users"][0]["emailVerified"]
        if email_verified:
            return (True,{'code': 200, 'message': 'Login Success'}, 200)
        else:
            return (False,{'code': 405, 'message':'User Email not verified!'}, 405)

    except Exception as e:
        error_message = str(e)
        # Find the start and end positions of the 'error' object
        start_idx = error_message.find('{')
        error_object = error_message[start_idx:]
        error = json.loads(error_object)
        error=error['error']
        error_message = ' '.join(error.get('message', 'Undefined').split('_'))
        return (False,{'code': error.get('code', '400'), 'message':error_message},  error.get('code', 400))


    
