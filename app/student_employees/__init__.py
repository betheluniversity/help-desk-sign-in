from flask_classy import FlaskView, route
from flask import render_template


class StudentEmployeesView(FlaskView):
    route_base = '/student'

    def __init__(self):
        pass

    @route('/')
    def index(self):
        return render_template('student_employees/index.html', **locals())
