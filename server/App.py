from flask import Flask, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

url_Mojang_uuid = "https://api.mojang.com/users/profiles/minecraft/"

url_Bz = "https://api.hypixel.net/v2/skyblock/bazaar"
url_Mayor = "http://api.hypixel.net/v2/resources/skyblock/election"

#https://api.hypixel.net/v2/skyblock/profiles?key=API_KEY&uuid=UUID
url_Profile = "https://api.hypixel.net/v2/skyblock/profiles?key="

#https://api.hypixel.net/v2/skyblock/auctions?key=API_KEY&page=PAGE
url_Ah = "https://api.hypixel.net/v2/skyblock/auctions?key="

key_API = ""
name = ""
uuid = ""

#16:55 ro time, 10 oct -> start year 378



def get_url_Profile(key, name):


    url_P = url_Profile + key + "&uuid=" + name
    return url_P



app = Flask(__name__)
CORS(app)  # This will allow cross-origin requests from your React frontend

@app.route('/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello from the backend!")


@app.route('/mayor', methods=['GET'])
def electionResults():

    response = requests.get(url_Mayor)

    if response.status_code == 200:
        data = response.json()
        mayor_name = data.get('mayor', {}).get('name', 'No mayor name found')

        return jsonify(message="OK", mayor = mayor_name)
    else:
        return jsonify(message="ERROR")



@app.route('/api/greet', methods=['GET'])
def greet():
    return jsonify({"message": "Hello from Python backend!"})

if __name__ == '__main__':
    app.run(port=5000)
