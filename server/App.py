from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import shutil
import json
import gzip
import nbt
import io
import base64

app = Flask(__name__)
CORS(app)  

url_mojang_uuid = "https://api.minecraftservices.com/minecraft/profile/lookup/name/"

url_bz = "https://api.hypixel.net/v2/skyblock/bazaar"
url_mayor = "http://api.hypixel.net/v2/resources/skyblock/election"

#https://api.hypixel.net/v2/skyblock/profiles?key=API_KEY&uuid=UUID
url_profile = "https://api.hypixel.net/v2/skyblock/profiles"

#https://api.hypixel.net/v2/skyblock/garden?profile=PROFILEID&key=KEY
url_garden = "https://api.hypixel.net/v2/skyblock/garden"

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

                    manualData = []

                    if os.path.isfile(file_path):
                        #os.remove(file_path)
                        with open(file_path, 'r') as file:
                            manualData = json.load(file).get('manuallyEnteredData', [])

            
                    shutil.copy(path_template, file_path)
                        
                    
                    currentUser = name
                    currentProfile = profile
                    guestMode = False

                    #shutil.copy(path_template, file_path)

                    message = "Success"



                    #adding data

                    with open(file_path, 'r') as file:
                        savedData = json.load(file)

                    with open(path_general_data, 'r') as file:
                        usefulData = json.load(file)

                    if manualData:
                        savedData['manuallyEnteredData'] = manualData

                    savedData['profileId'] = selected_profile['profile_id']

                    playerData = selected_profile['members'][user_id]


                    savedData['level'] = int(str(playerData['leveling']['experience']))//100


                    for col in savedData['collections']:
                        collectionData = next((c for c in usefulData['collectionsRequirements'] if (c['name'] == col )), None)

                        if collectionData:
                            playerHas = playerData.get('collection', {}).get( turn_name_into_id(collectionData['name']), 0)

                            colLevel = 0
                            
                            for milestone in collectionData['milestones']:
                                if playerHas >= milestone:
                                    colLevel += 1
                                else:
                                    break
                            
                            savedData['collections'][col] = colLevel



                    for slay in savedData['slayers']:
                        slayerData = next((s for s in usefulData['slayerRequirements'] if (s['name'] == slay )), None)

                        if slayerData:
                            playerHasExp = playerData.get('slayer', {}).get('slayer_bosses', {}).get(slay , {}).get('xp',0)

                            slayLevel = 0
                            
                            for milestone in slayerData['milestones']:
                                if playerHasExp >= milestone:
                                    slayLevel += 1
                                else:
                                    break
                            
                            savedData['slayers'][slay] = slayLevel




                    savedData['faction'] = playerData.get('nether_island_player_data', {}).get('selected_faction' , '-')
                    savedData['barbarianReputation'] = playerData.get('nether_island_player_data', {}).get('barbarians_reputation' , 0)
                    savedData['mageReputation'] = playerData.get('nether_island_player_data', {}).get('mages_reputation' , 0)


                    savedData['factoryPrestige'] = playerData.get('events', {}).get('easter', {}).get('chocolate_level' , 1)
                    savedData['hasZorro'] = playerData.get('events', {}).get('easter', {}).get('rabbits' , {}).get('zorro' , 0) > 0 


                    response = requests.get(url_garden + "?profile=" + selected_profile['profile_id'] + "&key=" + key)
                    dataGarden = response.json()
                    
                    if str(dataGarden.get('success')): 
                        for perk in savedData['composter']:
                            savedData['composter'][perk] = dataGarden.get('garden', {}).get('composter_data', {}).get('upgrades', {}).get(turn_name_into_id(perk), 0)
                    else:
                        message = "Error at fetching garden data - " + dataGarden.get('cause', '')
                        

                    talisCoded = playerData.get('inventory', {}).get('bag_contents', {}).get('talisman_bag', {}).get('data' , '')

                    if talisCoded:
                        talisSomewhatDecoded = gzip.decompress(base64.b64decode(talisCoded))


                        if b"CANDY_RELIC" in  talisSomewhatDecoded:
                            savedData['accessories']['candy accessory'] = 4
                        else:
                            if b"CANDY_ARTIFACT" in  talisSomewhatDecoded:
                                savedData['accessories']['candy accessory'] = 3
                            else:
                                if b"CANDY_RING" in  talisSomewhatDecoded:
                                    savedData['accessories']['candy accessory'] = 2
                                else:
                                    if b"CANDY_TALISMAN" in  talisSomewhatDecoded:
                                        savedData['accessories']['candy accessory'] = 1


                        if b"GOLD_GIFT_TALISMAN" in  talisSomewhatDecoded:
                            savedData['accessories']['gift accessory'] = 5
                        else:
                            if b"PURPLE_GIFT_TALISMAN" in  talisSomewhatDecoded:
                                savedData['accessories']['gift accessory'] = 4
                            else:
                                if b"BLUE_GIFT_TALISMAN" in  talisSomewhatDecoded:
                                    savedData['accessories']['gift accessory'] = 3
                                else:
                                    if b"GREEN_GIFT_TALISMAN" in  talisSomewhatDecoded:
                                        savedData['accessories']['gift accessory'] = 2
                                    else:    
                                        if b"WHITE_GIFT_TALISMAN" in  talisSomewhatDecoded:
                                            savedData['accessories']['gift accessory'] = 1    
                                            

                        if b"SEAL_OF_THE_FAMILY" in  talisSomewhatDecoded:
                            savedData['accessories']['seal accessory'] = 3
                        else:
                            if b"CROOKED_ARTIFACT" in  talisSomewhatDecoded:
                                savedData['accessories']['seal accessory'] = 2
                            else:    
                                if b"SHADY_RING" in  talisSomewhatDecoded:
                                    savedData['accessories']['seal accessory'] = 1    
                                    
                        
                        if b"BUCKET_OF_DYE" in  talisSomewhatDecoded:
                            savedData['accessories']['bucket of dye'] = 1   
                            
                    
                    
                    minSlots = 5
                    
                    playerHas = len(playerData.get('player_data', {}).get('crafted_generators', {}))
                    
                    
                    for milestone in usefulData['minionSlotsRequirements']:
                        if playerHas >= milestone:
                            minSlots += 1
                        else:
                            break
                    
                    for upg in selected_profile.get('community_upgrades', {}).get('upgrade_states', {}):
                        if upg.get('upgrade', '') == "minion_slots":
                            minSlots += 1
                    
                    savedData['minionSlots'] = minSlots
                    
                    
                    
                    
                    for perk in playerData.get('leveling', {}).get('completed_tasks', {}):
                        if "SPOOKY_FESTIVAL_CANDY_SCAVENGER" in perk:
                            savedData['perks']['extra candy'] += 1
                        if "WINTER_PROFESSIONAL_GIFTER" in perk:
                            savedData['perks']['better gifts'] += 1




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
