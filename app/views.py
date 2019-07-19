# Global
import re

# Packages
from flask import render_template, request
from flask_classy import FlaskView, route

# Local
from app.shifts_controller import ShiftsController


class ShiftsView(FlaskView):
    def __init__(self):
        self.sc = ShiftsController()

    # STUDENT EMPLOYEES #

    @route('/')
    def index(self):
        return render_template('student_index.html', **locals())

    @route('/student_employees/timestamp', methods=['POST'])
    def student_time_clock(self):
        nothing = 'sign out'
        form = request.form
        time = form.get("time")
        print(self.sc.convert12(time))

        return render_template('student_index.html', **locals()), self.sc.student_time_clock(nothing)

    @route('/no-cas/verify-scanner', methods=['POST'])
    def verify_scanner(self):
        form = request.form
        scan = form.get("scan")
        time = form.get("time")
        print(self.sc.convert12(time))
        nothing = 'sign in'
        # Here is where we make call to post this time to spreadsheet as a clock-in
        card_id = re.search("\[\[(.+?)\]\]", scan)
        scan = scan[2:-2]
        if card_id:
            # return card_id.group(1)
            return render_template('student_index.html', **locals()), self.sc.student_time_clock(nothing)
        else:
            return 'failed'

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('staff_index.html', **locals())

    @route('/full_time_staff/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        return render_template('staff_index.html', **locals()), \
               self.sc.shift_generator(self.sc.help_desk, self.sc.scanner_shifts)

    # USERS #

    @route('/users')
    def users_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('users_index.html', **locals())
