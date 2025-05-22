#my code
from flask import Flask, request
import threading 
import paho.mqtt.client as mqtt
import requests
import json
from mqtt import start_mqtt_subscriber

app = Flask(__name__)

import os

response = ""
unique = ['1','mars', 'elvis', 'Kori', 'brian','205', 'keith']
    
mqtt_data = {}

def search_id(identity, unique):
    return identity in unique
         
#///creating the methods of communictionb
@app.route('/post_data', methods=['POST', 'GET'])
def post_data():
    data = request.get_json()
    mqtt_data["gm"]=data.get("gm")
  
    print(mqtt_data)
    return "Data posted"
    
    
@app.route('/', methods=['POST', 'GET'])
def ussd_callback():
    print ("connected to mqtt server")
    global response
    global mqtt_data
    session_id = request.values.get("sessionId", None)#/////getting the session id
    service_code = request.values.get("serviceCode", None)#//////////getting the service code
    #phone_number = request.values.get("phoneNumber", None)#getting the phone number that requested
    text =request.values.get("text", "default")#getting the request
    session_state = text.split('*')  
    
    current_level = len(session_state)
    
    
    if current_level == 1:
        response  = "CON Hello and welcome to Agri-verify. \n"
        response += "1. Get general information about GMO.\n"
        response += "2. Use Chatbot.\n"
        response += "3. Verify a product.\n"
        response += "4. Give feedback.\n"
    
    if current_level == 2 and session_state[1] == '1':
        response  = "CON Hello and welcome to Agri-verify. Get general information about GMO.\n"
        response += "1. History of GMO.\n"
        response += "2. Myths and misconceptions of GMO.\n"
        response += "3. Benefits of GMO.\n"
        
    elif current_level == 3 and session_state[2] == '1':
        response = "END GMOs (Genetically Modified Organisms) are living organisms—like plants, animals, or microbes—whose genetic material has been artificially altered using genetic engineering techniques. This modification is done to introduce desirable traits such as resistance to pests, improved nutritional content, or faster growth.\n"
   
        
        
    elif current_level ==3 and session_state[2]== '2':
        response = "END Many believe GMOs are unsafe, but studies by health organizations show they are as safe as regular foods.\n"
        response += "Some think GMOs are made by injecting chemicals, but they’re actually created by precisely altering DNA to add useful traits. It's also a myth that only big companies benefit—GMO crops help small farmers grow more and use fewer pesticides."

    elif current_level ==3 and session_state[2]== '3':
        response = "END GMOs can help feed the world by increasing crop yields, reducing pesticide use, and improving nutritional content. They can also be engineered to withstand harsh conditions, making them valuable in regions affected by climate change.\n"
        response += "Additionally, GMOs can reduce food waste by extending shelf life and improving resistance to spoilage."        
   
    elif current_level == 2 and session_state[1] == '2':
        response = "CON Use Chatbot by typing your question.\n"

    elif current_level == 3:
        if "gm" in mqtt_data:
            temperature = mqtt_data["gm"]
            response = f"END Chatbot says {temperature}."
        else:
            response = "END chatbot not available."

    elif current_level == 2 and session_state[1] == '3':
        response = "CON Verify a product by entering the product ID.\n"
        
    elif current_level == 3:
        if "gm" in mqtt_data:
            temperature = mqtt_data["gm"]
            response = f"END The product is{temperature}."
        
    elif current_level == 2 and session_state[1] == '4':
        response = "CON Thank you for your feedback. We value your input and will use it to improve our services.\n"
        response += "1. Rate our service from 1 to 5.\n"
        response += "2. Report an issue.\n"
    elif current_level == 3  and( session_state[2] == '1' or session_state[2] == '2' or session_state[2] == '3' or session_state[2] == '4' or session_state[2] == '5') and session_state[1] == '4':
        response = "END Thank you for your feedback. We value your input and will use it to improve our services.\n"
      
    elif current_level == 3 and session_state[2] == '2' and session_state[1] == '4':
        response = "CON Please describe the issue you encountered. We appreciate your feedback and will work to resolve it.\n"

    elif current_level == 4:
        response = "END Thank you for your feedback. We value your input and will use it to improve our services.\n"
       
    

    return response
   
#Receive response from africas talking
@app.route('/call', methods=['POST'])
def call_back_client():
    return '<Response> <Dial phoneNumbers="" maxDuration="5"/></Response>'


if __name__ == '__main__':
    mqtt_thread = threading.Thread(target=start_mqtt_subscriber)
    mqtt_thread.daemon = True  # Daemonize the thread so it exits when the main thread exits
    mqtt_thread.start()
    app.run(host="0.0.0.0", port=os.environ.get('PORT'))
 




