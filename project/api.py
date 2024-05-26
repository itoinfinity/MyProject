from datetime import datetime
from flask import Blueprint,current_app,request,jsonify
from numpy import double
from resources import models

Injections = {'SQL':r'C:\Final_Project\SQLInjectionNLP\sqli_new3.csv','XSS':r'C:\Final_Project\SQLInjectionNLP\xss_final.csv'}
type_list = list(Injections.keys())

trained_models = {}
trained_vectorizers = {}
for type in type_list:
    trained_models[type],trained_vectorizers[type]=models.train_model(Injections[type])

api_bp = Blueprint('login', __name__)

@api_bp.route('/check_injection', methods=['POST'])
def check_injection():
    try:
        db=current_app.config['db']
        ip=request.json.get('ip')
        value = request.json.get('value')
        longitude = double(request.json.get('lng'))
        latitude = double(request.json.get('lat'))
        user = db.Users.find_one({'UserIPAddress':ip})
        print(user)
        customer = user['CompanyName']
        city = request.json.get('city')
        country = request.json.get('country')
        type = isInjection(value)
        if(type):
            db.Injections.insert_one({'ip':ip,'city':city,'country':country,'longitude':longitude,'latitude':latitude,'customer':customer,'type':type,'string':value,'entry_time':datetime.now()})
            return jsonify(result=True)
        return jsonify(result=False)
    except Exception as e:
        print(f"Error processing JSON data: {e}")
        return jsonify(result=False), 400

@api_bp.route('/get_location/<city>',methods=['GET'])
def get_location(city):
    db=current_app.config['db']
    data=db.Cities.find({"city":city},{"_id":0})
    data_list = [document for document in data]
    return data_list

@api_bp.route('/get_cities/')
def get_cities():
    city = request.args.get('city')
    db=current_app.config['db']
    cities_cursor = db.Cities.find({ 'city': { '$regex': city ,'$options': 'i'} }, { "_id": 0, "city": 1, "country": 1 })
    cities = [city for city in cities_cursor]
    return jsonify(cities)

def isInjection(value):
    for type in type_list:
        if(models.check(value, trained_models[type], trained_vectorizers[type])[0]):
            return type
    return False