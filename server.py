#!/usr/bin/python
from flask import Flask, request, abort
from webexteamssdk import WebexTeamsAPI
import json
import os
import pymongo
import requests

app = Flask(__name__)
api_webexTeams = WebexTeamsAPI()
BOT_PERSON_EMAIL = os.environ['WEBEXTEAMS_BOT_PERSON_EMAIL']
MONGO_URL = os.environ['MONGODB_URI']

SEED_DATA = [
    {
        'decade': '1970s',
        'artist': 'Debby Boone',
        'song': 'You Light Up My Life',
        'weeksAtOne': 10
    },
    {
        'decade': '1980s',
        'artist': 'Olivia Newton-John',
        'song': 'Physical',
        'weeksAtOne': 10
    },
    {
        'decade': '1990s',
        'artist': 'Mariah Carey',
        'song': 'One Sweet Day',
        'weeksAtOne': 16
    }
]

client = pymongo.MongoClient(MONGO_URL)
db = client.get_default_database()
requests_log = db['requests_log']
messages_log = db['messages_log']

def convert_to_dict(obj):
  """
  A function takes in a custom object and returns a dictionary representation of the object.
  This dict representation includes meta data such as the object's module and class names.
  """
  
  #  Populate the dictionary with object meta data 
  obj_dict = {
    "__class__": obj.__class__.__name__,
    "__module__": obj.__module__
  }
  
  #  Populate the dictionary with object properties
  obj_dict.update(obj.__dict__)
  
  return obj_dict['_json_data']


@app.route('/webhook',methods=['POST'])
def webhook():
  if request.method == 'POST':
      incoming_message  = request.json
      #print(incoming_message)
      #requests_log.insert_one(incoming_message)
      #parse post reqest for message id and room id
      inc_msg_id  = incoming_message['data']['id']
      inc_room_id = incoming_message['data']['roomId']
      inc_person_email = incoming_message['data']['personEmail']

      incoming_message['_id']=incoming_message['data']['id']
      #requests_log.insert_one(incoming_message)
      #print(BOT_PERSON_EMAIL)
      #print(inc_person_email)

      #check if this is a message sent by the bot 
      if inc_person_email==BOT_PERSON_EMAIL:
        return '', 200
      else:
        

        #reqest the txt of the message id
        inc_msg = api_webexTeams.messages.get(inc_msg_id)

        #insert into Mogoddb
        message_json= json.loads(json.dumps(inc_msg,default=convert_to_dict))
        message_json['_id']=message_json['id']
        messages_log.insert_one(message_json)

        #check if message has file attched:
        if ('files' in message_json) and '/process' in inc_msg.text:
          #print(message_json)
          response = requests.get(message_json['files'][0],headers={"Authorization":"Bearer "+os.environ['WEBEX_TEAMS_ACCESS_TOKEN']})
          record_json={}
          print(response.text)
          for record in response.text.split('\n'):
              print(record)
              record_json={}
              line = record.split('|')
              print(line)
              record_json['field0']=line[0]
              record_json['field1']=line[1]
              record_json['field2']=line[2]
              record_json['field3']=line[3]
              record_json['field4']=line[4]
              record_json['field5']=line[5]
              record_json['field6']=line[6]
              record_json['field7']=line[7]
              record_json['field8']=line[8]
              record_json['field9']=line[9]
              record_json['field10']=line[10]
              record_json['field11']=line[11]
              record_json['field12']=line[12]
              record_json['field13']=line[13]
              record_json['field14']=line[14]
              record_json['field15']=line[15]
              record_json['field16']=line[16]
              record_json['field17']=line[17]
              record_json['field18']=line[18]
              record_json['field19']=line[19]
              record_json['field20']=line[20]
              record_json['field21']=line[21]
              record_json['field22']=line[22]
              record_json['field23']=line[23]
              record_json['field24']=line[24]
              record_json['field25']=line[25]
              record_json['field26']=line[26]
              record_json['field27']=line[27]
              record_json['field28']=line[28]
              record_json['field29']=line[29]  
              record_json['field30']=line[30]
              record_json['field31']=line[31]    

          print(record_json)



          api_webexTeams.messages.create(inc_room_id,text='respose'+json.dumps(record_json))

        #print(inc_msg_txt)

        return '', 200
  else:
      abort(400)

if __name__ == '__main__':
    try :
        app.run()
    except:
      #log the exceptionq
      print('exception')
    finally:
      print('closing DB')
      client.close()