# Global
from gspread.exceptions import APIError
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
        try:
            day_list = self.sc.day_list()
            return render_template('student_index.html', day_list=day_list)
        except APIError:
            # displays table of no shifts, since shift data is where the API calls occur
            return render_template('student_index.html', **locals())

    @route('/verify_scanner', methods=['POST'])
    def verify_scanner(self):
        try:
            form = request.form
            scan = form.get("scan")
            scan_success = re.search("\[\[(.+?)\]\]", scan)
            if scan_success and len(scan[2:-2]) == 5:
                card_id = int(scan[2:-2])
                self.sc.student_time_clock(card_id)
                day_list = self.sc.day_list()
                return render_template('student_table.html', day_list=day_list)
            else:
                return 'failed'
        except APIError:
            return 'resource exhausted'

    # FULL-TIME STAFF #

    @route('/full_time_staff')
    def full_time_staff_index(self):
        return render_template('staff_index.html', **locals())

    @route('/process_shifts', methods=['POST'])
    def process_shifts(self):
        try:
            self.sc.shift_processor()
            return 'shift data processing complete'
        except APIError:
            return 'resource exhausted'

    @route('/help')
    def help(self):
        return render_template('help.html', **locals())
