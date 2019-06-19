from flask import Flask

# Declaring and registering the views
from app.full_time_staff import FullTimeStaffView
from app.student_employees import StudentEmployeesView
from app.views import View

app = Flask(__name__)
app.config.from_object('config')

View.register(app)
FullTimeStaffView.register(app)
StudentEmployeesView.register(app)
