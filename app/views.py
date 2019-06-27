from flask_classy import FlaskView, route
from flask import render_template

from app.sheets_controller import SheetsController


class ShiftsView(FlaskView):
    def __init__(self):
        self.controller = SheetsController()

    @route('/')
    def index(self):
        return render_template('index.html', **locals())

    @route('/student_employees')
    def student_employees_index(self):
        return render_template('student_employees/index.html', **locals())

    @route('/clock_in')
    def clock_in(self):
        return render_template('/student_employees/clock_in.html', **locals())

    @route('/clock_out')
    def clock_out(self):
        return render_template('/student_employees/clock_out.html', **locals())

    @route('/full_time_staff')
    def full_time_staff_index(self):
        return render_template('full_time_staff/index.html', **locals())

    @route('/show_shifts')
    def show_shifts(self):
        return render_template('full_time_staff/show_shifts.html', **locals())

    @route('/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        gen = self.controller.shift_generator(self.controller.help_desk, self.controller.scanner_shifts)
        return render_template('full_time_staff/index.html', **locals()), gen

    @route('/reset_RFID', methods=['GET'])
    def reset_rfid(self):
        res = self.controller.reset_py_data()
        return render_template('full_time_staff/index.html', **locals()), res
