import os
import requests

from flask import Flask
from flask import request

API_URL = 'https://api.groupme.com/v3/bots/post'
BOT_ID = os.environ['BOT_ID']

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello World!"

#Echo message back
@app.route('/testPost', methods = ['POST'])
def echo():
    data = request.get_json()
    sendMessage(f'Hello {data["name"]}, you said "{data["text"]}"')
    return "good", 200

def sendMessage(text):
    data = {
        'bot_id': BOT_ID,
        'text': text
    }
    r = requests.post(url = API_URL,data = data)
    print(r)

if __name__ == '__main__':
    app.run()
