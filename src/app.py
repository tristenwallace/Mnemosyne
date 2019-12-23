import os

from flask import Flask
from flask import request
from random import choice
from utils.utils import *

#App constants
BOT_NAME = 'Test'

#Flask App
app = Flask(__name__)

#Initiate connections and get files
db = getMongoDb()
driveService = getGoogleService(db)
fileDict = getFiles(driveService)

@app.route('/message', methods = ['POST'])
def handleMessage():
    data = request.get_json()
    text = data['text'].lower()
    if(data['name'] != BOT_NAME and text.startswith('@mnem')):
        if('send a memory' in text):
            sendPic()
        elif('add a goal:' in text):
            addGoal(data['name'], text)
        elif('list goals' in text):
            listGoals()
        elif('help' in text):
            listHelp()
    return 'good', 200

def addGoal(name, text):
    goal = ''.join(text.split('add a goal:')[1:]).strip()
    week = getCurrentWeek()
    print(week[0], week[1])
    print(goal)

def listGoals():
    pass

def listHelp():
    helpText = '''
        Use the following commands:
        @mnem send a memory
        @mnem add a goal
        @mnem list goals
        @mnem help
    '''
    data = {
        'bot_id': BOT_ID,
        'text': helpText
    }
    post(data)

#sends a single picture
def sendPic():
    fileId = choice(list(fileDict.keys()))
    imageUrl = getImageUrl(fileId, fileDict, driveService)
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
    post(data)

if __name__ == '__main__':
    app.run()
