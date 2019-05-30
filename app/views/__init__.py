from flask import render_template, request
from flask_classy import FlaskView, route


class TestView(FlaskView):
    # Method that initially renders the index.html class
    @route('/')
    def index(self):
        return 'Test'
