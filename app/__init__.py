import logging

# Packages
from flask import Flask
from raven.contrib.flask import Sentry

app = Flask(__name__)
app.config.from_object('config')

# Declaring and registering the view
from app.views import ShiftsView

sentry = Sentry(app, dsn=app.config['SENTRY_URL'], logging=True, level=logging.ERROR)

ShiftsView.register(app, route_base='/')
