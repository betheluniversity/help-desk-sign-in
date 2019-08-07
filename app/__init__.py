# Packages
from flask import Flask

app = Flask(__name__)
app.config.from_object('config')

# Declaring and registering the view
from app.views import ShiftsView

ShiftsView.register(app, route_base='/')
