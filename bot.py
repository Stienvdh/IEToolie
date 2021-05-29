"""
Copyright (c) 2021 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from flask import Flask, request, jsonify
from webexteamssdk import WebexTeamsAPI
import os, re
import ie2k

# get environment variables
WT_BOT_TOKEN = os.environ['WT_BOT_TOKEN']

# uncomment next line if you are implementing a notifier bot
#WT_ROOM_ID = os.environ['WT_ROOM_ID']

# uncomment next line if you are implementing a controller bot
WT_BOT_EMAIL = os.environ['WT_BOT_EMAIL']

# start Flask and WT connection
app = Flask(__name__)
api = WebexTeamsAPI(access_token=WT_BOT_TOKEN)


# defining the decorater and route registration for incoming alerts
@app.route('/', methods=['POST'])
def alert_received():
    raw_json = request.get_json()
    print(raw_json)

    # customize the behaviour of the bot here
    welcome_message = """
        Hi, I am IE Toolie.

        I can do two things:
        - Run the Mac sticky script: type "Stick"
        - Find a device: type "Find *IP Address*"

        Have a great day ☀! 
    """

    message_id = raw_json['data']['id']
    message_object = api.messages.get(message_id)
    message_text = message_object.text.strip().lower()

    message = welcome_message

    if "stick" in message_text:
        message = "Running Sticky MAC"
    elif "find" in message_text:
        IP_REGEX = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ip_list = re.findall(IP_REGEX, message_text)
        ip_address = convert_list_to_string(ip_list[0],'')
        message = "Finding IP address: " + ip_address 

    # uncomment if you are implementing a controller bot
    WT_ROOM_ID = raw_json['data']['roomId']
    personEmail_json = raw_json['data']['personEmail']
    if personEmail_json != WT_BOT_EMAIL:
        api.messages.create(roomId=WT_ROOM_ID, markdown=message)

    return jsonify({'success': True})

def convert_list_to_string(list_object, seperator=''):
    return seperator.join(list_object)

if __name__=="__main__":
    app.run()