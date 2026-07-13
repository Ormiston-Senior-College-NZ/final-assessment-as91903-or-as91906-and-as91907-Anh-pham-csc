"""This is a web-app that created to provide more information
about food poisoning and food incompatibility"""
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/check', methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        stname = request.form.get('stfoodname')
        ndname = request.form.get('ndfoodname')
        print(stname, ndname)
    return render_template('name.html')
@app.route('/')
def home():
    return redirect(url_for('check'))

if __name__ == '__main__':
    app.run(debug=True)
