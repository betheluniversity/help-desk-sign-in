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
        shifts_list = self.sc.day_list()
        users_list = self.sc.users_list()
        for shift in shifts_list:
            for user in users_list:
                if user['Username'] == shift['Username']:
                    shift['Username'] = user['Name']
        return render_template('student_index.html', shifts_list=shifts_list)

    @route('/verify_scanner', methods=['POST'])
    def verify_scanner(self):
        form = request.form
        scan = form.get("scan")
        scan_success = re.search("\[\[(.+?)\]\]", scan)
        if scan_success and len(scan[2:-2]) == 5:
            card_id = int(scan[2:-2])
            self.sc.student_time_clock(card_id)
            self.sc.student_shifts_today(card_id)
            # the code below is repeated from the index method in order to refresh and search through the lists of
            # users and shifts for that day
            users_list = self.sc.users_list()
            shifts_list = self.sc.day_list()
            for shift in shifts_list:
                for user in users_list:
                    if shift['Username'] == user['Username']:
                        shift['Username'] = user['Name']
            return render_template('student_table.html', shifts_list=shifts_list)
        else:
            return 'failed'

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        # self.sc.check_roles_and_route(['Administrator'])
        return render_template('staff_index.html', **locals())

    @route('/full_time_staff/generate_shifts', methods=['POST'])
    def generate_shifts(self):
        self.sc.shift_generator(self.sc.hd_shifts, self.sc.scanner_shifts)
        return render_template('staff_index.html', **locals())

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
        self.sc.add_users(student_name, username, card_id)
        # the code below is repeated from the users_index in order to refresh the list of users once a new user
        # has been added
        users_list = self.sc.users_list()
        users_list = self.sc.multi_key_sort(users_list, ['Name', 'Username'])
        for user in users_list:
            user['Card ID'] = str(user['Card ID'])
            while len(user['Card ID']) != 5:
                user['Card ID'] = '0' + user['Card ID']
        return render_template('users_table.html', users_list=users_list)
