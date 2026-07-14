"""This is a web-app that created to provide more information
about food poisoning and food incompatibility using Python (Flask) and React"""
import sqlite3
from pathlib import Path 
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)
DATABASE = Path(__file__).with_name("purebite.db")


"Connect the database with the python file"
def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection 


"""Create a data base for the food compatibility checker"""
def create_database():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS foods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL COLLATE NOCASE,
            food_group TEXT NOT NULL)
    """ )

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS combination_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_one TEXT NOT NULL,
            group two TEXT NOT NULL, 
            result TEXT NOT NULL, 
            message TEXT NOT NULL)
    """)

    foods = [
        ("milk", "dairy"),
        ("cheese", "dairy"),
        ("yoghurt", "dairy"),
        ("orange", "acidic"),
        ("lemon", "acidic"),
        ("lime", "acidic"),
        ("banana", "fruit"),
        ("apple", "fruit"),
        ("fish", "protein"),
        ("chicken", "protein"),
        ("egg", "protein"),
        ("energy drink", "caffeinated"),
        ("alcohol", "alcohol"),
    ]
 
    rules = [
        ("dairy", "acidic", "Caution", 
         "This combination can cause dairy to curdle. It is usually not harmful, but some people may find it uncomfortable."
        ), 

        ("alcohol", "caffeinated", "Avoid",
         "Caffein can hide the effects of alcohol and make it easier to drink more intended."),
    ]

    cursor.executemany(
        "INSERT OR IGNORE INTO foods (name, food_group) VALUES (?, ?)",
        foods
    )

    cursor.executemany("""
        INSERT OR IGNORE INTO combination_rules
        (group_one, group_two, result, message)
        VALUES (?, ?, ?, ?)
    """, rules)

    connection.commit()
    connection.close()

    
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
