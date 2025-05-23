from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os
import shutil
import json
import gzip
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
url_ah = "https://api.hypixel.net/v2/skyblock/auctions?page="

path_players = "server/resources/playerData"
path_template = "server/resources/generalData/template.json"
path_general_data = "server/resources/generalData/data.json"

path_prices = "server/resources/generalData/prices.json"
path_prices_clean = "server/resources/generalData/pricesClean.json"
path_recipes_clean = "server/resources/generalData/recipesClean.json"

guest_path = "server/resources/generalData/guest.json"
guest_recipes_path = "server/resources/generalData/recipes.json"

key_API = ""
name = ""
uuid = ""


currentUser = ""
currentProfile = ""
guestMode = True

#16:55 ro time, 10 oct -> start year 378



def get_player_path(userName, profile):
    return f"{path_players}/{userName}/{profile}.json" if profile else f"{path_players}/{userName}"

def get_current_player_path():
    if guestMode:
        return guest_path
    else:
        return get_player_path(currentUser,currentProfile)

def get_player_recipes_path(userName, profile):
    return f"{path_players}/{userName}/{profile}_recipes.json"

def get_current_player_recipes_path():
    if guestMode:
        return guest_recipes_path
    else:
        return get_player_recipes_path(currentUser,currentProfile)


def get_ah_page(page):
    return url_ah + str(page)

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
                        with open(file_path, 'r') as file:
                            manualData = json.load(file).get('manuallyEnteredData', [])

            
                    shutil.copy(path_template, file_path)
                        
                    currentUser = name
                    currentProfile = profile
                    guestMode = False
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


                    for colId, playerHas in playerData.get('collection', {}).items():

                        collectionName = usefulData['conversion'].get(colId, "")

                        if collectionName != "" and usefulData['collectionsRequirements'].get(collectionName,{}):
                            collectionData = usefulData['collectionsRequirements'][ collectionName ]
                            

                            colLevel = 0
                                
                            for milestone in collectionData:
                                if playerHas >= milestone:
                                    colLevel += 1
                                else:
                                    break
                                
                            savedData['collections'][collectionName] = colLevel


                    for slayName, slayData in playerData.get('slayer', {}).get('slayer_bosses', {}).items():

                        slayerMilestones =  usefulData['slayerRequirements'][slayName]
                        playerHasExp = slayData.get('xp',0)
                        slayLevel = 0
                            
                        for milestone in slayerMilestones:
                            if playerHasExp >= milestone:
                                slayLevel += 1
                            else:
                                break
                            
                        savedData['slayers'][slayName] = slayLevel




                    savedData['faction'] = playerData.get('nether_island_player_data', {}).get('selected_faction' , '-')
                    savedData['barbarianReputation'] = playerData.get('nether_island_player_data', {}).get('barbarians_reputation' , 0)
                    savedData['mageReputation'] = playerData.get('nether_island_player_data', {}).get('mages_reputation' , 0)


                    savedData['factoryPrestige'] = playerData.get('events', {}).get('easter', {}).get('chocolate_level' , 1)
                    savedData['hasZorro'] = playerData.get('events', {}).get('easter', {}).get('rabbits' , {}).get('zorro' , 0) > 0 



                    playerHasExp = playerData.get('mining_core', {}).get('experience', -1)

                    hotmLevel = 0
                            
                    for milestone in usefulData['hotmRequirements']:
                        if playerHasExp >= milestone:
                            hotmLevel += 1
                        else:
                            break
                            
                    savedData['hotmLevel'] = hotmLevel

                    hotmPerks = playerData.get('mining_core', {}).get('nodes', {})

                    for perk, perkLevel in hotmPerks.items():
                        if usefulData['conversion'].get(perk,"") != "":
                            savedData['hotmPerks'][usefulData['conversion'][perk]] = perkLevel
              
                    response = requests.get(url_garden + "?profile=" + selected_profile['profile_id'] + "&key=" + key)
                    dataGarden = response.json()
                    
                    if str(dataGarden.get('success')): 
                        composterUpgrades = dataGarden.get('garden', {}).get('composter_data', {}).get('upgrades', {})
                        for perk in composterUpgrades:
                            if usefulData['conversion'][perk]:
                                savedData['composter'][usefulData['conversion'][perk]] = composterUpgrades.get(perk, 0)

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
        shutil.copy(path_template, file_path)
        message += "Profile added; "

    currentUser = name
    currentProfile = profile
    guestMode = False
    
    return jsonify({"message": message})


