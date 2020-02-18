# Global
from gspread.exceptions import APIError
import ldap
import re
import time

# Packages
from flask import abort, make_response, redirect, render_template, request, session, url_for
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

            # if accessing staff-only pages, then get username and check if user has ITS - Employee role in IAM
            if '/staff' in request.path or '/help' in request.path:
                get_user()
                get_its_view()

                if session['ITS_view'] is False:  # after checking ITS_view, if not staff, then abort
                    abort(403)

        def get_user():
            if app.config['ENVIRON'] == 'prod':
                username = request.environ.get('REMOTE_USER')
            else:
                username = app.config['TEST_USER']

            session['username'] = username

        def get_its_view():
            try:
                session['ITS_view'] = False
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
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
            except:
                session['ITS_view'] = False

        init_user()

    @route('/')
    def index(self):
        return render_template('index.html', **locals())

    @route('/student-signin')
    def student_signin(self):
        try:
            day_list = self.sc.day_list()
            return render_template('student_signin.html', day_list=day_list)
        except APIError:
            # does not display table of shifts since day_list is where the API calls for shift data occur
            return render_template('student_signin.html', **locals())

    @route('/verify_scanner', methods=['POST'])
    def verify_scanner(self):
        try:
            form = request.form
            scan = form.get("scan")
            scan_success = re.search("\[\[(.+?)\]\]", scan)
            day_list = self.sc.day_list()
            alert_type = 'danger'
            alert_message = 'Scan failed, please try again'
            try:
                card_id = int(scan[2:-2])
            except ValueError:
                return render_template('shifts_table.html', **locals())
            if scan_success and len(scan[2:-2]) == 5:
                alert_message = 'Scan failed, user not found'
                if self.sc.student_time_clock(card_id):
                    day_list = self.sc.day_list()
                    alert_type = 'success'
                    alert_message = 'Scan successful'
            return render_template('shifts_table.html', **locals())
        except APIError as api_error:
            alert_type = 'danger'
            alert_message = 'Error: Server exhausted, please wait 1 minute and try again'
            if str(api_error).find("RESOURCE_EXHAUSTED"):
                return render_template('shifts_table.html', **locals())

    @route('/staff')
    def staff_index(self):
        return render_template('staff_index.html', **locals())

    @route('/process_shifts', methods=['POST'])
    def process_shifts(self):
        try:
            self.sc.shift_processor()
            alert_type = 'success'
            alert_message = 'Shift data processing complete'
            return render_template('shift_alert.html', **locals())
        except IndexError:
            alert_type = 'warning'
            alert_message = 'Error: Data mismatch between Service Desk Schedule and Scanner Data'
            return render_template('shift_alert.html', **locals())
        except APIError as api_error:
            alert_type = 'danger'
            alert_message = 'Error: Server exhausted, please wait 1 minute and try again'
            if str(api_error).find("RESOURCE_EXHAUSTED"):
                return render_template('shift_alert.html', **locals())

    @route('/help')
    def help(self):
        return render_template('help.html', **locals())

    @route('/cas_passthrough')
    def cas_passthrough(self):
        if app.config.get('ENVIRON') == 'prod':
            session.clear()
            resp = make_response(redirect(app.config['LOGOUT_URL'] + '?service=' + request.host_url[:-1] +
                                          url_for('ShiftsView:student_signin')))
            resp.set_cookie('MOD_AUTH_CAS_S', '', expires=0, path='/')
            resp.set_cookie('MOD_AUTH_CAS', '', expires=0, path='/')
            return resp
        else:
            return redirect(url_for('ShiftsView:student_signin'))

    @app.errorhandler(403)
    def permission_denied(self):
        return render_template('error403.html', **locals())

    @app.errorhandler(500)
    def server_error(self):
        return render_template('error500.html', **locals())
