from flask import Flask, request, jsonify
from twilio.rest import Client
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS  # For Cross platform APIs
from random import randint
from werkzeug.security import generate_password_hash


app = Flask(__name__)
app.secret_key = 'topsecret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///API.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)
auth = HTTPBasicAuth()
twilio_ssid = ""
twilio_auth = ""
client = Client(twilio_ssid, twilio_auth)
CORS(app)

class User_table(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String, nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String, nullable=False)
    Phone_No = db.Column(db.String, unique=True, nullable=False)
    Recent_otp = db.Column(db.Integer, nullable=True)

@auth.verify_password
def verify(number, password):
    user = User_table.query.filter_by(Phone_No=number).first()
    if user:
        if user.Password == password:
            return True
    return False

def gen_otp(phone_number):
    otp = randint(100000, 999999)
    user = User_table.query.filter_by(Phone_No=phone_number).first()
    notp = otp
    if len(str(notp)) < 6:
        noz = 6 - len(str(notp))
        notp = ("0" * noz) + str(notp)
    client.messages.create(to=[phone_number],
                          from_="+12183777167",
                          body="Your OTP is "+str(notp)
                          )
    user.Recent_otp = notp
    db.session.commit()

@app.route('/vNumber',methods=["POST"])
@auth.login_required
def vNumber():
    data = request.get_json()
    uotp = int(data['otp'])
    number = auth.current_user()
    user = User_table.query.filter_by(Phone_No=number).first()
    if uotp == int(user.Recent_otp):
        db.session.commit()
        return jsonify({'vNumber': 'Successful'})
    else:
        return jsonify({'vNumber': 'Failed'})


@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data['email']
    name = data['name']
    ph_number = data['ph_number']
    password1 = data['password1']
    password2 = data['password2']

    user = User_table.query.filter_by(Email=email).first()
    user_number = User_table.query.filter_by(Phone_No=ph_number).first()
    if user:
        return jsonify({'Signup': 'Email already exists, Try to Login.'})
    elif user_number:
        return jsonify({'Signup': 'Phone number is already registered with other user .'})
    elif len(name) < 2:
        return jsonify({'Signup': 'Name is too short.'})
    elif len(password1) < 7:
        return jsonify({'Signup': 'Password is too short.'})
    elif password1 != password2:
        return jsonify({'Signup': 'Password doesn\'t match.'})
    else:
        new_user = User_table(Email=email, Name=name, Password=generate_password_hash(password1, method='sha256'), Phone_No=ph_number , Recent_otp=0)
        db.session.add(new_user)
        db.session.commit()
        gen_otp(ph_number)
        return jsonify({'Signup': "Successful", "sha": str(new_user.Password)})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    ph_number = data['ph_number']

    user = User_table.query.filter_by(Phone_No=ph_number).first()
    if user:
            gen_otp(ph_number)
    else:
        return jsonify({'Login': 'User does not exist.'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
