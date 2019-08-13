# Global
from gspread.exceptions import APIError
import ldap
import re
import time

# Packages
from flask import abort, render_template, request, session
from flask_classy import FlaskView, route

# Local
from app import app
from app.shifts_controller import ShiftsController


class ShiftsView(FlaskView):
    def __init__(self):
        self.sc = ShiftsController()

    def before_request(self, name, **kwargs):
        def init_user():
            if 'session_time' in session.keys():
                seconds_in_12_hours = 60 * 60 * 12  # equates to 12 hours
                reset_session = time.time() - session['session_time'] >= seconds_in_12_hours
            else:
                reset_session = True

            # if not production or 12 hours have past, then clear our session variables on each call
            if reset_session:
                session.clear()
                seconds_in_12_hours = 60 * 60 * 12
                session['session_time'] = time.time() + seconds_in_12_hours

            if 'username' not in session.keys():
                get_user()

            get_its_view()

            # TODO: change to ".. and session['ITS_view'] is False:"
            if '/full-time-staff' in request.path and session['username'] != 'mjw83735':
                abort(403)

            # TODO: change to ".. and (session['ITS_view'] is False and session['ITS_Student_view'] is False):"
            if '/' in request.path and session['username'] != 'mjw83735':
                abort(403)

            if 'ITS_view' not in session.keys() or 'ITS_view' is None or \
                    'ITS_Student_view' not in session.keys() or 'ITS_Student_view' is None:
                get_its_view()

        def get_user():
            if app.config['ENVIRON'] == 'prod':
                username = request.environ.get('REMOTE_USER')
            else:
                username = app.config['TEST_USER']

            session['username'] = username

        def get_its_view():
            try:
                # ITS_view = True if a full-time staff member at the Help Desk
                # ITS_Student_view = True if a student employee at the Help Desk
                session['ITS_view'] = False
                session['ITS_Student_view'] = False
                con = ldap.initialize(app.config['LDAP_CONNECTION_INFO'])
                con.simple_bind_s('BU\svc-tinker', app.config['LDAP_SVC_TINKER_PASSWORD'])

                # code to get all users in a group
                results = con.search_s('ou=Bethel Users,dc=bu,dc=ac,dc=bethel,dc=edu', ldap.SCOPE_SUBTREE,
                                       "(|(&(sAMAccountName=%s)))" % session['username'])

                for result in results:
                    for ldap_string in result[1]['memberOf']:
                        user_iam_group = re.search('CN=([^,]*)', str(ldap_string)).group(1)
                        if user_iam_group == 'ITS - Employees':
                            session['ITS_view'] = True
                        elif user_iam_group == 'ITS - Help Desk Call Center Students' or \
                            user_iam_group == 'ITS - Help Desk Student Managers' or \
                                user_iam_group == 'ITS - Desktop Services Students':
                            session['ITS_Student_view'] = True
            except:
                session['ITS_view'] = False
                session['ITS_Student_view'] = False

        init_user()

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

    @route('/full-time-staff')
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
