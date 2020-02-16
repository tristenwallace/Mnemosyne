import os
import requests
import pickle
import io
import pymongo

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, date

GROUPME_URL = 'https://image.groupme.com/pictures'
MONGO_URI = os.environ['MONGODB_URI'] + '?retryWrites=false'
API_URL = 'https://api.groupme.com/v3/bots/post'
BOT_NAME = 'Test'
BOT_ID = os.environ['BOT_ID']
GROUPME_ACCESS_KEY = os.environ['ACCESS_KEY']

def getCurrentWeek():
    today = date.today()
    startOfWeek = today - timedelta(days=today.weekday())  # Monday
    endOfWeek = startOfWeek + timedelta(days=6)  # Sunday
    return (startOfWeek.strftime('%Y-%m-%d'), endOfWeek.strftime('%Y-%m-%d'))

def getLastWeek(): #should only be run by cronjob on monday
    today = date.today()
    startOfWeek = today - timedelta(days=7) #last Monday
    endOfWeek = startOfWeek + timedelta(days=6)  #Last Sunday
    return (startOfWeek.strftime('%Y-%m-%d'), endOfWeek.strftime('%Y-%m-%d'))

# param db: a mongodb connection
# gets google drive credentials from mongodb
def getGoogleCreds(db):
    creds = None
    dbCreds = db.creds.find_one({})
    if(dbCreds):
        creds = pickle.loads(dbCreds['rawCreds'])
        return creds
    #TODO - add mechanism to refresh creds
    #if not creds or not creds.valid:

# param db: a mongodb connection
# returns a google drive service
def getGoogleService(db):
    creds = getGoogleCreds(db)
    return build('drive', 'v3', credentials=creds)

# returns a mongo db connection
def getMongoDb():
    #TODO - Add error checking
    client = pymongo.MongoClient(MONGO_URI)
    db = client.get_default_database()
    return db

# param driveService: google drive service
# returns a dictionary from fileId to name and description
# gets a list of file metadatas stored in google drive
def getFiles(driveService):
    fileDict = {}
    results = driveService.files().list(fields='nextPageToken, files(id, name, description)').execute()
    for file in results.get('files', []):
        desc = ''
        if 'description' in file:
            desc = file['description']
        fileDict[file['id']] = {
            'name': file['name'],
            'description': desc
        }
    return fileDict

# param fileId: google drive id for a single file
# param fileDict: dictionary of file infos
# param driveService: google drive service
# return: url of image stored from groupme service
# downloads file from google drive, uploads to groupme and returns url of image to send
def getImageUrl(fileId, fileDict, driveService):
    if('imageUrl' in fileDict[fileId]):
        return fileDict[fileId]['imageUrl']
    try:
        req = driveService.files().get_media(fileId=fileId)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, req)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        fh.seek(0)
        res = requests.post(url=GROUPME_URL, data=fh,
                headers={'Content-Type': 'image/jpeg','X-Access-Token': GROUPME_ACCESS_KEY})
        imageUrl = res.json()['payload']['url']
        fileDict[fileId]['imageUrl'] = imageUrl
        return imageUrl
    except:
        getImageUrl(fileId, fileDict, driveService)

#param data: dictionary of metadata and info to send
#Posts given data to groupme
def post(data):
    requests.post(url = API_URL,data = data)

def postText(text):
    data = {
        'bot_id': BOT_ID,
        'text': text
    }
    post(data)

def postImage(text, imageUrl):
    data = {
        'bot_id': BOT_ID,
        'text': text,
        'picture_url': imageUrl,
        'attachments': [{
            'type': 'image',
            'url': imageUrl
        }]
    }
    post(data)

def formatGoalString(goal):
    return f'''
@{goal['name']}, your goal for {goal['startDate']} - {goal['endDate']} is:
{goal['goal']}
The status of your goal is: {goal['status']}
    '''

def formatThisWeeksGoalsString(goals, week):
    goalString = ''
    for goal in goals:
        goalString += f'{goal["name"]}: {goal["goal"]} - {goal["status"]}\n'

    if(goalString == ''):
        return 'There are no goals yet this week'
    else:
        return f'Here are the goals for {week[0]} - {week[1]}:\n' + goalString
