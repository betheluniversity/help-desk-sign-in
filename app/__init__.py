from flask import Flask
from app.views import View

app = Flask(__name__)
app.config.from_object('config')

View.register(app, route_base='/')
