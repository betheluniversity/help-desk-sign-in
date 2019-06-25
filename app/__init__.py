from flask import Flask

# Declaring and registering the view
from app.views.__init__ import ShiftsView

app = Flask(__name__)
app.config.from_object('config')

ShiftsView.register(app, route_base='/')
