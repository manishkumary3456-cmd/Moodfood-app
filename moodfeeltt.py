# foodfeel.py
# MoodFood Pro — Full Streamlit app with separate signup page

import streamlit as st
import sqlite3, os, json, random, hashlib, urllib.parse, requests
from datetime import datetime, timedelta, date
from collections import Counter
import time
from functools import lru_cache

# Try to import optional dependencies
try:
    from requests_oauthlib import OAuth2Session
    OAUTH_AVAILABLE = True
except ImportError:
    OAUTH_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from twilio.rest import Client
    import schedule
    import threading
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# -----------------------
# Config & secrets
# -----------------------
st.set_page_config(page_title="MoodFood Pro", page_icon="🍽️", layout="wide")

# Read secrets (preferred) or fallback to env
GOOGLE_CLIENT_ID = st.secrets.get("google_client_id", os.environ.get("GOOGLE_CLIENT_ID", ""))
GOOGLE_CLIENT_SECRET = st.secrets.get("google_client_secret", os.environ.get("GOOGLE_CLIENT_SECRET", ""))
BASE_URL = st.secrets.get("base_url", os.environ.get("BASE_URL", "http://localhost:8501"))

EDAMAM_APP_ID = st.secrets.get("edamam_app_id", os.environ.get("EDAMAM_APP_ID", ""))
EDAMAM_APP_KEY = st.secrets.get("edamam_app_key", os.environ.get("EDAMAM_APP_KEY", ""))

USDA_API_KEY = st.secrets.get("usda_api_key", os.environ.get("USDA_API_KEY", ""))
GEMINI_API_KEY = st.secrets.get("gemini_api_key", os.environ.get("GEMINI_API_KEY", ""))

ADMIN_USER = st.secrets.get("admin_user", os.environ.get("ADMIN_USER", "admin"))
ADMIN_PW = st.secrets.get("admin_password", os.environ.get("ADMIN_PASSWORD", "adminpass"))

