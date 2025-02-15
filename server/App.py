from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import shutil
import json

app = Flask(__name__)
CORS(app)  

url_mojang_uuid = "https://api.minecraftservices.com/minecraft/profile/lookup/name/"

url_bz = "https://api.hypixel.net/v2/skyblock/bazaar"
url_mayor = "http://api.hypixel.net/v2/resources/skyblock/election"

#https://api.hypixel.net/v2/skyblock/profiles?key=API_KEY&uuid=UUID
url_profile = "https://api.hypixel.net/v2/skyblock/profiles"

#https://api.hypixel.net/v2/skyblock/auctions?key=API_KEY&page=PAGE
url_ah = "https://api.hypixel.net/v2/skyblock/auctions?key="

path_players = "server/resources/playerData"
path_template = "server/resources/generalData/template.json"
path_general_data = "server/resources/generalData/data.json"

path_conversion = "server/resources/generalData/conversion.json"

key_API = ""
name = ""
uuid = ""


currentUser = ""
currentProfile = ""
guestMode = True

#16:55 ro time, 10 oct -> start year 378


def turn_name_into_id(name):
    with open(path_conversion, 'r') as file:
        data = json.load(file)

    item_id = next((item['id'] for item in data if (item['name'] == name )), None)
    return item_id

def turn_id_into_name(item_id):
    with open(path_conversion, 'r') as file:
        data = json.load(file)

    name = next((item['name'] for item in data if (item['id'] == item_id )), None)
    return name


def get_player_path(folder, profile):
    return f"{path_players}/{folder}/{profile}.json" if profile else f"{path_players}/{folder}"





@app.route('/hello', methods=['GET'])
def hello():
    return jsonify(message="Hello from the backend!")


@app.route('/mayor', methods=['GET'])
def electionResults():

    response = requests.get(url_mayor)

    if response.status_code == 200:
        data = response.json()
        mayor_name = data.get('mayor', {}).get('name', 'No mayor name found')

        return jsonify(message="OK", mayor = mayor_name)
    else:
        return jsonify(message="ERROR")



@app.route('/api/greet', methods=['GET'])
def greet():
    return jsonify({"message": "Hello from Python backend!"})


@app.route('/player', methods=['GET'])
def getPlayerData():

    global currentUser
    global currentProfile
    global guestMode


    currentUser = ""
    currentProfile = ""
    guestMode = True

    name = request.args.get('name',"")
    profile = request.args.get('profile',"")
    key = request.args.get('key',"")

    message = ""


    if(name == ""):
        message = "No player specified; defaulting to guest"
        return jsonify({"message": message})

    
    if key != "":


        response = requests.get(url_mojang_uuid + name)

        

        if response.status_code == 200:
            data = response.json()
            user_id = data.get('id', '-')

            if user_id == "-":
                message += "Cannot locate Mojang uuid; "
            else:
                message += "Found uuid; "


            
            response = requests.get(url_profile + "?uuid=" + user_id + "&key=" + key)
            data = response.json()


            if str(data.get('success')):  
                profiles = data.get("profiles", []) 
                    
                selected_profile = next((p for p in profiles if ((profile != "" and p.get("cute_name") == profile) or (profile == "" and p.get("selected") is True))), None)

                if selected_profile:
                    print("Selected Profile:", str(selected_profile.get("cute_name", "???")))
                    message += "Profile = " + str(selected_profile.get("cute_name", "???")) + "; "

                    folder_path = get_player_path(name,"")

                    if os.path.isdir(folder_path):
                        message += "Player located; "
                    else:
                        message += "Player added; "
                        os.makedirs(folder_path)


                    file_path = get_player_path(name,selected_profile.get("cute_name"))

                    if os.path.isfile(file_path):
                        message += "Profile located; "
                    else:
                        currentUser = name
                        currentProfile = profile
                        guestMode = False

                        shutil.copy(path_template, file_path)

                        message += "Profile added; "



                    #adding data

                    with open(file_path, 'r') as file:
                        savedData = json.load(file)

                    with open(path_general_data, 'r') as file:
                        usefulData = json.load(file)

                    

                    playerData = selected_profile['members'][user_id]


                    savedData['level'] = int(str(playerData['leveling']['experience']))//100

                    #item_id = next((item["id"] for item in data if item["name"] == "abc"), None)


                    for col in savedData['collections']:
                        collectionData = next((c for c in usefulData['collectionsRequirements'] if (c['name'] == col )), None)

                        if collectionData:
                            playerHas = playerData.get('collection', {}).get( turn_name_into_id(collectionData['name']), 0)

                            colLevel = 0
                            
                            for milestone in collectionData['milestones']:
                                if playerHas >= milestone:
                                    colLevel = colLevel + 1
                                else:
                                    break
                            
                            savedData['collections'][col] = colLevel




                    with open(file_path, 'w') as file:
                        json.dump(savedData, file, indent=4)

                    #-


                    # Please get the data from selected_profile too pls pls pls

                    return jsonify({"message": message})
                else:
                    if(profile == ""):
                        message = "No skyblock profiles selected, somehow...; defaulting to guest"

                        return jsonify({"message": message})
                    else:
                         message += "Could not find the profile " + profile + "; "
            else:
                message += "Error at Hypixel API - " + str(data.get("cause")) + "; Looking into local profile; "
        else:
            message += "Error at Mojang API - " + str(data.get("cause")) + "; Looking into local profile; "


    
    if(profile == ""):
        message += "No profile specified; defaulting to guest"
        return jsonify({"message": message})

    folder_path = get_player_path(name,"")

    if os.path.isdir(folder_path):
        message += "Player located; "
    else:
        message += "Player added; "
        os.makedirs(folder_path)


    file_path = get_player_path(name, profile)

    if os.path.isfile(file_path):
        message += "Profile located; "
    else:
        currentUser = name
        currentProfile = profile
        guestMode = False

        shutil.copy(path_template, file_path)

        message += "Profile added; "
        


    return jsonify({"message": message})

if __name__ == '__main__':
    app.run(port=5000)
