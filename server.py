#!/usr/bin/python
from flask import Flask, request, abort
from webexteamssdk import WebexTeamsAPI
import json
import os
import pymongo
import requests
from datetime import datetime
import re
import time


app = Flask(__name__)
api_webexTeams = WebexTeamsAPI()
BOT_PERSON_EMAIL = os.environ['WEBEXTEAMS_BOT_PERSON_EMAIL']
MONGO_URL = os.environ['MONGODB_URI']

client = pymongo.MongoClient(MONGO_URL)
db = client.get_default_database()
requests_log = db['requests_log']
messages_log = db['messages_log']
apointnements_coll = db['apointnements_coll']
doctors_coll = db['doctors_coll']

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

def date_to_json(obj):
    if isinstance(obj, datetime):
        return obj.__str__()

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

          #TODO Controle file name for duplicates 
          response = requests.get(message_json['files'][0],headers={"Authorization":"Bearer "+os.environ['WEBEX_TEAMS_ACCESS_TOKEN']})
          record_json={}
          #print(response.text)
          for record in response.text.split('\n'):
              record_json={}
              line = record.split('|')
              if len(line)==32:
                  #record_json['name']=line[0]
                  record_json['Treating Hospital']=line[1]
                  #record_json['field2']=line[2]
                  record_json['Treating Specialty']=line[3]
                  record_json['Treating Service occasion']=line[4]
                  record_json['date_start']=datetime.strptime(line[5].replace('.',''), '%d/%m/%Y %I:%M:%S %p')#TODO add timezone everywhere
                  record_json['date_end']=datetime.strptime(line[6].replace('.',''), '%d/%m/%Y %I:%M:%S %p')#TODO add timezone everywhere
                  #record_json['field7']=line[7]
                  record_json['Referral Hospital']=line[8]
                  #record_json['field9']=line[9]
                  record_json['Referral Specialty']=line[10]
                  record_json['Referral Service occasion']=line[11]
                  record_json['Referral Beginning']=line[12]
                  record_json['Referral Ending']=line[13]
                  #record_json['field14']=line[14]
                  record_json['Treating Physician Name']=line[15]
                  record_json['Treating Physician Last name']=line[16]
                  #record_json['field17']=line[17]
                  #record_json['field18']=line[18]
                  record_json['Referral Physician Name']=line[19]
                  record_json['Referral Physician Last name']=line[20]
                  #record_json['field21']=line[21]
                  record_json['Patient Social Security Number']=line[22]
                  record_json['Patient Additional Social Security Number']=line[23]
                  record_json['Patient Name']=line[24]
                  record_json['Patient Last name']=line[25]
                  record_json['Patient Surname']=line[26]
                  record_json['Patient Birthdate']=line[27]
                  #record_json['field28']=line[28]
                  record_json['Patient Gender']=line[29]  
                  record_json['Consultation Reason']=line[30]
                  record_json['Diagnostic']=line[31]
                  apointnements_coll.insert_one(record_json)
              else:
                #file io error at line N
                print('file io error') 
              #print(record_json)
              print(json.dumps(record_json,default=date_to_json, ensure_ascii=False))
              #api_webexTeams.messages.create(inc_room_id,text='respose'+json.dumps(record_json,default=date_to_json, ensure_ascii=False))
          api_webexTeams.messages.create(inc_room_id,text='file processed')
        #print(inc_msg_txt)
        if '/today' in inc_msg.text: #if some one is cheking there today or tomo appointements
            #TODO: add a controle based on the incoming message email to filter only appointements for this doctor
            date_match = re.search('\d{4}-\d{2}-\d{2}', inc_msg.text)
            #check for errors 
            #TODO add timezone everywhere
            start_date= datetime.strptime(date_match.group()+ ' 06:00:00 am','%Y-%m-%d %I:%M:%S %p') #TODO dose this need to be set as global params ?
            end_date  = datetime.strptime(date_match.group()+ ' 10:00:00 pm','%Y-%m-%d %I:%M:%S %p') #TODO dose this need to be set as global params ?
            #print(start_date)
            #print(end_date)

            today_appointments = apointnements_coll.find({'date_start': {'$lt': end_date, '$gte': start_date}})
            print(today_appointments)
            i=0
            for appointment in today_appointments:
              formated_str='# Appointement :'+str(i+1)+'\n'
              for key in appointment:
                if key=='_id': 
                  continue
                formated_str+= '* {:20} : {} \n'.format('**'+key+'**',str(appointment[key]))  #'* **'+key+'** ==' + str(appointment[key]) +'\n'
              print(formated_str)
              api_webexTeams.messages.create(inc_room_id,markdown=formated_str)
              i=i+1
            if i==0:
              api_webexTeams.messages.create(inc_room_id,markdown='> No appoinetement at this day')
            print(datetime.now())
            #print(datetime.timezone)
        if '/set_shedual' in inc_msg.text: 
            date_match     = re.search('\s(\d{2}\:\d{2}\s?(?:AM|PM|am|pm))', inc_msg.text)#timezone ?
            #treshhold_date = datetime.strptime(date_match.group(),'%Y-%m-%d %I:%M:%S %p')
            print(date_match.group())
            print(datetime.now())
            print(time.tzname)

        if '/add_doctor' in inc_msg.text: 
          try:

            print(inc_msg.text)
            input_add     = (re.search('\((.*?)\)', inc_msg.text)).group(1).split(';')
            record_json={}
            record_json['name']=input_add[0]
            record_json['email']=input_add[1]
            print(record_json)
            doctors_coll.insert_one(record_json)
            api_webexTeams.messages.create(inc_room_id,markdown='> Doctor added')
          except:
            api_webexTeams.messages.create(inc_room_id,markdown='> Error')



        return '', 200
  else:
      abort(400)

@app.route('/send_shedual/<date_match>',methods=['GET']) #this endpoint will be calledd by the shedualer to send the appointements to all users reguralrly 
def send_shedual(date_match):
    print(date_match)
    doctors_records = doctors_coll.find({})
    for doctor in doctors_records:
      print(doctor['email'])
      print(doctor['name'])
      
      start_date= datetime.strptime(date_match+ ' 06:00:00 am','%Y-%m-%d %I:%M:%S %p') #TODO dose this need to be set as global params ?
      end_date  = datetime.strptime(date_match+ ' 10:00:00 pm','%Y-%m-%d %I:%M:%S %p') #TODO dose this need to be set as global params ?
      today_appointments = apointnements_coll.find({'date_start': {'$lt': end_date, '$gte': start_date},'name':doctor['name']})
      
      print(today_appointments)
      i=0
      api_webexTeams.messages.create(toPersonEmail=doctor['email'],markdown="Hi **"+doctor['name']+"** here is a list of your appointements today!")
      for appointment in today_appointments:
        formated_str='# Appointement :'+str(i+1)+'\n'
        for key in appointment:
          if key=='_id': 
            continue
          formated_str+= '* {:20} : {} \n'.format('**'+key+'**',str(appointment[key]))  #'* **'+key+'** ==' + str(appointment[key]) +'\n'
        print(formated_str)
        api_webexTeams.messages.create(toPersonEmail=doctor['email'],markdown=formated_str)
        i=i+1
      if i==0:
        api_webexTeams.messages.create(toPersonEmail=doctor['email'],markdown='> No appoinetement at this day')
      print(datetime.now())
      
    return date_match, 200


if __name__ == '__main__':
    try :
        app.run()
    except:
      #log the exceptions
      print('exception')
    finally:
      print('closing DB')
      client.close()