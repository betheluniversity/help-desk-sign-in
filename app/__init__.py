import logging

# Packages
from flask import Flask
import sentry_sdk

app = Flask(__name__)
app.config.from_object('config')

# Declaring and registering the view
from app.views import ShiftsView

if app.config['ENVIRON'] == 'prod' and app.config['SENTRY_URL']:
    from sentry_sdk.integrations.flask import FlaskIntegration
    sentry_sdk.init(dsn=app.config['SENTRY_URL'], integrations=[FlaskIntegration()])

ShiftsView.register(app, route_base='/')
