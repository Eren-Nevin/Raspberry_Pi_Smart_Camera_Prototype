from pprint import pprint
from flask import Flask, request

app = Flask(__name__, static_folder='.', static_url_path='/')
app.config['SECRET_KEY'] = 'secret!'

if __name__ == "__main__":
    app.run('0.0.0.0', 4322)
