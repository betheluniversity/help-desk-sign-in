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

    @route('/users/admin/<int:user_id>')
    def edit_user(self, user_id):
        self.sc.check_roles_and_route(['Administrator'])
        user = self.user.get_user(user_id)
        roles = self.user.get_all_roles()
        user_role_ids = self.user.get_user_role_ids(user_id)
        return render_template('users/edit_user.html', **locals())

    @route('/users/create/<username>/<first_name>/<last_name>')
    def select_user_roles(self, username, first_name, last_name):
        self.sc.check_roles_and_route(['Administrator'])
        roles = self.user.get_all_roles()
        existing_user = self.user.get_user_by_username(username)
        if existing_user:  # User exists in system
            message = 'This user already exists in the system and is activated.'
        return render_template('users/select_user_roles.html', **locals())

    @route('/users/search-users', methods=['POST'])
    def search_users(self):
        self.sc.check_roles_and_route(['Administrator'])
        form = request.form
        first_name = form.get('firstName')
        last_name = form.get('lastName')
        # results = self.wsapi.get_username_from_name(first_name, last_name)
        return render_template('users/user_search_results.html', **locals())

    @route('users/save-user-edits', methods=['POST'])
    def save_user_edits(self):
        self.sc.check_roles_and_route(['Administrator'])
        form = request.form
        user_id = form.get('user-id')
        username = form.get('username')
        first_name = form.get('first-name')
        last_name = form.get('last-name')
        roles = form.getlist('roles')
        try:
            self.user.update_user_info(user_id, first_name, last_name)
            self.user.clear_current_roles(user_id)
            self.user.set_user_roles(username, roles)
            self.slc.set_alert('success', 'Edited {0} {1} ({2}) successfully!'.format(first_name, last_name, username))
            return redirect(url_for('ShiftsView:users_index'))
        except Exception as error:
            self.slc.set_alert('danger', 'Failed to edit user: {0}'.format(str(error)))
            return redirect(url_for('ShiftsView:edit_user', user_id=user_id))

    @route('/users/create-users', methods=['POST'])
    def create_user(self):
        self.slc.check_roles_and_route(['Administrator'])
        form = request.form
        first_name = form.get('first-name')
        last_name = form.get('last-name')
        username = form.get('username')
        roles = form.getlist('roles')
        try:
            self.user.create_user(first_name, last_name, username)
            self.user.set_user_roles(username, roles)
            self.slc.set_alert('success', '{0} {1} ({2}) added successfully!'.format(first_name, last_name, username))
            return redirect(url_for('ShiftsView:users_index'))
        except Exception as error:
            self.slc.set_alert('danger', 'Failed to add user: {0}'.format(str(error)))
            return redirect(url_for('ShiftsView:select_user_roles', username=username, first_name=first_name,
                                    last_name=last_name))

    # OTHER #

    @route('/no-cas/verify-scanner', methods=['post'])
    def verify_scanner(self):
        form = request.form
        scan = form.get("scan")
        card_id = re.search("\[\[(.+?)\]\]", scan)
        if card_id:
            return card_id.group(1)
        else:
            return 'failed'
