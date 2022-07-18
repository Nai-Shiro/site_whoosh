from flask import Flask, render_template, redirect


app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, World!"


def main():  # Функция запуска
    import os
    ON_HEROKU = os.environ.get('ON_HEROKU')
    if ON_HEROKU:
        port = int(os.environ.get("PORT", 17995))
    else:
        port = 3000
    app.run(port=port)


main()
