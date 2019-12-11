import os
import requests
import pickle
import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import Flask
from flask import request
from random import choice

#App constants
API_URL = 'https://api.groupme.com/v3/bots/post'
GROUPME_URL = 'https://image.groupme.com/pictures'
BOT_ID = os.environ['BOT_ID']
ACCESS_KEY = os.environ['ACCESS_KEY']
CREDENTIAL_DIR = './creds'
BOT_NAME = 'Test'

#Flask App
app = Flask(__name__)

#get google drive credentials
if os.path.exists(os.path.join(CREDENTIAL_DIR,'token.pickle')):
    with open(os.path.join(CREDENTIAL_DIR,'token.pickle'), 'rb') as token:
        creds = pickle.load(token)

#open dictionary
fileDict = {}

#initiate google drive service
driveService = build('drive', 'v3', credentials=creds)

#Routes
@app.route('/message', methods = ['POST'])
def handleMessage():
    data = request.get_json()
    if(data['name'] != BOT_NAME and data['text'].startswith('@mnem')):
        parseRequest(data['text'])
    return 'good', 200

# param: message text to parse
# return: void
def parseRequest(text):
    if('memory' in text):
        sendPic()

# param: google drive id for a single file
# return: url of image stored from groupme service
# downloads file from google drive, uploads to groupme and returns url of image to send
def getImageUrl(fileId):
    if('imageUrl' in fileDict[fileId]):
        return fileDict[fileId]['imageUrl']
    req = driveService.files().get_media(fileId=fileId)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    res = requests.post(url=GROUPME_URL, data=fh,
            headers={'Content-Type': 'image/jpeg','X-Access-Token': ACCESS_KEY})
    imageUrl = res.json()['payload']['url']
    fileDict[fileId]['imageUrl'] = imageUrl
    return imageUrl

# gets metadata for all files stored in google drive
def getFileData():
    results = driveService.files().list(fields='nextPageToken, files(id, name, description)').execute()
    for file in results.get('files', []):
        desc = ''
        if 'description' in file:
            desc = file['description']
        fileDict[file['id']] = {
            'name': file['name'],
            'description': desc
        }

#sends a single picture
def sendPic():
    fileId = choice(list(fileDict.keys()))
    imageUrl = getImageUrl(fileId)
    text = ''
    if('description' in fileDict[fileId]):
        text = fileDict[fileId]['description']
    data = {
        'bot_id': BOT_ID,
        'text': text,
        'picture_url': imageUrl,
        'attachments': [{
            'type': 'image',
            'url': imageUrl
        }]
    }
    r = requests.post(url = API_URL,data = data)

if __name__ == '__main__':
    getFileData()
    app.run()
