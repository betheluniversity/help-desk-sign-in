from flask import render_template
from flask_classy import FlaskView


class StudentEmployeesView(FlaskView):
    def __init__(self):
        pass

    def index(self):
        return render_template('student_employees/index.html', **locals())
