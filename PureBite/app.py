from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)


if __name__ == '__main__':
    app.run(debug=True)
