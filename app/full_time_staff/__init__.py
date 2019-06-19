from flask_classy import FlaskView, route
from flask import render_template


class FullTimeStaffView(FlaskView):
    route_base = '/staff'

    def __init__(self):
        pass

    @route('/')
    def index(self):
        return render_template('full_time_staff/index.html', **locals())
