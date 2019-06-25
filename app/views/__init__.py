from flask_classy import FlaskView, route
from flask import render_template


class ShiftsView(FlaskView):
    @route('/')
    def index(self):
        return render_template('index.html', **locals())

    @route('/student_employees')
    def student_employees_index(self):
        return render_template('student_employees/index.html', **locals())

    @route('/full_time_staff')
    def full_time_staff_index(self):
        return render_template('full_time_staff/index.html', **locals())

    @route('/show_shifts')
    def show_shifts(self):
        return render_template('full_time_staff/show_shifts.html', **locals())

    @route('/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        # do something
        return render_template('full_time_staff/index.html', **locals())

    @route('get_new_data')
    def get_new_data(self):
        return 'EMPTY'
