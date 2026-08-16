"""PureBite food-poisoning information and food-combination web application.

Main functions include:
- provide more information about food poisoning.
- introduce a food incompatibility checking tool.
Built with Python and Flask.
"""

import os
import random
import re
import smtplib
import sqlite3
import ssl
from email.message import EmailMessage
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

load_dotenv()
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get(
    "PUREBITE_SECRET_KEY",
    "change-this-before-publishing"
)
DATABASE = Path(__file__).with_name("purebite.db")


def get_db_connection():
    """Connect the database with the python file"""
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_database():
    """Create a data base for the food compatibility checker"""
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
            group_two TEXT NOT NULL,
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
            "apple", "passionfruit", "cranberry", "juice",
        ],

        "fruits": [
            "banana", "apple", "pear", "mango",
            "strawberry","coconut", "pineapple",
            "kiwi", "blueberry", "raspberry", "blackberry",
            "cherry", "watermelon", "papaya", "peach",
            "plum", "grape", "pomegranate", "fig",
            "date", "dragon fruit", "lychee", "guava",
        ],

        "proteins": [
            "beef", "chicken", "turkey", "pork", "lamb",
            "venison", "duck", "salmon", "tuna", "sardine",
            "mackerel", "cod", "shrimp", "crab", "lobster",
            "mussels", "scallops", "clams", "oysters",
            "cockles", "egg", "tofu", "tempeh", "lentils",
            "chickpeas", "black beans", "soybeans", "peanuts",
            "peanut butter", "almonds", "walnuts",
            "pistachios", "cashews", "pumpkin seeds",
            "chia seeds", "flaxseed", "quinoa", "spirulina",
        ],

        "starches": [
            "white rice", "rice", "brown rice", "basmati rice",
            "jasmine rice","wheat", "bread", "whole-grain bread",
            "pasta", "noodles", "udon", "soba", "rice noodles",
            "vermicelli", "corn", "cornmeal", "tortilla",
            "oats", "barley", "rye", "buckwheat", "millet",
            "sorghum", "potato", "sweet potato", "yams",
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
            "ginger", "turmeric"
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
            "energy drink", "coffee", "tea",
        ],

        "alcohol": [
            "beer", "wine", "alcohol",
        ]
    }
    rules = [
        ("dairy", "acidic", "Caution",
         "This combination can cause dairy to curdle."
         "It is usually not harmful, but some people may find it uncomfortable."
        ),

        ("alcohol", "caffeinated", "Avoid",
         "Caffein can hide the effects of alcohol and make it easier to drink more intended."
        ),

        ("proteins", "proteins", "Caution",
         "Different proteins digest at different rates and need varying enzymes."
         "Combining animal proteins may overload the degestive system."
        ),

        ("proteins", "starches", "Caution",
         "They need different environment conditions to digest. "
         "When eaten together, they may cause slow digestion."
         "In one meal, you should eat proteins first so that it can be digested first, "
         "then starches for a better digestion. "
        ),

        ("proteins", "fruits", "Compatible",
         "Human digestive system is fully capable of handling proteins and fruits together."
         "Individuals with sensitive digestion or conditions (IBS) may notice some discomforts."
        ),

        ("proteins", "vegetables", "Compatible",
         "Proteins and non-starchy vegetables are a beneficial combination "
         "because it helps to ensure that the body receives all the essential nutrients for a healthy body."
        ),

        ("proteins", "fats", "Compatible",
         "Combining proteins with fats is beneficial because it creates a balanced meal that supports overaal health."
        ),

        ("proteins", "dairy", "Avoid",
         "There will be too much proteins for stomach to digest. "
         "This can lead to digestive problems such as bloating, indigestion, heartburn, "
         "and even diarrhea, especially in children and people with sensitive digestive systems."
        ),

        ("proteins", "caffeinated", "Compatible",
         "Caffeine doesn't prevent or reduce the protein absorption ability of digestion."
         " However, caffeine will prevent absorbing iron from meat."
        ),

        ("proteins", "alcohol", "Avoid",
         "Alcohol will prevent the protein absorption ability of digestion and the ability of muscle building."
        ),

        ("proteins", "acidic", "Compatible",
         "Vitamin C in acidic fruits increases iron absorption from meats"
         " by chemically transforming iron into a form that is easier to absorb."
        ),

        ("proteins", "fermented foods", "Compatible",
         "Meat is an abundant source of protein but it takes a lot of time and energy "
         "to break complex peptide bonds. Fermented foods contain natural lactic acid "
         "that helps support the acidic environment of the stomach, stimulating digestive enzymes to work better."
        ),

        ("proteins", "sugar", "Caution",
         "It is both the core of muscle recovery and an ageing agent if used incorrectly"
         " due to producing insulin."
        ),

        ("starches", "starches", "Compatible",
        "Grains share the same steady starch digestion so thay can be eaten together."
        ),

        ("starches", "fruits", "Avoid",
         "Starches are digested quicker than fruits. "
         "Combining them may cause bloating and gas."
        ),

        ("starches", "dairy", "Caution",
         "This reduces the speed of starch digestion, helps glucose "
         "enter the blood slowly, maintains stable energy and prolongs"
         " the feeling of fulness. Carbon and insulin are also increased."
        ),

        ("starches", "vegetables", "Compatible",
         "This is a good combination that will reduce the disadvantage "
         "of starch and help you to have long-lasting satiety, effective "
         "weight loss, and a healthy colon."
        ),

        ("starches", "fats", "Caution",
         "This combination creates the most delicious dishes"
         " (chips, butter bread, pizza, cakes) but contains many risks "
         "for weight and metabolism if the source of fat is not controlled."
        ),

        ("starches", "caffeinated", "Compatible",
         "Caffeine slightly increases the metabolic rate and stimulates the"
         " release of energy from glucose. However, consuming too many "
         "fast-digesting carbohydrates (sugar, flour) along with high doses"
         " of caffeine can cause restlessness or rapid heartbeat in sensitive individuals."
        ),

        ("starches", "alcohol", "Avoid",
         "The liver will prioritize metabolizing alcohol first and "
         "temporarily halt the process of burning fat or releasing glycogen. "
         "Carbohydrates consumed at this time are easily stored as excess fat "
         "(especially abdominal and liver fat)."),

        ("starches", "acidic", "Compatible",
         "Modern medicine proves that the stomach has a strong acidic environment, "
         "so it can digest both starch and acidic foods. "
         "Mild acids even reduce the glycemic index of starch."
        ),

        ("starches", "fermented foods", "Compatible",
         "Organic acids in fermented foods slow down gastric emptying, "
         "reducing the glycemic load. Lactic acid bacteria also help "
         "the gut break down complex starch bonds more gently."
        ),

        ("starches", "sugar", "Avoid",
         "Both are metabolized into glucose. Eating them together"
         " creates a huge amount of empty calories, overloading "
         "the pancreas with insulin, leading to fat accumulation, "
         "insulin resistance, and accelerated skin aging."
        ),

        ("fruits", "fruits", "Compatible",
         "Different types of fruits (sour, sweet, melon) can absolutely "
         "be eaten together. The human body has enough multi-functional"
         " enzymes to absorb simple sugars (fructose, glucose) and "
         "vitamins at the same time without causing 'rotting' as"
         " old macrobiotic theories suggest."
        ),

        ("fruits", "vegetables", "Compatible",
         "This is the foundation of juices and salads. Fiber from "
         "vegetables slows down the absorption of fructose from "
         "fruits, helping to safely provide the body with abundant "
         "vitamins and antioxidants."
        ),

        ("fruits", "fats", "Compatible",
         "Many fruits contain fat-soluble vitamins (Vitamins A, E, K) "
         "and antioxidants such as lycopene and beta-carotene. "
         "When eaten with good fats (such as avocado, nuts, olive oil in salads),"
         " the absorption rate of these vitamins increases 3-5 times."
        ),

        ("fruits", "dairy", "Compatible",
         "Dairy provides protein and calcium, while fruit provides vitamin C and fiber."
         " Vitamin C enhances the absorption of certain minerals in milk,"
         " and the matrix structure of milk slows the absorption of sugar from fruit."
        ),

        ("fruits", "caffeinated", "Compatible",
         "There is no negative chemical reaction between these two groups."
         " Antioxidants in fruit combine with antioxidants in coffee/tea"
         " to protect cells from oxidative stress."),

        ("fruits", "alcohol", "Caution",
         "Fructose in fruit can slightly increase the liver's rate"
         " of alcohol metabolism, but drinking alcohol with large "
         "amounts of sweet fruit will cause a surge in calories"
         " and sugar, putting a great strain on the liver and"
         " easily leading to weight gain."),

        ("fruits", "acidic", "Compatible",
         "Many fruits themselves contain natural acids."
         " Eating them together doesn't harm a healthy stomach. "
         "However, if you have gastroesophageal reflux disease"
         " (GERD) or ulcers, consuming too much acid at once"
         " can irritate the lining."),

        ("fruits", "fermented foods", "Compatible",
         "Soluble fiber in fruits (like pectin) acts as a prebiotic"
         " (food for beneficial bacteria). When combined with "
         "probiotic bacteria in fermented foods, they help the gut microbiome thrive."),

        ("fruits", "sugar", "Avoid",
         "Fruits already contain natural sugar. Adding granulated sugar "
         "or syrup to fruits negates the health benefits, causes blood "
         "sugar spikes, and contributes to tooth decay."),

        ("vegetables", "vegetables", "Compatible",
         "Eating a variety of vegetables (in many different colors)"
         " helps the body receive a full range of vitamins, minerals,"
         " and diverse phytochemicals to fight disease."),

        ("vegetables", "dairy", "Compatible",
         "Fats in dairy products (like cheese, butter) "
         "help dissolve and absorb fat-soluble vitamins (A, D, E, K)"
         " which are abundant in leafy green vegetables."),

        ("vegetables", "caffeinated", "Caution",
         "There are no adverse interactions, except for one note:"
         " Tannins and caffeine in tea/coffee may reduce the "
         "absorption of non-heme iron (plant-based iron) "
         "found in vegetables like spinach and kale if "
         "consumed too close together."),

        ("vegetables", "alcohol", "Compatible",
         "Vegetables are rich in fiber and water, "
         "which slows the rate of alcohol absorption into the "
         "bloodstream, helping to protect the stomach lining "
         "and reduce the acute effects of alcohol intoxication."),

        ("vegetables", "acidic", "Compatible",
         "Squeezing lemon or adding vinegar to vegetables (salad) "
         "not only enhances the flavor, but the mild acidity also "
         "helps convert iron from plants into a more easily absorbed "
         "form for the body."),

        ("vegetables", "fermented foods", "Compatible",
         "The fiber in vegetables is an excellent source of"
         " nourishment for the beneficial bacteria found in "
         "fermented foods, helping to optimize the digestive system."),

        ("vegetables", "sugar", "Caution",
         "Adding too much sugar to vegetables during preparation "
         "reduces their natural nutritional value and increases "
         "unnecessary calories."),

        ("vegetables", "fats", "Compatible",
         "Healthy fats are essential solvents for the body "
         "to absorb powerful antioxidants."),

        ("fats", "fats", "Caution",
         "Combining different sources of fat is normal. "
         "However, it is advisable to prioritize combining"
         " unsaturated fats (olive oil, avocado) and limit"
         " the combination of too much saturated animal fat "
         "or trans fat due to cardiovascular risk."),

        ("fats", "dairy", "Caution",
         "Dairy products already contain fat. "
         "Adding more fat doesn't harm digestion, but it "
         "rapidly increases the calorie density of the dish, "
         "easily leading to weight gain."),

        ("fats", "caffeinated", "Compatible",
         "This is the basis of the popular 'bulletproof coffee'"
         " (coffee mixed with butter/coconut oil) in the Keto diet."
         " Fat slows the absorption of caffeine, allowing "
         "the energy from caffeine to be released more steadily "
         "and for a longer period, without sudden energy drops."),

        ("fats", "alcohol", "Avoid",
         "When alcohol is present, the liver stops burning fat "
         "to focus on alcohol detoxification. Eating greasy foods "
         "while drinking alcohol will cause all that fat to accumulate, "
         "increasing the risk of fatty liver disease and acute pancreatitis."),

        ("fats", "acidic", "Compatible",
         "This is the structure of classic dipping sauces. "
         "Acidity helps to break down and emulsify fat molecules, "
         "making it easier for lipase enzymes in the small intestine"
         " to break down and digest fat, reducing the feeling of satiety."),

        ("fats", "fermented foods", "Compatible",
         "Organic acids and probiotics in fermented foods "
         "help the digestive system process high-fat meals "
         "more gently, reducing bloating."),

        ("fats", "sugar", "Avoid",
         "The most dangerous combination for metabolism. "
         "Sugar causes a spike in insulin, and insulin will"
         " order the body to store all the accompanying "
         "fat in adipose tissue immediately, while also"
         " causing systemic inflammation."),

        ("dairy", "dairy", "Compatible",
         "Combining dairy products is perfectly safe"
         " because they share the same protein structure "
         "(casein/whey) and lactose, and the body digests"
         " them using the same enzyme system."),

        ("dairy", "caffeinated", "Compatible",
         "This combination is extremely popular."
         " A small note: tannins in tea/coffee may bind "
         "to a small amount of calcium in milk, reducing absorption,"
         " but this is negligible for people with a balanced diet."),

        ("dairy", "alcohol", "Caution",
         "They are ingredients in some cocktails. The fat and protein"
         " in milk create a protective layer on the stomach lining, "
         "slowing down the absorption of alcohol. However, high"
         " concentrations of alcohol can coagulate the proteins "
         "in milk, which can cause bloating in some people with"
         " sensitive stomachs."),

        ("dairy", "sugar", "Caution",
         "Dairy contains naturally occurring lactose. Adding too much "
         "refined sugar increases the glycemic load and empty calories, "
         "easily leading to weight gain and increased risk of "
         "insulin resistance."),

        ("dairy", "fermented foods", "Compatible",
         "Combining these helps supplement a diverse range"
         " of beneficial bacteria strains in the gut and "
         "increases the bioavailability of minerals."),

        ("caffeinated", "caffeinated", "Caution",
         "Consuming caffeine from multiple sources at the same time"
         " adds up the caffeine content. If exceeding 400mg/day, "
         "it will overstimulate the central nervous system,"
         " causing rapid heartbeat, anxiety, insomnia, and"
         " increased blood pressure."),

        ("caffeinated", "fermented foods", "Compatible",
         "No negative chemical interactions have been observed"
         " between these two groups. The acids in coffee/tea"
         " and the organic acids in fermented foods do not "
         "negatively affect each other in the digestive system "
         "of a healthy person."),

        ("caffeinated", "sugar", "Caution",
         "Caffeine provides a temporary boost of energy, "
         "while sugar causes a rapid increase in blood sugar. "
         "When this sugar level drops, you will feel tired,"
         " lethargic, and crave more food."),

        ("alcohol", "alcohol", "Avoid",
         "Mixing different types of alcoholic beverages doesn't"
         " cause immediate alcohol poisoning, but it makes it"
         " difficult to control your alcohol intake, increases"
         " the risk of overdrinking, and exacerbates hangover "
         "symptoms due to the different congeners in each mixed "
         "type of alcohol."),

        ("alcohol", "fermented foods", "Caution",
         "Both fermented foods and some types of alcohol contain "
         "high levels of biogenic amines. In sensitive individuals"
         " or those lacking the enzyme that breaks down histamine,"
         " this combination can trigger allergic reactions,"
         " facial flushing, headaches, or increased blood pressure."),

        ("alcohol", "sugar", "Avoid",
         "The sweetness of sugar masks the harshness of alcohol,"
         " causing you to drink more without realizing it. "
         "Sugar and alcohol simultaneously put immense metabolic"
         " pressure on the liver, accelerating the formation of "
         "fatty liver disease."),

        ("fermented foods", "fermented foods", "Compatible",
        "Combining different fermented foods helps diversify"
        " the beneficial bacteria strains (Lactobacillus, Bifidobacterium,"
        " beneficial yeasts) in the gut, making the"
        " microbiome richer and healthier."),

        ("fermented foods", "sugar", "Caution",
         "During processing (such as pickling, making kombucha), "
         "sugar is food for beneficial bacteria to ferment into "
         "organic acids (very good). However, if too much sugar "
         "is added to already fermented food for direct consumption,"
         " this excess sugar can feed harmful bacteria or"
         " negative yeasts (such as Candida) in the gut."),

        ("sugar", "sugar", "Avoid",
         "Combining different types of refined sugars"
         " simply increases the concentration of empty "
         "calories consumed, overloading the pancreas "
         "and liver, leading to obesity and type 2 diabetes."),
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


def find_food(food_name):
    """Search for the food names in the database."""
    connection = get_db_connection()
    food = connection.execute(
        "SELECT * FROM foods WHERE name = ?",
        (food_name.strip(),)
    ).fetchone()
    connection.close()
    return food


def check_combination(first_food, second_food):
    """Compare the foods with the rules in the database."""

    if re.search(r'[^a-zA-Z\s\-]',
                 first_food) or re.search(r'[^a-zA-Z\s\-]',
                                          second_food):
        return {
            "status": "Invalid",
            "message": "Food names should not contain numbers or"
            " special characters. Please enter valid food names."
        }

    first = find_food(first_food)
    second = find_food(second_food)

    if first is None or second is None:
        missing_foods = []
        if first is None:
            missing_foods.append(first_food.title())
            record_missing_food(first_food)

        if second is None:
            missing_foods.append(second_food.title())
            record_missing_food(second_food)

        return {
            "status": "Unknown food",
            "message": (
                f"{','.join(missing_foods)} is not in the PureBite database yet. "
                "We have collected this information. Please try another food."
            )
        }
    if first_food == second_food:
        return {
            "status": "Same food",
            "message": "They are the same ingredent so they are good to combine. Remember just don't eat too much of them."
        }

    connection = get_db_connection()

    rule = connection.execute("""
        SELECT * FROM combination_rules
        WHERE (group_one = ? AND group_two = ?)
        OR (group_one = ? AND group_two = ?)
    """, (
        first["food_group"],
        second["food_group"],
        second["food_group"],
        first["food_group"]
    )).fetchone()

    connection.close()

    if rule:
        return {
            "status": rule["result"],
            "message": rule["message"]
        }

    return {
        "status": "No special rule.",
        "message": (f"We have collected this information. Please try a new combination.")
    }


def choose_result_image(status):
    """Choose one random image to show the result."""

    if status in ("Unknown food", "No special rule."):
        return "result_image/unknown_food.jpeg"

    if status == "Same food":
        return "result_image/same.jpeg"

    if status == "Invalid":
        return "result_image/invalid.jpeg"

    image_folders = {
        "Compatible": "result_image/compatible",
        "Caution": "result_image/caution",
        "Avoid": "result_image/avoid",
    }

    folder_name = image_folders.get(status)
    if folder_name is None:
        return "default.png"

    image_folder = Path(app.static_folder) / folder_name
    allowed_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    images = [
        image for image in image_folder.iterdir()
        if image.suffix.lower() in allowed_extensions
    ]

    if not images:
        return "default.png"

    chosen_image = random.choice(images)
    return f"{folder_name}/{chosen_image.name}"


def record_missing_food(food_name):
    """Record the food name that is not in the database."""

    if re.search(r'[^a-zA-Z\s\-]', food_name):
        return

    file_path = "missing_food.txt"
    food_clean = food_name.strip().lower()

    if not food_clean:
        return

    existing_foods = []

    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                existing_foods = [line.strip().lower() for line in file]
        except Exception as e:
            print("Error reading missing_food.txt:", e)

    if food_clean not in existing_foods:
        try:
            with open(file_path, "a") as file:
                file.write(food_name.strip().title() + "\n")
            print(f"Recorded missing food: {food_name}")
        except Exception as e:
            print(f"Recorded")


def is_real_email(email_address):
    """Check whether the email addrees is valid or not."""

    api_key = os.environ.get("ABSTRACT_API_KEY")

    if not api_key or not email_address:
        return True

    url= f"https://emailreputation.abstractapi.com/v1/?api_key={api_key}&email={email_address}"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()

            email_status = data.get("email_deliverability", {}).get("status") or data.get("deliverability")
            return str(email_status).upper() == "DELIVERABLE"
        return True
    except Exception as e:
        print("API Error:", e)
        return True

@app.route('/')
def home():
    """Return home."""

    return render_template('home.html')


@app.route('/overall')
def overall():
    """Return overall page."""
    return render_template('overall.html')


@app.route('/transmission')
def transmission():
    """Return transmission page."""

    return render_template('transmission.html')


@app.route('/prevention')
def prevention():
    """Return prevention page."""

    return render_template('prevention.html')


@app.route('/checker', methods=['GET', 'POST'])
def checker():
    """Return the checker page."""

    result = None
    first_food = ''
    second_food = ''

    if request.method == 'POST':
        first_food = request.form.get('stfoodname', '').strip()
        second_food = request.form.get('ndfoodname', '').strip()
        print(first_food, second_food)
    if first_food and second_food:
        result = check_combination(first_food, second_food)
        result["image"] = choose_result_image(result["status"])
    return render_template('checker.html',
                           result= result,
                           first_food= first_food,
                           second_food= second_food)


@app.route("/api/check", methods=["POST"])
def api_check():
    """API checking the email validity."""

    data = request.get_json(silent=True) or {}
    first_food = data.get("firstFood")
    second_food = data.get("secondFood", "").strip()

    if not first_food or not second_food:
        return jsonify({"error": "Please provide both firstFood and secondFood"}), 400

    result = check_combination(first_food, second_food)
    result["image"] = choose_result_image(result["status"])
    return jsonify(result)


@app.route("/contact", methods=["POST"])
def contact():
    """The contact footer."""

    customer_name = request.form.get("customer_name", "").strip()
    customer_email = request.form.get("customer_email", "") or request.form.get("email", "").strip()
    customer_message = request.form.get("customer_message", "").strip()

    if not customer_name.replace(" ", "").isalpha():
        flash("Please check the typos in Customer name", "error")
        return redirect(request.referrer or url_for("home"))

    if not customer_name or not customer_email or not customer_message:
        flash("Please complete every contact field.", "error")
        return redirect(request.referrer or url_for("home"))

    if not is_real_email(customer_email):
        flash("The email address you entered does not exist or cannot receive mail. Please check for typos!",
               "error")
        return redirect(request.referrer or url_for('contact'))

    sender_email = os.environ.get("PUREBITE_SENDER_EMAIL")
    sender_password = os.environ.get("PUREBITE_SMTP_PASSWORD")
    receiver_email = os.environ.get("PUREBITE_RECEIVER_EMAIL")

    if not sender_email or not sender_password or not receiver_email:
        flash("The contact email settings have not been configured yet.", "error")
        return redirect(request.referrer or url_for("home"))

    email = EmailMessage()
    email["Subject"] = f"PureBite contact message from {customer_name}"
    email["From"] = sender_email
    email["To"] = receiver_email
    email["Reply-To"] = customer_email

    email.set_content(
        f"Name: {customer_name}\n"
        f"Email: {customer_email}\n\n"
        f"Message:\n{customer_message}"
    )

    try:
        smtp_host = os.environ.get("PUREBITE_SMTP_HOST")
        smtp_port = int(os.environ.get("PUREBITE_SMTP_PORT", "587"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(sender_email, sender_password)
            server.send_message(email)

        flash("Thank you! Your message has been sent.", "success")

    except (OSError, smtplib.SMTPException):
        flash("Sorry, your message could not be sent. Please try again later.", "error")

    return redirect(request.referrer or url_for("home"))


@app.route('/copyright')
def copyright():
    """Copyright page."""

    return render_template('copyright.html')


@app.route('/privacy')
def privacy():
    """Privacy page."""

    return render_template('privacy.html')


@app.route('/disclaimer')
def disclaimer():
    """disclaimer page."""
    return render_template('disclaimer.html')

if __name__ == '__main__':
    create_database()
    app.run(host='0.0.0.0', port=5000, debug=True)