# ==== NEW: Twilio secrets ====
TWILIO_SID = st.secrets.get("twilio_sid", os.environ.get("TWILIO_SID", ""))
TWILIO_AUTH_TOKEN = st.secrets.get("twilio_auth_token", os.environ.get("TWILIO_AUTH_TOKEN", ""))
TWILIO_SMS_FROM = st.secrets.get("twilio_sms_from", os.environ.get("TWILIO_SMS_FROM", ""))
TWILIO_WA_FROM = st.secrets.get("twilio_whatsapp_from", os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886"))

# OAuth endpoints
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO = "https://www.googleapis.com/oauth2/v1/userinfo"

# -----------------------
# DB init
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "moodfood_final.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "community"), exist_ok=True)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password TEXT,
                    email TEXT,
                    provider TEXT,
                    is_admin INTEGER DEFAULT 0,
                    phone TEXT,
                    sms_enabled INTEGER DEFAULT 0,
                    wa_enabled INTEGER DEFAULT 0,
                    reminder_time TEXT DEFAULT '09:00'
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS moods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    date TEXT,
                    mood TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    date TEXT,
                    mood TEXT,
                    suggestions TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    date TEXT,
                    caption TEXT,
                    photo TEXT,
                    likes INTEGER DEFAULT 0
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS mood_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mood TEXT,
                    name TEXT
                )""")
    # notification sent log (avoid duplicate per day)
    cur.execute("""CREATE TABLE IF NOT EXISTS notif_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    sent_date TEXT
                )""")
    conn.commit()
    return conn, cur

conn, cur = init_db()

# create admin user if not exists (from secrets)
try:
    cur.execute("SELECT username FROM users WHERE username=?", (ADMIN_USER,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (username,password,email,provider,is_admin) VALUES (?, ?, ?, ?, ?)",
                    (ADMIN_USER, hash_pw(ADMIN_PW), "", "local", 1))
        conn.commit()
except Exception as e:
    st.error(f"Error creating admin user: {e}")
# -----------------------
# Mood-wise Big Pools (70–100+ each) + DB seed
# -----------------------

import itertools

def _expand(base_items, style_suffixes=None, style_prefixes=None, extras=None, max_count=120):
    """Helper: expand a seed list into many variants and cap length."""
    style_suffixes = style_suffixes or []
    style_prefixes = style_prefixes or []
    extras = extras or []
    out = []

    # raw base
    out.extend(base_items)

    # prefix + base
    for p, x in itertools.product(style_prefixes, base_items):
        out.append(f"{p} {x}")

    # base + suffix
    for x, s in itertools.product(base_items, style_suffixes):
        out.append(f"{x} {s}")

    # extras as-is
    out.extend(extras)

    # unique while preserving order
    seen = set()
    deduped = []
    for it in out:
        k = it.strip().lower()
        if not k or k in seen:
            continue
        seen.add(k)
        deduped.append(it.strip())

    return deduped[:max_count]


def build_mood_food_keywords():
    """Return dict: mood -> 100-ish items each (>=70)."""
    # Common building blocks
    SUFFIXES_LIGHT = ["Salad", "Bowl", "Wrap", "Soup", "Sandwich", "Toast", "Smoothie", "Parfait"]
    SUFFIXES_HEARTY = ["Bowl", "Platter", "Wrap", "Burger", "Pizza", "Pasta", "Grill", "Curry"]
    PREFIXES_HEALTH = ["Whole-Wheat", "Multigrain", "High-Protein", "Low-Sugar", "Fiber-Rich", "Herbed", "Garlic"]
    PREFIXES_FUN = ["Cheesy", "Spicy", "Zesty", "Crispy", "Loaded", "Smoky", "Tangy", "Masala"]
    PREFIXES_SOOTHING = ["Warm", "Mild", "Gentle", "Light", "Herbal", "Calming"]
    FRUITY = ["Mango", "Berry", "Banana", "Apple", "Pineapple", "Kiwi", "Pomegranate", "Grapes"]
    PROTEINS = ["Paneer", "Tofu", "Egg", "Chicken", "Fish", "Salmon", "Tuna", "Chickpea", "Rajma", "Chole", "Lentil"]
    INDIAN_COMFORT = ["Khichdi", "Dal Rice", "Curd Rice", "Lemon Rice", "Veg Pulao", "Upma", "Poha", "Paratha", "Thepla"]
    STREET_FOOD = ["Pani Puri", "Bhel Puri", "Sev Puri", "Vada Pav", "Samosa", "Kathi Roll", "Frankie", "Chowmein", "Manchurian"]
    SWEETS = ["Gulab Jamun", "Rasgulla", "Kheer", "Rabri", "Jalebi", "Brownie", "Cupcake", "Donut", "Cheesecake", "Ice Cream"]
    GLOBAL = ["Tacos", "Nachos", "Quesadilla", "Burrito", "Hummus", "Falafel", "Shawarma", "Sushi", "Ramen", "Bibimbap"]
    GREENS = ["Leafy Greens", "Spinach", "Kale", "Broccoli", "Lettuce", "Cucumber", "Carrot", "Beet", "Zucchini"]
    GRAINS = ["Oats", "Quinoa", "Brown Rice", "Millet", "Barley", "Buckwheat"]
    NUTS = ["Almonds", "Walnuts", "Pistachios", "Cashews", "Peanuts", "Mixed Nuts", "Peanut Butter", "Almond Butter"]
    DRINKS = ["Green Tea", "Herbal Tea", "Buttermilk", "Lassi", "Warm Milk", "Turmeric Latte", "Coconut Water"]

    # Per-mood seeds
    HAPPY_SEED = [
        "Margherita Pizza","Veggie Pizza","Paneer Tikka Pizza","Garlic Bread","Pasta Arrabbiata","Pasta Alfredo",
        "Chocolate Brownie","Fruit Salad","Tiramisu","Burrito Bowl (veg)","Veg Quesadilla","Cheese Nachos","Hakka Noodles",
        "Veg Burger","Peri-Peri Fries","Street Sandwich","Chole Bhature","Butter Paneer","Dal Makhani","Veg Biryani",
        "Sushi (veg)","Ramen (veg)","Falafel Wrap","Hummus Platter","Tacos (veg)","Loaded Nachos","Paneer Wrap",
        "Veggie Shawarma","Cheesy Corn Toast","Chili Garlic Noodles","Pav Bhaji","Paneer Frankie","Veg Kathi Roll",
        "Manchurian Gravy","Veg Momos","Spring Rolls","Schezwan Noodles","Veg Handi","Stuffed Paratha","Curd Rice"
    ]

    SAD_SEED = [
        "Tomato Soup","Sweet Corn Soup","Khichdi","Dal Rice","Curd Rice","Lemon Rice","Veg Pulao","Poha","Upma",
        "Veg Stew","Light Veg Soup","Mashed Potatoes","Grilled Cheese Sandwich","Oats Porridge","Rava Sheera",
        "Sabudana Khichdi","Moong Dal Khichdi","Dalia Porridge","Vegetable Daliya","Steamed Idli","Soft Dosa",
        "Veg Uttapam","Broth Bowl","Chicken Soup","Egg Drop Soup","Soft Paneer Bhurji","Sooji Upma","Lentil Soup",
        "Plain Paratha with Curd","Soft Thepla with Curd","Besan Chilla","Carrot Soup","Pumpkin Soup","Spinach Soup"
    ]

    STRESSED_SEED = [
        "Green Tea","Herbal Tea","Chamomile Tea","Ginger Tea","Lemon Honey Water","Cucumber Salad","Greek Yogurt",
        "Yogurt Parfait","Mixed Nuts","Dark Chocolate","Avocado Toast","Oats with Fruit","Banana Smoothie",
        "Berry Smoothie","Protein Smoothie (veg)","Sprouts Salad","Quinoa Salad","Hummus with Veg Sticks",
        "Fruit Bowl","Veg Clear Soup","Miso Soup (veg)","Warm Milk","Turmeric Latte","Coconut Water",
        "Roasted Chickpeas","Baked Sweet Potato","Apple with Peanut Butter","Trail Mix","Whole-Wheat Crackers",
        "Chia Pudding","Overnight Oats","Granola Yogurt"
    ]

    TIRED_SEED = [
        "Banana Smoothie","Peanut Butter Toast","Granola Yogurt","Protein Shake","Oats Banana Bowl",
        "Paneer Sandwich","Egg Sandwich","Paneer Wrap","Tofu Stir-Fry","Chicken Salad","Tuna Sandwich",
        "Salmon Bowl","Rajma Chawal","Chole Chawal","Sprouts Chaat","Boiled Eggs","Paneer Bhurji",
        "Paneer Tikka Wrap","Hummus Wrap","Veggie Omelette","Besan Chilla","Paneer Paratha","Tofu Scramble",
        "Quinoa Bowl","Peanut Chaat","Dahi Poha","Cottage Cheese Salad","Fruit + Nuts Bowl","Millet Khichdi"
    ]

    EXCITED_SEED = [
        "Pani Puri","Bhel Puri","Sev Puri","Vada Pav","Samosa","Kathi Roll","Frankie","Tacos","Nachos","Quesadilla",
        "Schezwan Noodles","Manchurian","Chili Paneer","Peri-Peri Fries","Popcorn","Corn Chaat","Momos","Spring Rolls",
        "Pizza Slice","Veg Hot Dog","Cheesy Sandwich","Loaded Fries","Tandoori Paneer Tikka","Hakka Noodles",
        "Veggie Burrito","Sushi (veg)","Korean Bibimbap (veg)","Paneer Shawarma","Cheesy Garlic Bread"
    ]

    BORED_SEED = [
        "Street Sandwich","French Fries","Donuts","Cupcake","Cookies","Brownie","Ice Cream Sundae","Fruit Cream",
        "Milkshake","Cold Coffee","Candy Popcorn","Nachos with Salsa","Chocolate Muffin","Cheese Balls","Corn Cheese Balls",
        "Paneer Pops","Potato Smiles","Garlic Bread Sticks","Mini Pizza","Pita Chips with Hummus","Veg Nuggets",
        "Waffles","Pancakes","Churros","Pretzels","Apple Pie","Chocolate Fudge","Trail Mix Sweet","Caramel Popcorn"
    ]

    ANXIOUS_SEED = [
        "Cucumber Salad","Herbal Tea","Warm Soup","Fruit Bowl","Yogurt","Banana with Peanut Butter","Oatmeal",
        "Khichdi (light)","Veg Clear Soup","Steamed Veggies","Buttermilk","Coconut Water","Roasted Foxnuts (Makhana)",
        "Chia Pudding","Smoothie (low sugar)","Rice + Dal (light)","Steamed Idli","Plain Dosa","Sprouts Salad (mild)",
        "Sabudana Khichdi (light)","Honey Lemon Water","Apple Slices","Boiled Potatoes (light masala)","Porridge (mild)"
    ]

    RELAXED_SEED = [
        "Garden Salad","Spinach Salad","Kale Salad","Quinoa Salad","Veg Buddha Bowl","Steamed Idli","Buttermilk",
        "Fruit Smoothie","Light Veg Soup","Veggie Wrap (light)","Grilled Paneer Salad","Tofu Salad","Sprouts Bowl",
        "Stir-Fried Veggies (light oil)","Lentil Soup (light)","Veg Clear Soup","Cucumber Raita","Hummus with Veggies",
        "Avocado Salad","Tomato Basil Soup","Minestrone (veg)","Zucchini Noodles (veg)","Broccoli Stir-Fry (light)",
        "Brown Rice Bowl (veg)"
    ]

    PREG_SEED = [
        "Milk","Warm Milk","Yogurt","Buttermilk","Paneer","Tofu","Boiled Eggs","Lentils","Chickpeas","Rajma",
        "Mixed Beans Salad","Leafy Greens","Spinach Dal","Dal Khichdi","Vegetable Khichdi","Vegetable Pulao (low oil)",
        "Whole-Wheat Roti + Dal","Quinoa Khichdi","Veggie Omelette","Dry Fruits Mix","Almonds","Walnuts","Dates",
        "Fresh Fruit Bowl","Banana Shake (low sugar)","Veggie Poha","Upma with Veggies","Thepla + Curd",
        "Paneer Paratha (light)","Moong Dal Chilla","Besan Chilla","Sprouts Chaat (light)","Carrot Halwa (low sugar)",
        "Coconut Water","Lassi (low sugar)","Ragi Malt","Jaggery Peanut Chikki","Sesame Ladoo (til)","Oats Porridge",
        "Methi Thepla (light)","Beetroot Salad","Broccoli Soup","Tomato Soup","Chicken Soup (if non-veg)","Fish Curry (light)",
        "Egg Curry (light)","Vegetable Daliya","Vegetable Handvo (light oil)"
    ]

    # Build large lists with expansions
    MOOD_MAP = {
        "Happy": _expand(HAPPY_SEED, SUFFIXES_HEARTY, PREFIXES_FUN, SWEETS + GLOBAL + STREET_FOOD, max_count=120),
        "Sad": _expand(SAD_SEED, SUFFIXES_LIGHT, PREFIXES_SOOTHING, INDIAN_COMFORT + ["Rice Bowl","Curd Bowl"], max_count=110),
        "Stressed": _expand(STRESSED_SEED, SUFFIXES_LIGHT, PREFIXES_SOOTHING, DRINKS + NUTS + ["Oat Cookies (low sugar)"], max_count=110),
        "Tired": _expand(TIRED_SEED, SUFFIXES_HEARTY, PREFIXES_HEALTH, PROTEINS + GRAINS + ["Energy Bar (clean)"], max_count=115),
        "Excited": _expand(EXCITED_SEED, SUFFIXES_HEARTY, PREFIXES_FUN, STREET_FOOD + GLOBAL + ["Salsa & Chips"], max_count=115),
        "Bored": _expand(BORED_SEED, ["Bites","Pops","Sticks","Cups"], ["Cheesy","Crunchy","Sweet"], SWEETS + ["Fruit Skewers"], max_count=110),
        "Anxious": _expand(ANXIOUS_SEED, SUFFIXES_LIGHT, PREFIXES_SOOTHING, DRINKS + ["Light Khichdi Bowl","Soft Chapati + Dal"], max_count=105),
        "Relaxed": _expand(RELAXED_SEED, SUFFIXES_LIGHT, ["Herbed","Light"], GREENS + GRAINS + ["Herb Rice Bowl"], max_count=105),
        "Pregnancy": _expand(PREG_SEED, SUFFIXES_LIGHT, PREFIXES_HEALTH, GREENS + GRAINS + NUTS + ["Folate-Rich Salad","Calcium Smoothie"], max_count=120),
    }
    # Ensure each mood has at least 70; if not, pad with sensible combos
    for mood, items in MOOD_MAP.items():
        if len(items) < 70:
            # pad using fruits + suffixes
            pad = []
            for f, s in itertools.product(FRUITY, ["Smoothie","Bowl","Parfait"]):
                pad.append(f"{f} {s}")
            need = 70 - len(items)
            for it in pad:
                if it.lower() not in {x.lower() for x in items}:
                    items.append(it)
                    if len(items) >= 70:
                        break
            MOOD_MAP[mood] = items[:120]

    # Cap to ~100 for DEFAULT pools later
    return {mood: items[:100] for mood, items in MOOD_MAP.items()}


# Build mega list
MOOD_FOOD_KEYWORDS = build_mood_food_keywords()

# Keep the same interface used elsewhere in your app:
DEFAULT_POOLS = {m: lst for m, lst in MOOD_FOOD_KEYWORDS.items()}

# ---- Seed DB if empty (unchanged semantics) ----
cur.execute("SELECT COUNT(*) FROM mood_items")
if cur.fetchone()[0] == 0:
    for mood, items in DEFAULT_POOLS.items():
        for it in items:
            cur.execute("INSERT INTO mood_items (mood,name) VALUES (?, ?)", (mood, it))
    conn.commit()

def get_pool_from_db(mood):
    cur.execute("SELECT name FROM mood_items WHERE mood=? ORDER BY id ASC", (mood,))
    return [r[0] for r in cur.fetchall()]


# -----------------------
# Nutrition: Edamam -> USDA -> fallback (mood-aware)
# -----------------------

def get_nutrition_edamam(qname: str):
    if not EDAMAM_APP_ID or not EDAMAM_APP_KEY:
        return None, "Edamam keys not set"
    try:
        q = urllib.parse.quote_plus(qname)
        url = f"https://api.edamam.com/api/nutrition-data?app_id={EDAMAM_APP_ID}&app_key={EDAMAM_APP_KEY}&ingr={q}"
        r = requests.get(url, timeout=8)
        if r.status_code != 200:
            return None, f"Edamam HTTP {r.status_code}"
        data = r.json()
        calories = int(data.get("calories", 0))
        nutrients = data.get("totalNutrients", {})
        protein = round(nutrients.get("PROCNT", {}).get("quantity", 0), 1)
        vitamins = []
        for k, v in nutrients.items():
            if k.startswith("VIT"):
                vitamins.append(v.get("label"))
        vitamins_str = ", ".join(vitamins) if vitamins else "Various"
        return {"calories": calories, "protein_g": protein, "vitamins": vitamins_str, "source": "edamam"}, None
    except Exception as e:
        return None, f"Edamam error: {e}"


def get_nutrition_usda(qname: str):
    if not USDA_API_KEY:
        return None, "USDA key not set"
    try:
        url = "https://api.nal.usda.gov/fdc/v1/foods/search"
        payload = {"query": qname, "pageSize": 1}
        params = {"api_key": USDA_API_KEY}
        r = requests.post(url, params=params, json=payload, timeout=10)
        if r.status_code != 200:
            return None, f"USDA HTTP {r.status_code}"
        data = r.json()
        foods = data.get("foods", []) or data.get("foodSearchCriteria", [])
        if not foods:
            return None, "USDA: no results"
        f0 = foods[0]
        nutrients = f0.get("foodNutrients", [])
        calories = None; protein = 0.0; vitamins = []
        for n in nutrients:
            name = n.get("nutrientName","{}").lower()
            qty = n.get("value", 0)
            if "energy" in name or "calorie" in name:
                try:
                    calories = int(qty)
                except Exception:
                    calories = 0
            if "protein" in name:
                protein = round(qty,1)
            if any(v in name for v in ["vitamin", "vit a", "vit c", "vit d", "vit b", "folate", "iron", "calcium"]):
                vitamins.append(n.get("nutrientName"))
        calories = calories if calories is not None else 0
        vitamins_str = ", ".join(vitamins) if vitamins else "Various"
        return {"calories": calories, "protein_g": protein, "vitamins": vitamins_str, "source": "usda"}, None
    except Exception as e:
        return None, f"USDA error: {e}"


# Reverse index: food(lower) -> mood
_ITEM_TO_MOOD = {}
for mood, items in MOOD_FOOD_KEYWORDS.items():
    for it in items:
        _ITEM_TO_MOOD[it.lower()] = mood

def _guess_mood_from_name(name: str):
    """Fallback to guess mood by keyword if item not in our map."""
    n = name.lower()
    # quick keyword rules
    if any(k in n for k in ["pani puri","sev puri","nachos","taco","fries","frankie","roll","momo","momos","manchurian","schezwan"]):
        return "Excited"
    if any(k in n for k in ["khichdi","dal rice","porridge","curd","oats","soup","stew","idli","uttapam","poha","upma"]):
        return "Sad"
    if any(k in n for k in ["green tea","herbal","chamomile","cucumber","yogurt","parfait","sprout","chia","coconut water","turmeric"]):
        return "Stressed"
    if any(k in n for k in ["smoothie","peanut","protein","paneer","tofu","egg","chicken","tuna","salmon","sprouts","quinoa"]):
        return "Tired"
    if any(k in n for k in ["brownie","donut","cupcake","cheesecake","pizza","burger","biryani","pav bhaji","shawarma"]):
        return "Happy"
    if any(k in n for k in ["cookies","waffle","pancake","popcorn","candy","churros","fudge"]):
        return "Bored"
    if any(k in n for k in ["buttermilk","light","clear soup","makhana","low sugar"]):
        return "Anxious"
    if any(k in n for k in ["salad","buddha bowl","stir-fry","grilled","minestrone","zucchini"]):
        return "Relaxed"
    if any(k in n for k in ["folate","iron","ragi","sesame","dates","ladoo","ladoo","preg"]):
        return "Pregnancy"
    return None


def approx_nutrition(name: str):
    """Mood-aware heuristic nutrition when APIs are unavailable."""
    n = name.lower()
    mood = _ITEM_TO_MOOD.get(n) or _guess_mood_from_name(n)

    # Non-veg keywords (for your veg-only toggle elsewhere)
    nonveg_kw = ["chicken","mutton","fish","egg","prawn","tuna","salmon","beef","pork","ham","bacon","shrimp"]

    # Default base
    calories = 180
    protein = round(random.uniform(3.0, 8.0), 1)
    vitamins = ["Various"]

    # If we still didn't get mood, fallback to generic keyword buckets (as before)
    if not mood:
        if any(k in n for k in ["salad","fruit","cucumber","banana","avocado","smoothie","sprout"]):
            calories = random.randint(60, 220); protein = round(random.uniform(1.0, 6.0), 1); vitamins = ["C","A"]
        elif any(k in n for k in ["pizza","burger","fries","cheese","pasta","brownie","donut","cake","ice cream","cheesecake","tiramisu"]):
            calories = random.randint(320, 720); protein = round(random.uniform(6.0, 18.0), 1); vitamins = ["B"]
        elif any(k in n for k in ["dal","paneer","egg","tofu","beans","lentil","chole","rajma"]):
            calories = random.randint(180, 420); protein = round(random.uniform(9.0, 26.0), 1); vitamins = ["B","E"]
        elif any(k in n for k in ["soup","khichdi","porridge","oats","green tea"]):
            calories = random.randint(40, 240); protein = round(random.uniform(1.0, 10.0), 1); vitamins = ["B","C"]
        elif any(k in n for k in ["nuts","almond","peanut","butter","walnut"]):
            calories = random.randint(150, 320); protein = round(random.uniform(5.0, 12.0), 1); vitamins = ["E"]
        return {"calories": calories, "protein_g": protein, "vitamins": ", ".join(vitamins), "source": "approx"}

    # Mood-specific ranges
    if mood == "Happy":
        calories = random.randint(300, 700)
        protein = round(random.uniform(5.0, 18.0), 1)
        vitamins = ["B", "E"]
    elif mood == "Sad":
        calories = random.randint(200, 500)
        protein = round(random.uniform(4.0, 15.0), 1)
        vitamins = ["B", "C"]
    elif mood == "Stressed":
        calories = random.randint(100, 300)
        protein = round(random.uniform(3.0, 12.0), 1)
        vitamins = ["C", "B"]
    elif mood == "Tired":
        calories = random.randint(200, 450)
        protein = round(random.uniform(6.0, 20.0), 1)
        vitamins = ["B", "E"]
    elif mood == "Excited":
        calories = random.randint(200, 600)
        protein = round(random.uniform(4.0, 14.0), 1)
        vitamins = ["B"]
    elif mood == "Bored":
        calories = random.randint(250, 650)
        protein = round(random.uniform(3.0, 10.0), 1)
        vitamins = ["B"]
    elif mood == "Anxious":
        calories = random.randint(80, 250)
        protein = round(random.uniform(3.0, 10.0), 1)
        vitamins = ["B", "C"]
    elif mood == "Relaxed":
        calories = random.randint(100, 300)
        protein = round(random.uniform(3.0, 12.0), 1)
        vitamins = ["A", "C", "E"]
    elif mood == "Pregnancy":
        calories = random.randint(200, 500)
        protein = round(random.uniform(6.0, 25.0), 1)
        vitamins = ["Folate", "Iron", "Calcium", "B12"]
    else:
        # generic
        calories = random.randint(150, 350)
        protein = round(random.uniform(3.0, 12.0), 1)
        vitamins = ["Various"]

    return {"calories": calories, "protein_g": protein, "vitamins": ", ".join(vitamins), "source": "approx"}


def get_nutrition(name: str):
    # Try Edamam
    nut, err = get_nutrition_edamam(name)
    if nut:
        return nut, None

    # Then USDA
    nut2, err2 = get_nutrition_usda(name)
    if nut2:
        return nut2, None

    # Heuristic fallback (now mood-aware)
    nut3 = approx_nutrition(name)
    emsgs = []
    if err: emsgs.append(err)
    if err2: emsgs.append(err2)
    return nut3, " | ".join(emsgs) if emsgs else None


# -----------------------
# AI Chat Helper Functions
# -----------------------
@lru_cache(maxsize=100)
def get_ai_response(prompt: str) -> str:
    if not GEMINI_AVAILABLE or not GEMINI_API_KEY:
        return "माफ़ कीजिए, Gemini AI सुविधा उपलब्ध नहीं है। कृपया google-generativeai install करें और API key सेट करें।"
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        full_prompt = f"""
        आप एक खुशमिजाज, दोस्ताना AI हैं जिसका नाम 'Mood Buddy' है।
        आप यूजर के मूड के आधार पर खाने के सजेशन देते हैं और उनका दिल भी बहलाते हैं।
        जवाब हमेशा हिंदी में, सरल भाषा में और दोस्ताना अंदाज में दें।
        यूजर कह रहा है: '{prompt}'
        """
        response = model.generate_content(full_prompt)
        return getattr(response, "text", "माफ़ कीजिए, मैं अभी जवाब नहीं दे पा रहा।")
    except Exception as e:
        return f"माफ़ कीजिए, मैं अभी जवाब नहीं दे पा रहा। त्रुटि: {str(e)}"

# -----------------------
# OAuth helpers (Google)
# -----------------------

def get_redirect_uri():
    return BASE_URL


def google_authorize_url():
    if not OAUTH_AVAILABLE:
        return None
    scope = [
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]
    oauth = OAuth2Session(GOOGLE_CLIENT_ID, redirect_uri=get_redirect_uri(), scope=scope)
    auth_url, state = oauth.authorization_url(GOOGLE_AUTH_URI, access_type="offline", prompt="select_account")
    st.session_state["oauth_state"] = state
    return auth_url


def exchange_code_for_token(code):
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": get_redirect_uri(),
        "grant_type": "authorization_code"
    }
    r = requests.post(GOOGLE_TOKEN_URI, data=data, timeout=8)
    r.raise_for_status()
    return r.json()


def fetch_userinfo(access_token):
    r = requests.get(GOOGLE_USERINFO, params={"access_token": access_token}, timeout=8)
    # FIX: correct method name
    r.raise_for_status()
    return r.json()

# -----------------------
# UI / UX CSS
# -----------------------
st.markdown("""
<style>
/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0f172a,#1e293b);
    color: #fff;
}
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* Grid System */
.grid { 
    display:grid; 
    grid-template-columns: repeat(auto-fill,minmax(280px,1fr)); 
    gap:20px; 
    align-items:start; 
    margin-top:20px;
}
.card { 
    background: rgba(255,255,255,0.08); 
    backdrop-filter: blur(14px) saturate(180%); 
    border-radius:18px;
    padding:18px; 
    margin-bottom:14px; 
    box-shadow:0 8px 30px rgba(0,0,0,0.2); 
    transition: all .25s ease; 
    animation: fadeIn 0.7s ease; 
}
.card:hover { 
    transform: translateY(-6px) scale(1.02); 
    box-shadow:0 20px 60px rgba(0,0,0,0.35); 
    border:1px solid rgba(255,255,255,0.25); 
}
.food-img { 
    width:100%; 
    height:180px; 
    object-fit:cover; 
    border-radius:12px; 
    margin-bottom:12px; 
}
.small-muted { 
    color:#94a3b8; 
    font-size:13px; 
}

