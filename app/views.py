# Global
import re

# Packages
from flask import render_template, request, redirect, url_for
from flask import session as flask_session
from flask_classy import FlaskView, route

# Local
# from app.db_repository.user_functions import User
from app.shifts_controller import ShiftsController
# from app.wsapi.wsapi_controller import WSAPIController


class ShiftsView(FlaskView):
    def __init__(self):
        self.sc = ShiftsController()
        # self.wsapi = WSAPIController()

    @route('/')
    def index(self):
        return render_template('index.html', **locals())

    # STUDENT EMPLOYEES #

    @route('/student_employees')
    def student_employees_index(self):
        return render_template('student_employees/index.html', **locals())

    @route('/student_employees/sign_in')
    def sign_in(self):
        return render_template('student_employees/sign_in.html', **locals())

    @route('/student_employees/sign_out')
    def sign_out(self):
        return render_template('student_employees/sign_out.html', **locals())

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('full_time_staff/index.html', **locals())

    @route('/full_time_staff/show_shifts')
    def show_shifts(self):
        return render_template('full_time_staff/show_shifts.html', **locals())

    @route('/full_time_staff/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        return render_template('full_time_staff/index.html', **locals()), \
               self.sc.shift_generator(self.sc.help_desk, self.sc.scanner_shifts)

    @route('/full_time_staff/reset_scanner', methods=['GET'])
    def reset_scanner(self):
        return render_template('full_time_staff/index.html', **locals()), self.sc.reset_py_data()

    # USERS #

    @route('/users')
    def users_index(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('users/users.html', **locals())

    @route('/users/search')
    def add_user(self):
        self.sc.check_roles_and_route(['Administrator'])
        return render_template('users/add_user.html', **locals())

    # OTHER #

    # @route('/no-cas/verify-scanner', methods=['post'])
    # def verify_scanner(self):
    #     form = request.form
    #     scan = form.get("scan")
    #     card_id = re.search("\[\[(.+?)\]\]", scan)
    #     if card_id:
    #         return card_id.group(1)
    #     else:
    #         return 'failed'
