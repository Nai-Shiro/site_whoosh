from flask import Flask, render_template, redirect


app = Flask(__name__)


@app.route('/')
def index():
    return "Hello, World!"


def main():  # Функция запуска
    app.run(port=5050)


main()
