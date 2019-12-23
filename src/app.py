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
        elif('check my current goal' in  text):
            checkGoal(data['name'])
        elif('i finished my goal' in text):
            updateStatus(data['name'], 'Completed')
        elif('i failed my goal' in text):
            updateStatus(data['name'], 'Failed')
        elif('my goal is in progress' in text):
            updateStatus(data['name'], 'In Progress')
        elif('help' in text):
            listHelp()
        else:
            errorMessage = f'@{data["name"]}, I do not recognize that command, enter "@mnem help" to get a list of valid commands'
            postText(errorMessage)
    return 'good stuff', 200

def updateStatus(name, status):
    week = getCurrentWeek()
    query = {
        'startDate': week[0],
        'endDate': week[1],
        'name': name
    }
    goal = db.goals.find_one(query)
    goal['status'] = status
    if(goal):
        db.goals.update_one({'_id': goal['_id']}, {"$set": goal})
        resp = f'@{name}, the status of your current date was set to: {status}'
        postText(resp)
    else:
        errorMessage = f'@{name}, you do not have a goal specified for {week[0]} - {week[1]}. Enter "@mnem add a goal: [new goal]" to add a goal'
        postText(errorMessage)


def checkGoal(name):
    week = getCurrentWeek()
    query = {
        'startDate': week[0],
        'endDate': week[1],
        'name': name
    }
    goal = db.goals.find_one(query)
    if(goal):
        postText(formatGoalString(goal))
    else:
        errorMessage = f'@{name}, you do not have a goal specified for {week[0]} - {week[1]}. Enter "@mnem add a goal: [new goal]" to add a goal'
        postText(errorMessage)

def addGoal(name, text):
    goal = ''.join(text.split('add a goal:')[1:]).strip() #some clever parsing
    if(not goal):
        postText(f'@{name}, the goal you specified is invalid')
        return
    week = getCurrentWeek()
    goalDoc = {
        'goal': goal,
        'startDate': week[0],
        'endDate': week[1],
        'status': 'In Progress',
        'name': name
    }
    db.goals.insert_one(goalDoc)
    postText(f'@{name}, your goal was saved')

def listGoals():
    week = getCurrentWeek()
    query = {
        'startDate': week[0],
        'endDate': week[1]
    }
    goals = db.goals.find(query)
    postText(formatThisWeeksGoalsString(goals, week))

def listHelp():
    helpText = '''
    Use the following commands:
        @mnem send a memory
        @mnem add a goal
        @mnem list goals
        @mnem check my current goal
        @mnem i failed my goal
        @mnem i finished my goal
        @mnem my goal is in progress
        @mnem help
    '''
    postText(helpText)

#sends a single picture
def sendPic():
    fileId = choice(list(fileDict.keys()))
    imageUrl = getImageUrl(fileId, fileDict, driveService)
    text = ''
    if('description' in fileDict[fileId]):
        text = fileDict[fileId]['description']
    postImage(text, imageUrl)

if __name__ == '__main__':
    app.run()
