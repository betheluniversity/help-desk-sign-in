from flask_classy import FlaskView, route
from flask import render_template


class FullTimeStaffView(FlaskView):
    route_base = '/staff'

    def __init__(self):
        pass

    @route('/')
    def index(self):
        return render_template('full_time_staff/index.html', **locals())

    # Test method for how the spreadsheet.py file can be run in the future
    @route('generate_shifts')
    def generate_shifts(self):
        return render_template('full_time_staff/generate_shifts.html', **locals())
