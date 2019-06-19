from flask_classy import FlaskView, route
from flask import render_template


class View(FlaskView):
    @route('/')
    def index(self):
        return render_template('index.html', **locals())
