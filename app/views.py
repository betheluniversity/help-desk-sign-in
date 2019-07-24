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
        shifts_list = self.sc.shifts_list()
        users_list = self.sc.users_list()
        for shift in shifts_list:
            for user in users_list:
                if user['Username'] == shift['Username']:
                    shift['Username'] = user['Name']
        return render_template('student_index.html', shifts_list=shifts_list)

    @route('/student_employees/timestamp', methods=['POST'])
    def student_time_clock(self):
        scan_type = 'sign out'
        form = request.form
        time = form.get("time")
        card_id = ''
        return render_template('student_index.html', **locals()), self.sc.student_time_clock(scan_type, card_id)

    # @route('/no-cas/verify-scanner', methods=['POST'])
    @route('/verify_scanner', methods=['POST'])
    def verify_scanner(self):
        form = request.form
        scan = form.get("scan")
        scan_success = re.search("\[\[(.+?)\]\]", scan)
        if scan_success:
            scan_type = 'sign in'
            card_id = int(scan[2:-2])
            shifts_list = self.sc.shifts_list()
            users_list = self.sc.users_list()
            for user in users_list:
                if user['Card ID'] == card_id:
                    student_name = user['Name']
            return render_template('student_table.html', student_name=student_name, shifts_list=shifts_list,
                                   scan_type=scan_type), self.sc.student_time_clock(scan_type, card_id)
        else:
            return 'failed'

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        # self.sc.check_roles_and_route(['Administrator'])
        return render_template('staff_index.html', **locals())

    @route('/full_time_staff/generate_shifts', methods=['GET'])
    def generate_shifts(self):
        return render_template('staff_index.html', **locals()), \
               self.sc.shift_generator(self.sc.hd_shifts, self.sc.scanner_shifts)

    # USERS #

    @route('/users')
    def users_index(self):
        # self.sc.check_roles_and_route(['Administrator'])
        users_list = self.sc.users_list()
        users_list = self.sc.multi_key_sort(users_list, ['Name', 'Username'])
        for user in users_list:
            user['Card ID'] = str(user['Card ID'])
            while len(user['Card ID']) != 5:
                user['Card ID'] = '0' + user['Card ID']
        return render_template('users_index.html', users_list=users_list)

    @route('/users/users_table', methods=['POST'])
    def add_user(self):
        form = request.form
        student_name = form.get("student_name")
        username = form.get("username")
        card_id = form.get("card_id")
        return render_template('users_table.html', student_name=student_name, username=username,
                               card_id=card_id), self.sc.add_users(student_name, username, card_id)
