from flask import render_template
from flask_classy import FlaskView


class FullTimeStaffView(FlaskView):
    def __init__(self):
        pass

    def index(self):
        return render_template('full_time_staff/index.html', **locals())
