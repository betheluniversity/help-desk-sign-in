from flask import Flask
from app.full_time_staff import ShiftView

app = Flask(__name__)
app.config.from_object('config')

ShiftView.register(app, route_base='/')
