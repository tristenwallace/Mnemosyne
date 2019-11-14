from flask import Flask
from flask import request

app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello World!"

@app.route('/testPost', methods = ['POST'])
def update_text():
    data = request.get_json()
    print(data)
    #print(data['text'])
    #print(data['name'])
    return "good", 200

if __name__ == '__main__':
    app.run()
