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

    FOOD_GROUPS = {
        "dairy": [
            "milk", "skim milk", "whole milk",
            "cheese", "mozzarella", "parmesan",
            "yoghurt", "Greek yoghurt", "butter",
            "cream", "sour cream", "ice cream",
            "ghee", "cream cheese", "buttermilk",
            "condensed milk", "evaporated milk",
            "milk powder",
        ], 

        "acidic": [
            "orange", "lemon", "lime", "grapefruit",
            "apple", "passionfruit", "cranberry",
        ],

        "fruit": [
            "banana", "apple", "pear", "mango",
            "strawberry","coconut", "pineapple",
            "kiwi", "blueberry", "raspberry", "blackberry",
            "cherry", "watermelon", "papaya", "peach",
            "plum", "grape", "pomegranate", "fig",
            "date", "dragon fruit", "lychee", "guava",
        ],

        "protein": [
            "beef", "chicken", "turkey", "pork", "lamb",
            "venison", "duck", "salmon", "tuna", "sardine",
            "mackerel", "cod", "shrimp", "crab", "lobster",
            "mussels", "scallops", "clams", "oysters",
            "cockles", "egg", "tofu", "tempeh", "lentils",
            "chickpeas", "black beans", "soybeans", "peanuts",
            "peanut butter", "almonds", "walnuts",
            "pistachios", "cashwes", "pumpkin seeds",
            "chia seeds", "flaxseed", "quinoa", "spirulina",
        ], 

        "starches": [
            "white rice", "brown rice", "basmati rice",
            "jasmine rice","wheat", "bread", "whole-grain bread",
            "pasta", "noodles", "udon", "soba", "rice noodles",
            "vermicelli", "corn", "cornmeal", "tortilla",
            "oats", "barley", "rye", "buckwheat", "millet",
            "sorghum", "potatoes", "sweet potatoes", "yams", 
            "cassava", "tapioca", "cereal", "granola", 
            "crackers", "pretzels", "bagels", "pancakes",
            "waffles", "muffins", "donuts", "croissant",
            "pizza crust",
        ], 

        "fats":[
            "olive oil", "avocado", "coconut oil",
            "canola oil", "peanut oil", "sesame oil",
            "sunflower oil", "lard", "tallow",
            "mayonnaise", "almond butter", "cashew butter",
            "walnut oil", "flaxseed oil",
            "pumpkin seed oil", "macadamia nuts",
            "hazelnuts",

        ],

        "vegetables": [
            "carrot", "broccoli", "cauliflower",
            "spinach", "kale", "tomato", "cucumber",
            "lettuce", "celery", "beetroot", "onion",
            "garlic", "bell pepper","zucchini",
            "eggplant", "pumpkin", "squash", "asparagus",
            "green beans", "peas", "cabbage", "okra",
            "radish", "turnip", "parsnip", 
            "brussels sprouts", "artichoke", "leek",
            "ginger", "turmetic"
        ], 

        "sugar": [
            "honey", "maple syrup", "brown sugar",
            "white sugar", "molasses", "jam",
            "chocolate", "candy",
        ], 

        "fermented foods": [
            "kimchi", "sauerkraut", "miso",
            "kombucha", "kefir", "sourdough",
            "pickles", "fish sauce",
        ], 

        "caffeinated": [
            "energy drink",
            "coffee",
            "tea", 
        ], 

        "alcohol": [
            "beer", 
            "wine",
            "alcohol,"
        ]
    }
    rules = [
        ("dairy", "acidic", "Caution", 
         "This combination can cause dairy to curdle. It is usually not harmful, but some people may find it uncomfortable."
        ), 

        ("alcohol", "caffeinated", "Avoid",
         "Caffein can hide the effects of alcohol and make it easier to drink more intended."),

        ("proteins", "proteins", "Avoid",
         "Different proteins digest at different rates and need") 
    ]
    
    foods = []
    
    for food_group, food_names in FOOD_GROUPS.items():
        for food_name in food_names:
            foods.append((food_name, food_group))


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
