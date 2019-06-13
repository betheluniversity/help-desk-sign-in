from flask import render_template, request
from flask_classy import FlaskView, route


class View(FlaskView):
    @route('/')
    def base(self):
        return render_template('manager_view.html')