@app.route('/craft', methods=['GET'])
def getCraftPrices():
    global currentUser
    global currentProfile
    global guestMode


    message = ""

    with open(get_current_player_path(), 'r') as file:
        playerData = json.load(file)


    shutil.copy(path_recipes_clean, get_current_player_recipes_path())


    with open(get_current_player_recipes_path(), 'r') as file:
        recipesData = json.load(file)

    with open(path_prices, 'r') as file:
        pricesData = json.load(file)



    for itemName, itemData in recipesData.items():
        for recipe in itemData.get('recipes',{}):
            if ((playerData.get('collections',{}).get( recipe.get('requirements',{}).get('collection','-') ,0) < recipe.get('requirements',{}).get('collectionLevel',0))
            or (playerData.get('slayers',{}).get( recipe.get('requirements',{}).get('slayer','-') ,0) < recipe.get('requirements',{}).get('slayerLevel',0))
            or (playerData.get('barbarianReputation',0) < recipe.get('requirements',{}).get('barbarianReputation',-9999))
            or (playerData.get('mageReputation',0) < recipe.get('requirements',{}).get('mageReputation',-9999))
            or (playerData.get('manuallyEnteredData',{}).get('museum milestone',0) < recipe.get('requirements',{}).get('museumMilestone',0))):
                recipe['canCraft'] = False
            


            for material, quantity in recipe['recipeMaterials'].items():

                materialPriceData = pricesData.get(material,{})

                if 'buy' in materialPriceData:

                    if(materialPriceData['buy'] != 0):
                        materialsList = dict(recipe['materialsNeededInstant'])
                        materialsList[material] = materialsList.get(material, 0.0) + quantity
                        recipe['materialsNeededInstant'] = materialsList
                        recipe['craftPriceInstant'] += materialPriceData['buy'] * quantity
                    else:
                        materialsList = dict(recipe['materialsNeededFarmInstant'])
                        materialsList[material] = materialsList.get(material, 0.0) + quantity
                        recipe['materialsNeededFarmInstant'] = materialsList


                    
                    materialsList = dict(recipe['materialsNeededOrders'])
                    materialsList[material] = materialsList.get(material, 0.0) + quantity
                    recipe['materialsNeededOrders'] = materialsList
                    recipe['craftPriceOrders'] += (materialPriceData['sell']+0.1) * quantity
                    
                        
                    continue



                materialCraftData = recipesData.get(material,{}).get("recipes", [])
                if materialCraftData:

                    # directPrice = 0
                    # if materialPriceData.get('NPCbuy',0) < directPrice or directPrice == 0:
                    #     directPrice = materialPriceData.get('NPCbuy',0)
                    directPrice = materialPriceData.get('NPCbuy',0)

                    if 'priceBIN' in materialPriceData:
                        if materialPriceData["NPCsell"] > 0 and materialPriceData["rarity"] == "COMMON":
                            if (materialPriceData['priceAUC'] < directPrice and materialPriceData['priceAUC'] >0 ) or directPrice == 0:
                                directPrice = materialPriceData['priceAUC']
                        else:
                            if (materialPriceData['priceBIN'] < directPrice and materialPriceData['priceBIN'] >0 )  or directPrice == 0:
                                directPrice = materialPriceData['priceBIN']

                    #materialCraftData = materialCraftData[0]

                    craftable_items = [item for item in materialCraftData if item.get('canCraft')]

                    if craftable_items:
                        materialCraftData = min(craftable_items, key=lambda item: item['craftPriceInstant'] / item['quantity'])
                    else:
                        materialCraftData = {}

                    if materialCraftData:


                        if directPrice < materialCraftData['craftPriceInstant']/materialCraftData['quantity']:
                            materialsList = dict(recipe['materialsNeededInstant'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededInstant'] = materialsList
                            recipe['craftPriceInstant'] += directPrice * quantity
                        else:
                            materialsList = dict(recipe['materialsNeededInstant'])
                            materialsListComponent = dict(materialCraftData['materialsNeededInstant'])

                            addedList = {key: value * (quantity / materialCraftData['quantity']) for key, value in materialsListComponent.items()}
                            for materialAdd, amount in addedList.items():
                                materialsList[materialAdd] = materialsList.get(materialAdd, 0.0) + amount 

                            recipe['materialsNeededInstant'] = materialsList
                            recipe['craftPriceInstant'] += materialCraftData['craftPriceInstant']/materialCraftData['quantity'] * quantity



                            materialsList = dict(recipe['materialsNeededFarmInstant'])
                            materialsListComponent = dict(materialCraftData['materialsNeededFarmInstant'])

                            addedList = {key: value * (quantity / materialCraftData['quantity']) for key, value in materialsListComponent.items()}
                            for materialAdd, amount in addedList.items():
                                materialsList[materialAdd] = materialsList.get(materialAdd, 0.0) + amount 

                            recipe['materialsNeededFarmInstant'] = materialsList

                        

                    if craftable_items:
                        materialCraftData = min(craftable_items, key=lambda item: item['craftPriceOrders'] / item['quantity'])
                    else:
                        materialCraftData = {}

                    if materialCraftData:


        
                        
                        if directPrice < materialCraftData['craftPriceOrders']/materialCraftData['quantity']:
                            materialsList = dict(recipe['materialsNeededOrders'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededOrders'] = materialsList
                            recipe['craftPriceOrders'] += directPrice * quantity
                        else:
                            materialsList = dict(recipe['materialsNeededOrders'])
                            materialsListComponent = dict(materialCraftData['materialsNeededOrders'])

                            addedList = {key: value * (quantity / materialCraftData['quantity']) for key, value in materialsListComponent.items()}
                            for materialAdd, amount in addedList.items():
                                materialsList[materialAdd] = materialsList.get(materialAdd, 0.0) + amount 

                            recipe['materialsNeededOrders'] = materialsList
                            recipe['craftPriceOrders'] += materialCraftData['craftPriceOrders']/materialCraftData['quantity'] * quantity



                            materialsList = dict(recipe['materialsNeededFarmOrders'])
                            materialsListComponent = dict(materialCraftData['materialsNeededFarmOrders'])

                            addedList = {key: value * (quantity / materialCraftData['quantity']) for key, value in materialsListComponent.items()}
                            for materialAdd, amount in addedList.items():
                                materialsList[materialAdd] = materialsList.get(materialAdd, 0.0) + amount 

                            recipe['materialsNeededFarmOrders'] = materialsList   

                        continue

                    continue


                if 'priceBIN' in materialPriceData:

                    if materialPriceData["NPCsell"] > 0 and materialPriceData["rarity"] == "COMMON":
        
                        if(materialPriceData['priceAUC'] > 0):
                            materialsList = dict(recipe['materialsNeededInstant'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededInstant'] = materialsList
                            recipe['craftPriceInstant'] += materialPriceData['priceAUC'] * quantity

                            materialsList = dict(recipe['materialsNeededOrders'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity 
                            recipe['materialsNeededOrders'] = materialsList
                            recipe['craftPriceOrders'] += materialPriceData['priceAUC'] * quantity
                        else:
                            materialsList = dict(recipe['materialsNeededFarmInstant'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededFarmInstant'] = materialsList

                            materialsList = dict(recipe['materialsNeededFarmOrders'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededFarmOrders'] = materialsList

                    else:

                        if(materialPriceData['priceBIN'] > 0):
                            materialsList = dict(recipe['materialsNeededInstant'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededInstant'] = materialsList
                            recipe['craftPriceInstant'] += materialPriceData['priceBIN'] * quantity

                            materialsList = dict(recipe['materialsNeededOrders'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity 
                            recipe['materialsNeededOrders'] = materialsList
                            recipe['craftPriceOrders'] += materialPriceData['priceBIN'] * quantity
                        else:
                            materialsList = dict(recipe['materialsNeededFarmInstant'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededFarmInstant'] = materialsList

                            materialsList = dict(recipe['materialsNeededFarmOrders'])
                            materialsList[material] = materialsList.get(material, 0.0) + quantity
                            recipe['materialsNeededFarmOrders'] = materialsList
                    
                    continue

                
                if 'NPCbuy' in materialPriceData:

                    materialsList = dict(recipe['materialsNeededInstant'])
                    materialsList[material] = materialsList.get(material, 0) + quantity
                    recipe['materialsNeededInstant'] = materialsList
                    recipe['craftPriceInstant'] += materialPriceData['NPCbuy'] * quantity

                    materialsList = dict(recipe['materialsNeededOrders'])
                    materialsList[material] = materialsList.get(material, 0.0) + quantity 
                    recipe['materialsNeededOrders'] = materialsList
                    recipe['craftPriceOrders'] += materialPriceData['NPCbuy'] * quantity
                        
                    continue


                materialsList = dict(recipe['materialsNeededFarmInstant'])
                materialsList[material] = materialsList.get(material, 0) + quantity
                recipe['materialsNeededFarmInstant'] = materialsList

                materialsList = dict(recipe['materialsNeededFarmOrders'])
                materialsList[material] = materialsList.get(material, 0) + quantity
                recipe['materialsNeededFarmOrders'] = materialsList

    
            itemPriceData = pricesData.get(itemName,{})
            recipe['sellForInstant'] = itemPriceData['NPCsell'] * recipe['quantity']
            recipe['sellForOrders'] = itemPriceData['NPCsell'] * recipe['quantity']
            recipe['sellOnInstant'] = 'NPC'
            recipe['sellOnOrders'] = 'NPC'
            # recipe['sellForInstant'] *(100-tax)/100 - for when npc tax is greater than 0
            recipe['profitInstantInstant'] = recipe['sellForInstant']  - recipe['craftPriceInstant']
            recipe['profitInstantOrders'] = recipe['sellForOrders']  - recipe['craftPriceInstant']
            recipe['profitOrdersInstant'] = recipe['sellForInstant']  - recipe['craftPriceOrders']
            recipe['profitOrdersOrders'] = recipe['sellForOrders']  - recipe['craftPriceOrders']



            if 'priceAUC' in itemPriceData:


                if itemPriceData["NPCsell"] > 0 and itemPriceData["rarity"]  == "COMMON":
                    price = itemPriceData['priceAUC']
                    sellType = 'AH - AUC'
                    tax = 1
                else:
                    price = itemPriceData['priceBIN']
                    sellType = 'AH - BIN'

                    if price < 10_000_000:
                        tax = 1
                    elif price < 100_000_000:
                        tax = 2
                    else:
                        tax = 2.5

                    tax += 1
                
                if recipe['quantity'] * price *(100-tax)/100 > recipe['sellForInstant'] :
                    recipe['sellForInstant'] = price * recipe['quantity']
                    recipe['sellOnInstant'] = sellType
                    recipe['profitInstantInstant'] = recipe['quantity'] * price *(100-tax)/100 - recipe['craftPriceInstant']
                    recipe['profitOrdersInstant'] = recipe['quantity'] * price *(100-tax)/100 - recipe['craftPriceOrders']
     

                if recipe['quantity'] * price *(100-tax)/100 > recipe['sellForOrders'] :
                    recipe['sellForOrders'] = price * recipe['quantity']
                    recipe['sellOnOrders'] = sellType
                    recipe['profitInstantOrders'] = recipe['quantity'] * price *(100-tax)/100 - recipe['craftPriceInstant']
                    recipe['profitOrdersOrders'] = recipe['quantity'] * price *(100-tax)/100 - recipe['craftPriceOrders']


            if 'buy' in itemPriceData:
                tax = 1.25 - 0.125 * playerData['manuallyEnteredData']['bazaar flipper perk']

               
                
                if recipe['quantity'] * itemPriceData['sell'] *(100-tax)/100 > recipe['sellForInstant'] :
                    recipe['sellForInstant'] = itemPriceData['sell'] * recipe['quantity']
                    recipe['sellOnInstant'] = 'BZ'
                    recipe['profitInstantInstant'] = recipe['quantity'] * itemPriceData['sell'] *(100-tax)/100 - recipe['craftPriceInstant']
                    recipe['profitOrdersInstant'] = recipe['quantity'] * itemPriceData['sell'] *(100-tax)/100 - recipe['craftPriceOrders']
     

                if recipe['quantity'] * (itemPriceData['buy']-0.1) *(100-tax)/100 > recipe['sellForOrders'] :
                    recipe['sellForOrders'] = (itemPriceData['buy']-0.1) * recipe['quantity']
                    recipe['sellOnOrders'] = 'BZ'
                    recipe['profitInstantOrders'] = recipe['quantity'] * (itemPriceData['buy']-0.1) *(100-tax)/100 - recipe['craftPriceInstant']
                    recipe['profitOrdersOrders'] = recipe['quantity'] * (itemPriceData['buy']-0.1) *(100-tax)/100 - recipe['craftPriceOrders']
            




                


    with open(get_current_player_recipes_path(), 'w') as file:
        json.dump(recipesData, file, indent=4)



    message = "ok"
    return jsonify({"message": message})


@app.route('/prices', methods=['GET'])
def getPrices():

    #decoded = gzip.decompress(base64.b64decode("A"))


    shutil.copy(path_prices_clean, path_prices)
    message = ""
   
    response = requests.get(url_bz)

    if response.status_code == 200:
        data = response.json()
        
        with open(path_prices, 'r') as file:
            pricesData = json.load(file)

        with open(path_general_data, 'r') as file:
            usefulData = json.load(file)

        for item, itemData in data.get('products', {}).items():
            itemName = usefulData['conversion'].get(itemData.get('product_id', {}),'')

            if pricesData.get(itemName):
                pricesData[itemName]['buy'] = round(itemData.get('quick_status', {}).get('buyPrice', 0), 1)
                pricesData[itemName]['sell'] = round(itemData.get('quick_status', {}).get('sellPrice', 0), 1)

        with open(path_prices, 'w') as file:
            json.dump(pricesData, file, indent=4)

    else:
        message = "Error at Hypixel api - " + response.json().get('cause', {})



    response = requests.get(get_ah_page(0))
    pages = response.json().get('totalPages',-1)

    for page in range(0, pages):

        response = requests.get(get_ah_page(page))

        if response.status_code == 200:
            data = response.json()
            
            with open(path_prices, 'r') as file:
                pricesData = json.load(file)


            for item in data.get('auctions', {}):

                #add 5 math hoes to list, beast crest, 5 kuudra armors
                # keywords = ['RARE', 'EPIC', 'LEGENDARY']
                # if any(keyword in item_name for keyword in keywords):
                    
                name_of_item = "-"
                if item.get('item_name', '') not in ['Griffin Upgrade Stone', 'Wisp Upgrade Stone', 'Inferno Minion Fuel',"Euclid's Wheat Hoe", "Gauss Carrot Hoe",
                    "Pythagorean Potato Hoe", "Turing Sugar Cane Hoe", "Newton Nether Warts Hoe", "Beastmaster Crest"] and not (any(checkName in 
                    item.get('item_name', '') for checkName in ['Aurora','Fervor','Terror','Crimson','Hollow']) and 
                    any(checkPiece in item.get('item_name', '') for checkPiece in ['Helmet','Chestplate','Leggings','Boots'])):

                    name_of_item = item.get('item_name', '-')
                    
                else:
                    name_of_item = item.get('item_name', '-') #just in case

                    if item.get('item_name', {}) == 'Griffin Upgrade Stone':
                        if 'UNCOMMON' in item.get('item_lore', ''):
                            name_of_item = "Griffin Upgrade Stone - Uncommon"
                        elif 'RARE' in item.get('item_lore', ''):
                            name_of_item = "Griffin Upgrade Stone - Rare"
                        elif 'EPIC' in item.get('item_lore', ''):
                            name_of_item = "Griffin Upgrade Stone - Epic"
                        elif 'LEGENDARY' in item.get('item_lore', ''):
                            name_of_item = "Griffin Upgrade Stone - Legendary"

                    
                    if item.get('item_name', {}) == 'Wisp Upgrade Stone':
                        if 'Droplet Wisp' in item.get('item_lore', ''):
                            name_of_item = "Wisp Upgrade Stone - Rare"
                        elif 'Frost Wisp' in item.get('item_lore', ''):
                            name_of_item = "Wisp Upgrade Stone - Epic"
                        elif 'Glacial Wisp' in item.get('item_lore', ''):
                            name_of_item = "Wisp Upgrade Stone - Legendary"
                        
                        
                    if item.get('item_name', {}) == 'Inferno Minion Fuel':
                        name_of_item = 'Inferno Minion Fuel - '

                        if 'RARE' in item.get('item_lore', ''):
                            name_of_item += "Rare - "
                        elif 'EPIC' in item.get('item_lore', ''):
                            name_of_item += "Epic - "
                        elif 'LEGENDARY' in item.get('item_lore', ''):
                            name_of_item += "Legendary - "

                    
                        if 'Magma Cream' in item.get('item_lore', ''):
                            name_of_item += "Magma Cream"
                        elif 'Glowstone Dust' in item.get('item_lore', ''):
                            name_of_item += "Glowstone Dust"
                        elif 'Nether Wart' in item.get('item_lore', ''):
                            name_of_item += "Nether Wart"
                        elif 'Blaze Rod' in item.get('item_lore', ''):
                            name_of_item += "Blaze Rod"
                        elif 'Crude Gabagool' in item.get('item_lore', ''):
                            name_of_item += "Crude Gabagool"
                        
                    
                    if item.get('item_name', {}) in ["Euclid's Wheat Hoe", "Gauss Carrot Hoe","Pythagorean Potato Hoe","Turing Sugar Cane Hoe","Newton Nether Warts Hoe"]:
                        name_of_item =  item.get('item_name', '')   + ' - '

                        if "Stone Hoe" in item.get('extra', {}):
                            name_of_item += "Common"
                        elif "Iron Hoe" in item.get('extra', {}):
                            name_of_item += "Uncommon"
                        elif "Diamond Hoe" in item.get('extra', {}):
                            name_of_item += "Rare"
                    
                    
                    if item.get('item_name', {}) == 'Beastmaster Crest':
                        coded = item.get('item_bytes', '')
                        decoded = gzip.decompress(base64.b64decode(coded))


                        if (b"BEASTMASTER_CREST_COMMON" in decoded):
                            name_of_item = "Beastmaster Crest - Common"
                        elif (b"BEASTMASTER_CREST_UNCOMMON" in decoded):
                            name_of_item = "Beastmaster Crest - Uncommon"
                        elif (b"BEASTMASTER_CREST_RARE" in decoded):
                            name_of_item = "Beastmaster Crest - Rare"
                        elif (b"BEASTMASTER_CREST_EPIC" in decoded):
                            name_of_item = "Beastmaster Crest - Epic"
                        elif (b"BEASTMASTER_CREST_LEGENDARY" in decoded):
                            name_of_item = "Beastmaster Crest - Legendary"
     

                    if (any(checkName in item.get('item_name', '') for checkName in ['Aurora','Fervor','Terror','Crimson','Hollow']) and 
                        any(checkPiece in item.get('item_name', '') for checkPiece in ['Helmet','Chestplate','Leggings','Boots'])):
                       
                       
                        prefixes = ["Hot", "Burning", "Fiery", "Infernal"]
                        name_of_item = next((prefix + " " for prefix in prefixes if prefix in item.get('item_name', '')), "")
                        

                        prefixes = ['Aurora','Fervor','Terror','Crimson','Hollow']
                        name_of_item +=  next((prefix + " " for prefix in prefixes if prefix in item.get('item_name', '')), "")

                        prefixes = ['Helmet','Chestplate','Leggings','Boots']
                        name_of_item +=  next((prefix for prefix in prefixes if prefix in item.get('item_name', '')), "")

                   

                    #yea
                    

                
                    

    
                if name_of_item in pricesData and "priceBIN" in pricesData[name_of_item]:
                    if item.get('bin', {}):
                        if ((item.get('starting_bid',0) > 0 and item.get('starting_bid',0) < pricesData[name_of_item]['priceBIN'])
                             or pricesData[name_of_item]['priceBIN']==0):
                            pricesData[name_of_item]['priceBIN'] = item.get('starting_bid',0)
                    else:
                        if ((item.get('end',0) > 0 and item.get('end',0) < pricesData[name_of_item]['timeEndAuc'])
                             or pricesData[name_of_item]['timeEndAuc']==0):
                                pricesData[name_of_item]['timeEndAuc'] = item.get('end',0)
                                pricesData[name_of_item]['priceAUC'] = max(item.get('highest_bid_amount',0), item.get('starting_bid',0))

            with open(path_prices, 'w') as file:
                json.dump(pricesData, file, indent=4)

        else:
            message += "   Error at Hypixel api - " + response.json().get('cause', {})



    message += " FINISHED"
    return jsonify({"message": message})

if __name__ == '__main__':
    app.run(port=5000)