/* Buttons */
.stButton button { 
    background: linear-gradient(90deg,#2563eb,#60a5fa); 
    color:white !important; 
    border-radius:12px; 
    padding:10px 16px;
    border:none; 
    font-weight:600; 
    transition: all .25s ease; 
}
.stButton button:hover { 
    background: linear-gradient(90deg,#1d4ed8,#3b82f6); 
    transform: translateY(-2px); 
    box-shadow:0 8px 20px rgba(37,99,235,0.4); 
}

/* Animations */
@keyframes fadeIn { 
    from {opacity:0; transform:translateY(10px);} 
    to {opacity:1; transform:translateY(0);} 
}

/* Footer */
.footer { 
    color:#94a3b8; 
    margin-top:28px; 
    text-align:center; 
    font-size:13px; 
}

/* Signup Page */
.signup-container {
    max-width: 500px;
    margin: 40px auto;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 15px;
    backdrop-filter: blur(10px);
}
.signup-title {
    text-align: center;
    color: #fff;
    margin-bottom: 30px;
}
.signup-form {
    display: flex;
    flex-direction: column;
    gap: 15px;
}
.signup-input {
    padding: 12px;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.1);
    color: white;
}
.signup-button {
    background: linear-gradient(90deg, #2563eb, #60a5fa);
    color: white;
    border: none;
    padding: 12px;
    border-radius: 8px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
}
.signup-button:hover {
    background: linear-gradient(90deg, #1d4ed8, #3b82f6);
    transform: translateY(-2px);
}

/* Profile Card */
.profile-card {
    text-align:center;
    padding:20px;
}
.profile-pic {
    width:100px;
    height:100px;
    border-radius:50%;
    object-fit:cover;
    margin-bottom:12px;
    border:3px solid #3b82f6;
}
.profile-name {
    font-size:18px;
    font-weight:600;
    color:#fff;
}
.profile-bio {
    font-size:14px;
    color:#94a3b8;
    margin-bottom:10px;
}

/* Upload Card */
.upload-box {
    border:2px dashed rgba(255,255,255,0.3);
    border-radius:12px;
    padding:25px;
    text-align:center;
    color:#94a3b8;
}
</style>
""", unsafe_allow_html=True)

# -----------------------
# Initialize Session State
# -----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "sched_started" not in st.session_state:
    st.session_state.sched_started = False
if "show_signup" not in st.session_state:
    st.session_state.show_signup = False
if "just_signed_up" not in st.session_state:
    st.session_state.just_signed_up = False

# -----------------------
# SIGNUP PAGE
# -----------------------
if not st.session_state.get("logged_in") and st.session_state.get("show_signup"):
    st.markdown("<div class='signup-container'>", unsafe_allow_html=True)
    st.markdown("<h1 class='signup-title'>Create Account</h1>", unsafe_allow_html=True)
    
    with st.form("signup_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        email = st.text_input("Email", placeholder="Enter your email")
        phone = st.text_input("Phone", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="Create a password")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
        
        col1, col2 = st.columns(2)
        with col1:
            signup_submit = st.form_submit_button("Sign Up", use_container_width=True)
        with col2:
            back_to_login = st.form_submit_button("Back to Login", use_container_width=True)
    
    if signup_submit:
        if not username or not email or not password:
            st.error("Please fill in all required fields")
        elif password != confirm_password:
            st.error("Passwords do not match")
        else:
            try:
                cur.execute("INSERT INTO users (username, password, email, phone, provider, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                            (username, hash_pw(password), email, phone, "local", 0))
                conn.commit()
                st.success("Account created successfully!")
                
                # Automatically log in the user after signup
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.is_admin = False
                st.session_state.show_signup = False
                st.session_state.just_signed_up = True
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Username already exists")
            except Exception as e:
                st.error(f"Error creating account: {str(e)}")
    
    if back_to_login:
        st.session_state.show_signup = False
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# -----------------------
# LOGIN PAGE
# -----------------------
if not st.session_state.get("logged_in"):
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<div class='signup-container'>", unsafe_allow_html=True)
        st.markdown("<h1 class='signup-title'>Login to MoodFood Pro</h1>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            login_submit = st.form_submit_button("Login", use_container_width=True)
            signup_redirect = st.form_submit_button("Create New Account", use_container_width=True)
        
        if login_submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                cur.execute("SELECT password, is_admin FROM users WHERE username=?", (username,))
                result = cur.fetchone()
                
                if result and result[0] == hash_pw(password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.is_admin = bool(result[1])
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        if signup_redirect:
            st.session_state.show_signup = True
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.stop()

# -----------------------
# OAuth redirect handling (optional)
# -----------------------
try:
    params = st.query_params if hasattr(st, "query_params") else st.experimental_get_query_params()
except Exception:
    params = {}

code_param = params.get("code")
if code_param and not st.session_state.get("logged_in") and GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    try:
        code = code_param[0] if isinstance(code_param, list) else code_param
        token = exchange_code_for_token(code)
        access_token = token.get("access_token")
        userinfo = fetch_userinfo(access_token)
        email = userinfo.get("email")
        if email:
            cur.execute("SELECT username FROM users WHERE username=?", (email,))
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO users (username,password,email,provider,is_admin) VALUES (?, ?, ?, ?, ?)",
                    (email, "", email, "google", 0)
                )
                conn.commit()
            st.session_state.logged_in = True
            st.session_state.username = email
            st.session_state.is_admin = False
            st.rerun()
    except Exception as e:
        st.error("Google sign-in failed: " + str(e))

# -----------------------
# Twilio helpers
# -----------------------

def get_twilio_client():
    if not TWILIO_AVAILABLE or not TWILIO_SID or not TWILIO_AUTH_TOKEN:
        return None
    try:
        return Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    except Exception:
        return None


def send_sms(to_number: str, message: str):
    client = get_twilio_client()
    if not client or not TWILIO_SMS_FROM:
        return False, "Twilio SMS not configured"
    try:
        client.messages.create(body=message, from_=TWILIO_SMS_FROM, to=to_number)
        return True, None
    except Exception as e:
        return False, str(e)


def send_whatsapp(to_number: str, message: str):
    client = get_twilio_client()
    if not client or not TWILIO_WA_FROM:
        return False, "Twilio WhatsApp not configured"
    try:
        client.messages.create(body=message, from_=TWILIO_WA_FROM, to=f"whatsapp:{to_number}" if not to_number.startswith("whatsapp:") else to_number)
        return True, None
    except Exception as e:
        return False, str(e)


def get_user_prefs(u: str):
    cur.execute("SELECT phone,sms_enabled,wa_enabled,reminder_time,email FROM users WHERE username=?", (u,))
    r = cur.fetchone()
    if not r:
        return {"phone": "", "sms_enabled": 0, "wa_enabled": 0, "reminder_time": "09:00", "email": ""}
    return {"phone": r[0] or "", "sms_enabled": int(r[1] or 0), "wa_enabled": int(r[2] or 0), "reminder_time": r[3] or "09:00", "email": r[4] or ""}

# -----------------------
# Reminder engine (runs every 60s)
# -----------------------

def send_reminders_due():
    now_str = datetime.now().strftime("%Y-%m-%d")
    now_hm = datetime.now().strftime("%H:%M")

    cur.execute("SELECT username, phone, sms_enabled, wa_enabled, reminder_time FROM users WHERE (sms_enabled=1 OR wa_enabled=1)")
    for u, phone, sms_en, wa_en, rtime in cur.fetchall():
        rtime = rtime or "09:00"
        if now_hm != rtime:
            continue
        cur.execute("SELECT 1 FROM notif_log WHERE username=? AND sent_date=?", (u, now_str))
        if cur.fetchone():
            continue
        msg = "🌿 MoodFood Reminder: apna mood log karna na bhoolen! Open app & generate suggestions 🍽️"
        if sms_en and phone:
            send_sms(phone, msg)
        if wa_en and phone:
            send_whatsapp(phone, msg)
        try:
            cur.execute("INSERT INTO notif_log (username,sent_date) VALUES (?, ?)", (u, now_str))
            conn.commit()
        except Exception:
            pass


def start_scheduler_once():
    if st.session_state.sched_started or not TWILIO_AVAILABLE:
        return
    schedule.every(1).minutes.do(send_reminders_due)

    def _loop():
        while True:
            try:
                schedule.run_pending()
            except Exception:
                pass
            time.sleep(60)

    threading.Thread(target=_loop, daemon=True).start()
    st.session_state.sched_started = True

# start scheduler after login
start_scheduler_once()

# -----------------------
# SIDEBAR NAVIGATION (after login)
# -----------------------
with st.sidebar:
    st.title("🍽️ MoodFood Pro")
    st.markdown(f"**Welcome, {st.session_state.username}**")
    
    if st.session_state.get("just_signed_up", False):
        st.success("🎉 Welcome to MoodFood Pro! Your account has been created successfully.")
        st.session_state.just_signed_up = False
    
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.is_admin = False
        st.session_state.chat_history = []
        st.rerun()
    
    st.markdown("---")
    page = st.radio("Navigate", ["Home","Journal","Community","Health Conditions","Admin","Export","Support","AI Chat"])

# -----------------------
# HOME
# -----------------------
if page == "Home":
    st.markdown("<h1 style='text-align:center; margin-bottom:20px;'>🏠 Mood → Food Generator</h1>", unsafe_allow_html=True)
    st.caption("Nutrition: Edamam → USDA → heuristic")

    # ---------- Streak, progress-to-100 & badges ----------
    username = "your_username_here"  # <-- define it first
    cur.execute("SELECT date FROM moods WHERE username=? ORDER BY date DESC", (username,))

   
    rows_dates = cur.fetchall()
    all_dates = []
    if rows_dates:
        for r in rows_dates:
            try:
                if ' ' in r[0]:
                    all_dates.append(datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S").date())
                else:
                    all_dates.append(datetime.strptime(r[0], "%Y-%m-%d").date())
            except Exception:
                continue

    today = datetime.now().date()
    streak = 0

    if all_dates:
        all_dates_sorted = sorted(all_dates)
        current_date = today
        consecutive_days = 0
        while current_date in all_dates_sorted:
            consecutive_days += 1
            current_date -= timedelta(days=1)
        streak = consecutive_days

    cycle_streak = streak % 100
    progress_pct = int((cycle_streak / 100) * 100) if streak > 0 else 0

    badges = []
    if streak >= 3:  badges.append(("🌱 Growth Seeker", "You're building the habit!"))
    if streak >= 7:  badges.append(("🔥 Streak Master", "One week strong, keep going!"))
    if streak >= 14: badges.append(("⚡ Consistency Hero", "Two weeks of discipline!"))
    if streak >= 30: badges.append(("🌟 Mindful Legend", "A full month of mindfulness!"))
    if streak >= 100: badges.append(("👑 Mood Champion", "100 days non-stop – You inspire others!"))

    c1, c2 = st.columns([3,2])
    with c2:
        st.markdown(f"#### 🔥 Streak: **{streak} days**")
        st.progress(progress_pct)
        st.caption(f"Next reset at 100 days · progress {progress_pct}%")

        if streak == 0:
            st.info("💡 Add your daily mood in Journal section to start your streak!")

        if badges:
            st.markdown("**🎖️ Badges:**")
            for b, t in badges[:5]:
                st.markdown(f"- {b} — _{t}_")

        if streak in (7, 30):
            st.snow()
        if streak >= 100 and cycle_streak == 0 and streak != 0:
            st.balloons()
            st.success("👑 100-DAY MOOD CHAMPION unlocked!")

    # ---------- Quick Mood Add for Streak ----------
    with st.expander("📝 Quick Mood Entry (For Streak)", expanded=False):
        st.write("Add your current mood to increase your streak:")
        quick_mood = st.selectbox("Select your mood", list(DEFAULT_POOLS.keys()), key="quick_mood")
        if st.button("Add Mood & Refresh Streak"):
            cur.execute("INSERT INTO moods (username, date, mood) VALUES (?, ?, ?)",
                        (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), quick_mood))
            conn.commit()
            st.success("Mood added! Refresh the page to see updated streak.")
            time.sleep(1)
            st.rerun()

    # ---------- Mood → Food Generator ----------
    col1, col2 = st.columns([3,1])
    with col1:
        mood = st.selectbox("💡 How are you feeling today?", list(DEFAULT_POOLS.keys()), key="food_mood")
    with col2:
        veg_only = st.toggle("🥦 Veg-only", value=False, key="veg_toggle")

    c1, c2 = st.columns([1,2])
    with c1:
        num = st.number_input("📌 No. of suggestions", min_value=1, max_value=10, value=5, key="suggestions_num")
    with c2:
        if st.button("🔮 Generate Foods", use_container_width=True, key="generate_foods"):
            pool = get_pool_from_db(mood)
            if not pool:
                st.error("⚠️ No items found for this mood. Ask admin to add items.")
            else:
                if veg_only:
                    nonveg = ["chicken","mutton","fish","egg","prawn"]
                    pool = [p for p in pool if not any(k in p.lower() for k in nonveg)]
                picks = random.sample(pool, min(len(pool), int(num)))
                try:
                    cur.execute("INSERT INTO history (username,date,mood,suggestions) VALUES (?,?,?,?)",
                                (username, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), mood, json.dumps(picks)))
                    conn.commit()
                except Exception as e:
                    st.error(f"Error saving history: {e}")

                st.markdown("<div class='grid'>", unsafe_allow_html=True)
                for item in picks:
                    nut, err = get_nutrition(item)
                    img_q = urllib.parse.quote_plus(item + " food")
                    img_url = f"https://source.unsplash.com/collection/9623632/800x600?{img_q}"
                    html = f"""
                    <div class="card">
                      <img class="food-img" src="{img_url}" alt="{item}" />
                      <div style="margin-top:8px; font-size:18px; font-weight:600;">{item}</div>
                      <div class="small-muted">🔥 {nut.get('calories','?')} kcal &nbsp; | &nbsp; 💪 {nut.get('protein_g','?')} g protein</div>
                      <div class="small-muted">🌿 Vitamins: {nut.get('vitamins','Various')} 
                        <span style="color:#38bdf8">{' ['+nut.get('source')+']' if nut.get('source') else ''}</span></div>
                    """
                    if err:
                        html += f"<div style='color:#f87171; margin-top:6px; font-size:12px'>⚠️ {err}</div>"
                    html += "</div>"
                    st.markdown(html, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # instant notification with picks (if user enabled)
                prefs = get_user_prefs(username)
                phone = prefs["phone"]
                msg = f"🍽️ MoodFood: Mood '{mood}' ke liye {len(picks)} ideas: " + ", ".join(picks[:6])
                if phone and phone.strip():
                    if prefs["sms_enabled"]:
                        ok, er = send_sms(phone, msg)
                        if ok: st.success("📩 SMS sent")
                        elif er: st.info(f"SMS not sent: {er}")
                    if prefs["wa_enabled"]:
                        ok, er = send_whatsapp(phone, msg)
                        if ok: st.success("📲 WhatsApp sent")
                        elif er: st.info(f"WhatsApp not sent: {er}")


    # -----------------------
    # Recent History Timeline  (MOVED INSIDE HOME)
    # -----------------------
    st.markdown("<h3 style='margin-top:30px;'>🕑 Recent History Timeline</h3>", unsafe_allow_html=True)

    cur.execute("SELECT date,mood,suggestions FROM history WHERE username=? ORDER BY id DESC LIMIT 12", (username,))
    rows = cur.fetchall()

    if rows:
        timeline_css = """
        <style>
        .timeline {
            position: relative;
            margin: 20px 0;
            padding: 0;
            list-style: none;
        }
        .timeline:before {
            position: absolute;
            left: 30px;
            top: 0;
            content: ' ';
            width: 2px;
            height: 100%;
            background-color: #10b981;
        }
        .timeline-item {
            position: relative;
            margin: 20px 0;
            padding-left: 60px;
        }
        .timeline-item:before {
            content: '●';
            position: absolute;
            left: 22px;
            font-size: 20px;
            color: #10b981;
        }
        .timeline-date {
            font-weight: bold;
            color: #374151;
        }
        .timeline-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 12px 18px;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.1);
            transition: 0.3s ease-in-out;
            border: 1px solid rgba(0,0,0,0.1);
        }
        .timeline-card:hover {
            transform: translateY(-2px);
            box-shadow: 0px 5px 15px rgba(0,0,0,0.15);
        }
        .timeline-food {
            color: #1f2937;
            font-weight: 500;
            margin-top: 5px;
        }
        .timeline-mood {
            color: #10b981;
            font-weight: 600;
        }
        </style>
        """

        st.markdown(timeline_css, unsafe_allow_html=True)
        st.markdown("<ul class='timeline'>", unsafe_allow_html=True)

        for d, m, sjson in rows:
            try:
                s = json.loads(sjson)
            except:
                s = []
            
            # Format date for better display
            try:
                if ' ' in d:
                    date_obj = datetime.strptime(d, "%Y-%m-%d %H:%M:%S")
                else:
                    date_obj = datetime.strptime(d, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%d %b %Y, %I:%M %p")
            except:
                formatted_date = d
                
            suggestions = ", ".join(s[:5]) if s else "No suggestions"
            
            st.markdown(
                f"""
                <li class="timeline-item">
                    <div class="timeline-card">
                        <div class="timeline-date">📅 {formatted_date} — Mood: <span class='timeline-mood'>{m}</span></div>
                        <div class="timeline-food">🍴 {suggestions}</div>
                    </div>
                </li>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</ul>", unsafe_allow_html=True)

    else:
        st.info("No history yet — generate something!")

# -----------------------
# JOURNAL
# -----------------------
elif page == "Journal":
    st.markdown("<h1 style='text-align:center;'>📓 Mood Journal & Trends</h1>", unsafe_allow_html=True)

    # ✅ check if logged in
    if "username" not in st.session_state:
        st.error("You must log in first.")
    else:
        username = st.session_state["username"]  # get current logged-in user

        days = st.slider("📆 Show past days", 3, 60, 14)

        # FIX: LIMIT parameter via f-string
        cur.execute(f"SELECT date,mood FROM moods WHERE username=? ORDER BY id DESC LIMIT {days}", (username,))
        rows = cur.fetchall()

        if rows:
            st.markdown("<div style='border-left:3px solid #2563eb; margin-left:15px; padding-left:15px;'>", unsafe_allow_html=True)
            for d, m in rows:
                st.markdown(f"""
                <div class="card" style="margin-bottom:12px;">
                    <div style="font-size:13px; color:#64748b;">📅 {d}</div>
                    <div style="margin-top:4px; font-weight:600; font-size:15px;">😌 {m}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            cnt = Counter([r[1] for r in rows])
            st.subheader("📊 Mood Frequency")
            st.bar_chart(dict(cnt))
        else:
            st.info("No moods recorded yet. Start journaling your feelings!")

        with st.expander("➕ Add a New Mood"):
            with st.form("add_mood"):
                new_mood = st.selectbox("✨ Select your mood", list(DEFAULT_POOLS.keys()))
                if st.form_submit_button("💾 Save Mood"):
                    cur.execute(
                        "INSERT INTO moods (username,date,mood) VALUES (?, ?, ?)",
                        (username, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), new_mood)
                    )
                    conn.commit()
                    st.success("Mood added successfully ✅")
                    st.rerun()


# -----------------------
# COMMUNITY
# -----------------------
elif page == "Community":
    st.header("👥 Community")
    with st.expander("Create post"):
        cap = st.text_input("Caption")
        imgurl = st.text_input("Image URL (optional)")
        if st.button("Post now"):
            cur.execute("INSERT INTO posts (username,date,caption,photo) VALUES (?, ?, ?, ?)",
                        (username, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), cap, imgurl))
            conn.commit()
            st.success("Posted")
            st.rerun()
    search = st.text_input("Search posts by username")
    if search:
        cur.execute("SELECT id,username,date,caption,photo,likes FROM posts WHERE username=? ORDER BY id DESC", (search.strip(),))
    else:
        cur.execute("SELECT id,username,date,caption,photo,likes FROM posts ORDER BY id DESC LIMIT 50")
    posts = cur.fetchall()
    for pid,puser,pdate,pcaption,pphoto,plikes in posts:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"**{puser}** • <span class='small-muted'>{pdate}</span>", unsafe_allow_html=True)
        if pcaption:
            st.write(pcaption)
        if pphoto:
            try:
                st.image(pphoto, use_column_width=True)
            except Exception:
                st.write("(Image failed to load)")
        st.write(f"❤️ {plikes} likes")
        c1,c2,c3 = st.columns([1,1,1])
        if c1.button("Like", key=f"like_{pid}"):
            cur.execute("UPDATE posts SET likes = likes + 1 WHERE id= ?", (pid,))
            conn.commit()
            st.rerun()
        if c2.button("Delete", key=f"del_{pid}"):
            if puser == username or st.session_state.get("is_admin"):
                cur.execute("DELETE FROM posts WHERE id=?", (pid,))
                conn.commit()
                st.success("Deleted")
                st.rerun()
            else:
                st.error("You can delete only your own posts")
        if c3.button("Save to history", key=f"save_{pid}"):
            cur.execute("INSERT INTO history (username,date,mood,suggestions) VALUES (?, ?, ?, ?)",
                        (username, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "SavedPost", json.dumps([pcaption or "Photo"])))
            conn.commit()
            st.success("Saved")
        st.markdown("</div>", unsafe_allow_html=True)
# -----------------------
# HEALTH CONDITIONS
# -----------------------
elif page == "Health Conditions":
    st.markdown("<h2 style='text-align:center; color:#2563eb'>🩺 Health Conditions - Smart Food Guidance</h2>", unsafe_allow_html=True)

    CONDITIONS = {
        "Pregnancy": {
            "good": ["Milk", "Nuts", "Leafy veg", "Fruits", "Whole grains", "Lentils", "Eggs"],
            "avoid": ["Raw papaya", "Excess pineapple", "Alcohol"],
            "tips": "✅ Eat small, frequent meals. 🥛 Stay hydrated. 🚶‍♀️ Do light exercise like walking.",
            "img": "https://images.unsplash.com/photo-1589935447067-553c30bfa014"
        },
        "Diabetes": {
            "good": ["Oats", "Brown rice", "Vegetables", "Dal", "Nuts"],
            "avoid": ["Sweets", "Sugary drinks"],
            "tips": "✅ Monitor sugar levels daily. 🍵 Prefer green tea. 🚶‍♂️ 30 min walk daily.",
            "img": "https://images.unsplash.com/photo-1600628421055-4cf8c8bf3d5a"
        },
        "High BP": {
            "good": ["Fruits", "Veg", "Low-salt dals", "Oats"],
            "avoid": ["Pickles", "Processed foods"],
            "tips": "✅ Limit salt intake. 🥗 Eat potassium-rich foods like banana. 🧘 Practice meditation.",
            "img": "https://images.unsplash.com/photo-1606756790138-2270d3dc02e0"
        },
        "Fever": {
            "good": ["Soups", "Khichdi", "Hydration"],
            "avoid": ["Greasy heavy food"],
            "tips": "✅ Drink warm fluids. 🛌 Take rest. 🍲 Eat light, easy-to-digest foods.",
            "img": "https://images.unsplash.com/photo-1515543237350-b3eea1ec8082"
        },
        "Cough & Cold": {
            "good": ["Ginger tea", "Warm soups", "Honey"],
            "avoid": ["Cold drinks", "Ice cream"],
            "tips": "✅ Gargle with warm salt water. ☕ Drink herbal teas. 🌡️ Keep warm & avoid dust.",
            "img": "https://images.unsplash.com/photo-1604503468506-c8f34eb5fd67"
        }
    }

    cond = st.selectbox("🔎 Select a Condition", list(CONDITIONS.keys()))
    info = CONDITIONS[cond]

    # Convert list to line-break HTML for better readability
    good_html = "<br>".join(info['good'])
    avoid_html = "<br>".join(info['avoid'])

    st.markdown(f"""
    <div class="card" style="text-align:center;">
        <img class="food-img" src="{info['img']}" alt="{cond}" style="width:100%; max-width:400px; border-radius:10px;" />
        <h3 style="margin-top:10px; color:#0f172a">{cond}</h3>

        <div style="margin-top:8px; padding:10px; border-radius:10px; background:rgba(34,197,94,0.12); color:#166534; font-weight:500; text-align:left;">
            ✅ Recommended:<br>{good_html}
        </div>

        <div style="margin-top:8px; padding:10px; border-radius:10px; background:rgba(239,68,68,0.12); color:#991b1b; font-weight:500; text-align:left;">
            🚫 Avoid:<br>{avoid_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Extra Expandable Tips Section
    with st.expander("📌 Extra Health Tips"):
        st.write(info["tips"])

    # Suggested Dishes
    st.markdown("### 🍴 Suggested Dishes")
    suggestions = {
        "Diabetes": "🥗 Moong Dal Chilla, 🥦 Veg Soup, 🍵 Green Tea",
        "Pregnancy": "🍲 Dal Khichdi, 🥛 Almond Milk, 🥗 Spinach Salad",
        "High BP": "🥗 Oats Upma, 🍌 Banana Smoothie, 🥬 Steamed Veggies",
        "Fever": "🍲 Vegetable Soup, 🍚 Soft Khichdi, 🍵 Herbal Tea",
        "Cough & Cold": "☕ Ginger-Honey Tea, 🍵 Tulsi Kadha, 🍲 Tomato Soup"
    }
    st.info(suggestions.get(cond, "No suggestions available."))
# -----------------------
# ADMIN
# -----------------------
elif page == "Admin":
    st.header("🔧 Admin — Manage Mood Pools")

    # ✅ check if user is logged in
    if "username" not in st.session_state:
        st.error("You must log in first.")
    else:
        username = st.session_state["username"]  # get current username

        cur.execute("SELECT is_admin FROM users WHERE username=?", (username,))
        r = cur.fetchone()
        if not r or r[0] != 1:
            st.error("Admin access only.")
        else:
            st.success("Admin verified")
            sel_mood = st.selectbox("Select mood to edit", list(DEFAULT_POOLS.keys()))
            items = get_pool_from_db(sel_mood)
            st.write(f"Items for {sel_mood} (count: {len(items)})")
            for i, it in enumerate(items, start=1):
                st.write(f"{i}. {it}")
            new_item = st.text_input("Add new item to pool")
            if st.button("Add item"):
                if new_item.strip():
                    cur.execute("INSERT INTO mood_items (mood,name) VALUES (?, ?)", (sel_mood, new_item.strip()))
                    conn.commit()
                    st.success("Added")
                    st.rerun()
            st.markdown("---")
            del_item = st.selectbox("Select item to delete", ["-- choose --"] + items)
            if del_item != "-- choose --" and st.button("Delete selected"):
                cur.execute("DELETE FROM mood_items WHERE id IN (SELECT id FROM mood_items WHERE mood=? AND name=? LIMIT 1)",
                            (sel_mood, del_item))
                conn.commit()
                st.success("Deleted")
                st.rerun()


# -----------------------
# EXPORT
# -----------------------
elif page == "Export":
    st.header("📂 Export")
    if st.button("Export my history as TXT"):
        cur.execute("SELECT date,mood,suggestions FROM history WHERE username=? ORDER BY id DESC", (username,))
        rows = cur.fetchall()
        fname = f"{username}_history_{datetime.utcnow().strftime('%Y%m%d')}.txt"
        path = os.path.join(BASE_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(str(r) + "\n")
        with open(path, "rb") as f:
            st.download_button("Download TXT", f, file_name=fname)
    st.write("Other exports coming soon.")

# -----------------------
# SUPPORT (includes Notification Settings UI)
# -----------------------
elif page == "Support":
    st.header("💡 Support & Notes")
    st.write("- Google Sign-in requires CLIENT_ID/SECRET and correct Redirect URI (BASE_URL).")
    st.write("- Edamam: APP_ID & APP_KEY in .streamlit/secrets.toml")
    st.write("- USDA API key in secrets")
    st.write("- Gemini API key in secrets")
    st.write("- If Edamam fails → USDA → heuristic.")
    st.write("Contact: support@foodfeel.app")

    st.markdown("### 🔔 Notification Settings (SMS/WhatsApp)")

    # ✅ check login
    if "username" not in st.session_state:
        st.error("You must log in first to access preferences.")
    else:
        username = st.session_state["username"]   # get logged-in user
        prefs = get_user_prefs(username)

        # fallback for reminder_time
        try:
            default_time = datetime.strptime(prefs.get("reminder_time") or "09:00", "%H:%M").time()
        except Exception:
            default_time = datetime.strptime("09:00", "%H:%M").time()

        with st.form("notif_prefs"):
            phone = st.text_input("📱 Phone (E.164 e.g. +9198xxxxxxx)", value=prefs.get("phone", ""))
            sms_en = st.checkbox("Enable SMS", value=bool(prefs.get("sms_enabled")))
            wa_en = st.checkbox("Enable WhatsApp", value=bool(prefs.get("wa_enabled")))
            rtime = st.time_input("Daily Reminder Time (server time)", value=default_time)

            saved = st.form_submit_button("Save Preferences")
            if saved:
                cur.execute(
                    "UPDATE users SET phone=?, sms_enabled=?, wa_enabled=?, reminder_time=? WHERE username=?",
                    (phone.strip(), 1 if sms_en else 0, 1 if wa_en else 0, rtime.strftime("%H:%M"), username)
                )
                conn.commit()
                st.success("Notification preferences saved ✅")
                prefs = get_user_prefs(username)  # refresh after save

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Test SMS"):
                ok, er = send_sms(prefs["phone"], "✅ MoodFood test: SMS working!")
                if ok: st.success("SMS sent")
                else: st.error(f"SMS failed: {er}")
        with c2:
            if st.button("Test WhatsApp"):
                ok, er = send_whatsapp(prefs["phone"], "✅ MoodFood test: WhatsApp working!")
                if ok: st.success("WhatsApp sent")
                else: st.error(f"WhatsApp failed: {er}")


# -----------------------
# AI CHAT WITH GEMINI
# -----------------------
elif page == "AI Chat":
    st.header("💬 Mood Buddy – आपका AI दोस्त! 🤖")
    if not GEMINI_API_KEY:
        st.error("""
        AI Chat सुविधा उपलब्ध नहीं है। कृपया:
        1) Gemini API Key लें (https://ai.google.dev/)
        2) .streamlit/secrets.toml में जोड़ें: gemini_api_key = "YOUR_KEY"
        3) ऐप को रीस्टार्ट करें
        """)
        st.stop()

    st.markdown("""
    नमस्ते! मैं आपका **Mood Buddy** हूँ.  
    मैं आपके मूड के हिसाब से खाने के आइडिया देता हूँ और दिल भी बहलाता हूँ 😊  
    नीचे अपना मूड या बात टाइप करें:
    """)

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("आप कैसा महसूस कर रहे हैं?")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.spinner("Mood Buddy सोच रहा है..."):
            time.sleep(0.4)
            try:
                bot_reply = get_ai_response(prompt)
            except Exception as e:
                bot_reply = f"माफ़ कीजिए, कुछ तकनीकी समस्या आई: {str(e)}"

        with st.chat_message("assistant"):
            st.markdown(bot_reply)
        st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

# -----------------------
# FOOTER
# -----------------------
st.markdown("---")
st.markdown("<div class='footer'>MoodFood Pro © 2023 | Built with ❤️ for better mental health through nutrition</div>", unsafe_allow_html=True)
