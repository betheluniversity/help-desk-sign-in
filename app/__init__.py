# Packages
from flask import Flask  # , request
# from flask import session as flask_session

app = Flask(__name__)
app.config.from_object('config')

# Declaring and registering the view
from app.views import ShiftsView

ShiftsView.register(app, route_base='/')

# @app.before_request
# def before_request():
#     if '/static/' in request.path \
#             or '/assets/' in request.path \
#             or '/cron/' in request.path \
#             or '/no-cas/' in request.path:
#
#         if 'ALERT' not in flask_session.keys():
#             flask_session['ALERT'] = []
#     else:
#         if 'USERNAME' not in flask_session.keys():
#             if app.config['ENVIRON'] == 'prod':
#                 username = request.environ.get('REMOTE_USER')
#             else:
#                 username = app.config['TEST_USERNAME']
#             # current_user = User().get_user_by_username(username)
#             # if not current_user:
#             #     current_user = User().create_user_at_sign_in(username)
#             # if current_user.deletedAt != None:  # User has been soft deleted in the past, needs reactivating
#             #     User().activate_existing_user(current_user.username)
#             # flask_session['USERNAME'] = current_user.username
#             flask_session['USERNAME'] = username
#             first_name = app.config['TEST_FIRSTNAME']
#             last_name = app.config['TEST_LASTNAME']
#             # flask_session['NAME'] = '{0} {1}'.format(current_user.firstName, current_user.lastName)
#             flask_session['NAME'] = '{0} {1}'.format(first_name, last_name)
#             flask_session['USER-ROLES'] = []
#             # user_roles = User().get_user_roles(current_user.id)
#             # for role in user_roles:
#             #     flask_session['USER-ROLES'].append(role.name)
#         if 'NAME' not in flask_session.keys():
#             flask_session['NAME'] = flask_session['USERNAME']
#         # if 'USER-ROLES' not in flask_session.keys():
#         #     flask_session['USER-ROLES'] = ['STUDENT']
#         flask_session['USER-ROLES'] = ['Administrator']
#         if 'ADMIN-VIEWER' not in flask_session.keys():
#             flask_session['ADMIN-VIEWER'] = False
#         if 'ALERT' not in flask_session.keys():
#             flask_session['ALERT'] = []
