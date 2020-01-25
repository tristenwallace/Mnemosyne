import os

from flask import Flask
from flask import request
from random import choice
from utils.utils import *
from apscheduler.schedulers.background import BackgroundScheduler
from random import randint

#App constants
BOT_NAME = 'Test'

#Flask App
app = Flask(__name__)

#Initiate connections and get files
db = getMongoDb()
driveService = getGoogleService(db)
fileDict = getFiles(driveService)
scheduler = BackgroundScheduler()

def weeklyPic():
    if(randint(1,2) == 1):
        sendPic()

def lastChance():
    postText('Hello, If you completed your goal this week, please post "@mnem i finished my goal" by noon tomorrow')

def endOfWeek(): #should run Monday afternoon
    week = getLastWeek()
    query = {
        'startDate': week[0],
        'endDate': week[1],
        'status': 'In Progress'
    }
    goals = db.goals.update(query, { '$set': { 'status': 'Failed'}}, multi=True )
    listGoalsForWeek(week)

def sendPic():
    fileId = choice(list(fileDict.keys()))
    imageUrl = getImageUrl(fileId, fileDict, driveService)
    text = ''
    if('description' in fileDict[fileId]):
        text = fileDict[fileId]['description']
    postImage(text, imageUrl)

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

def listGoalsForWeek(week):
    query = {
        'startDate': week[0],
        'endDate': week[1]
    }
    goals = db.goals.find(query)
    postText(formatThisWeeksGoalsString(goals, week))

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
        resp = f'@{name}, the status of your current goal was set to: {status}'
        postText(resp)
    else:
        errorMessage = f'@{name}, you do not have a goal specified for {week[0]} - {week[1]}. Enter "@mnem add a goal: [new goal]" to add a goal'
        postText(errorMessage)

def listHelp():
    helpText = '''
    Use the following commands:
        @mnem add a goal: some goal
        @mnem list all goals
        @mnem check my current goal
        @mnem i finished my goal
        @mnem send a memory
        @mnem help
    '''
    postText(helpText)

@app.route('/message', methods = ['POST'])
def handleMessage():
    data = request.get_json()
    text = data['text'].lower()
    if(data['name'] != BOT_NAME and text.startswith('@mnem')):
        if('send a memory' in text):
            sendPic()
        elif('add a goal:' in text):
            addGoal(data['name'], text)
        elif('list all goals' in text):
            #listGoalsForWeek(getCurrentWeek)
            endOfWeek()
        elif('check my current goal' in  text):
            checkGoal(data['name'])
        elif('i finished my goal' in text):
            updateStatus(data['name'], 'Completed')
        elif('help' in text):
            listHelp()
        else:
            errorMessage = f'@{data["name"]}, I do not recognize that command, enter "@mnem help" to get a list of valid commands'
            postText(errorMessage)
    return 'good stuff', 200

@app.route('/init', methods = ['GET'])
def initMessage():
    postText("Hello everyone, I'm Mnemosyne. I'm here to send you memories and to keep track of your weekly goals.")
    listHelp()
    return 'good stuff', 200

if __name__ == '__main__':
    #Init Scheduler
    scheduler.add_job(lastChance, 'cron', day_of_week='sun',hour='12',minute='0')
    scheduler.add_job(endOfWeek, 'cron', day_of_week='mon',hour='12',minute='0')
    scheduler.add_job(weeklyPic, 'cron', day_of_week='*',hour='16',minute='0')
    scheduler.start()
    app.run()
