from flask import render_template, request
from flask_classy import FlaskView, route


class TestView(FlaskView):
    @route('/')
    def base(self):
        return 'Test'
