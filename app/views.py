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

    @route('/')
    def index(self):
        return render_template('index.html', **locals())

    # STUDENT EMPLOYEES #

    @route('/student_employees')
    def student_employees_index(self):
        return render_template('student_employees/index.html', **locals())

    @route('/student_employees/timestamp', methods=['POST'])
    def student_sign_in(self):
        nothing = 'sign out'
        return render_template('student_employees/index.html', **locals()), self.sc.student_sign_in(nothing)

    @route('/no-cas/verify-scanner', methods=['POST'])
    def verify_scanner(self):
        form = request.form
        scan = form.get("scan")
        time = form.get("time")
        nothing = 'sign in'
        # Here is where we make call to post this time to spreadsheet as a clock-in
        card_id = re.search("\[\[(.+?)\]\]", scan)
        if card_id:
            # return card_id.group(1)
            return render_template('student_employees/index.html', **locals()), self.sc.student_sign_in(nothing)
        else:
            return 'failed'

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('full_time_staff/index.html', **locals())

    @route('/full_time_staff/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        return render_template('full_time_staff/index.html', **locals()), \
               self.sc.shift_generator(self.sc.help_desk, self.sc.scanner_shifts)

    # USERS #

    @route('/users')
    def users_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('users/users.html', **locals())

    @route('/users/search')
    def add_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('users/add_user.html', **locals())
