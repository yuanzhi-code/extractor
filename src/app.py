from flask import Flask

from src.config import config


class App(Flask):
    pass


def create_app() -> App:
    app = Flask(__name__)
    app.config = config
    return app


app = create_app()


@app.route("/")
def index():
    return "hello world"
