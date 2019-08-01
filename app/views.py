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
            # self.sc.student_time_clock(card_id)
            self.sc.student_time_clock(card_id)
            # the code below is repeated from the index method in order to refresh and search through the lists of users
            # and shifts for that day
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

    @route('/process_shifts', methods=['POST'])
    def process_shifts(self):
        self.sc.shift_processor()
        if self.sc.shift_processor() == 'resource exhausted':
            return 'resource exhausted'
        else:
            return 'still going'
        # return render_template('staff_index.html', **locals())

    # USERS #

    @route('/help')
    def how_to(self):
        # self.sc.check_roles_and_route(['Administrator'])
        return render_template('how_to.html', **locals())
