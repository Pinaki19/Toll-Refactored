import pyrebase

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
