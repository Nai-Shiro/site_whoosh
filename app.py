from flask import Flask, render_template, redirect


app = Flask(__name__)


def main():  # Функция запуска
    app.run(port=5050)