import streamlit as st
import random

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Emobite - Mood Based Food Suggestions (50+ per mood & health)",
    page_icon="🍲",
    layout="centered"
)

# ---------------- Strong SEO (Meta, OG, Twitter, JSON-LD, Canonical, Robots) ----------------
st.markdown("""
<!-- Primary SEO -->
<meta name="description" content="MoodFood: 50+ mood-based food suggestions with 50+ health condition modifiers. Get personalized diet ideas for Happy, Sad, Stressed, Angry, Tired, Excited, Relaxed, Anxious & Bored moods." />
<meta name="keywords" content="mood food app, mood based diet, food suggestions, healthy eating, diabetes friendly food, high BP diet, PCOS diet, thyroid diet, weight loss food, heart healthy recipes, Indian food, meal ideas" />
<meta name="author" content="Manish Yadav"/>
<meta name="robots" content="index, follow"/>

<!-- Canonical & Sitemap -->
<link rel="canonical" href="https://yourdomain.com/"/>
<link rel="sitemap" type="application/xml" title="Sitemap" href="https://yourdomain.com/sitemap.xml"/>

<!-- Open Graph -->
<meta property="og:title" content="MoodFood - Mood Based Food Suggestions"/>
<meta property="og:description" content="Personalized food ideas by mood & health. 50+ foods per mood, 50+ health modifiers. Try it now!"/>
<meta property="og:type" content="website"/>
<meta property="og:url" content="https://yourdomain.com/"/>
<meta property="og:image" content="https://yourdomain.com/thumbnail.png"/>

<!-- Twitter Card -->
<meta name="twitter:card" content="summary_large_image"/>
<meta name="twitter:title" content="MoodFood - Mood Based Food Suggestions"/>
<meta name="twitter:description" content="Get 50+ mood-based foods & 50+ health-wise modifiers for a smarter diet."/>
<meta name="twitter:image" content="https://yourdomain.com/thumbnail.png"/>

<!-- Performance hints -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />

<!-- JSON-LD: WebApplication -->
<script type="application/ld+json">
{
  "@context":"https://schema.org",
  "@type":"WebApplication",
  "name":"MoodFood",
  "url":"https://yourdomain.com/",
  "description":"50+ mood-based food ideas with 50+ health modifiers for Diabetes, High BP, Low BP, PCOS, Thyroid, Weight Loss, Heart Issues.",
  "applicationCategory":"FoodApplication",
  "operatingSystem":"Web Browser",
  "creator":{"@type":"Person","name":"Manish Yadav"}
}
</script>

<!-- JSON-LD: FAQPage (boost SEO for questions) -->
<script type="application/ld+json">
{
 "@context":"https://schema.org",
 "@type":"FAQPage",
 "mainEntity":[
  {"@type":"Question","name":"MoodFood kya karta hai?","acceptedAnswer":{"@type":"Answer","text":"MoodFood aapke mood aur health condition ke hisaab se khane ki recommendations deta hai."}},
  {"@type":"Question","name":"Kya ye diabetes/high BP ke liye options deta hai?","acceptedAnswer":{"@type":"Answer","text":"Haan, har health condition ke liye 50+ safe-style modifiers diye gaye hain."}},
  {"@type":"Question","name":"Kya mai ek baar me multiple suggestions le sakta hoon?","acceptedAnswer":{"@type":"Answer","text":"Haan, slider se 1 se 5 tak suggestions ek saath le sakte hain."}}
 ]
}
</script>
""", unsafe_allow_html=True)

# ---------------- Custom CSS (3D UI) ----------------
st.markdown("""
<style>
:root { --card:#ffffff; --ink:#0f172a; --muted:#475569; --bg1:#f8fbff; --bg2:#e9f6ff; --brand:#ef4444; }
.stApp { background: radial-gradient(1000px 600px at 20% 0%, var(--bg1), var(--bg2)); }

/* headings readable on light bg */
h1,h2,h3 { text-align:center; font-family: 'Poppins', system-ui, -apple-system, Segoe UI, Roboto, Ubuntu; color: var(--ink); text-shadow: 0 1px 0 rgba(255,255,255,.8); }
.small { opacity:.9; text-align:center; margin-top:-8px; color: var(--muted); }

.panel { background: rgba(255,255,255,0.95); border-radius:18px; padding:18px; box-shadow: 0 12px 30px rgba(0,0,0,0.12); border:1px solid rgba(15,23,42,.06); }
.rec-card {
  background: var(--card);
  border-radius: 16px;
  padding: 16px 18px;
  margin: 10px 0;
  box-shadow: 0 10px 24px rgba(20, 60, 90, 0.18);
  border: 1px solid rgba(0,0,0,0.06);
  transition: transform .18s ease, box-shadow .18s ease;
  color: var(--ink);
}
.rec-card:hover { transform: translateY(-4px); box-shadow: 0 16px 36px rgba(20, 60, 90, 0.25); }
.badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px; background:#eef7ff; border:1px solid #d5ecff; margin-left:6px; color:#0b3a64; }

.search-box {
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(255,255,255,.9));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 18px; padding: 16px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.15);
  color: var(--ink);
}

/* ★ New: SEO-friendly, readable footer */
.footer-wrap { display:flex; justify-content:center; margin:32px 0 10px; }
.footer {
  background: rgba(255,255,255,.92);
  border: 1px solid rgba(15,23,42,.08);
  border-radius: 14px;
  padding: 10px 16px;
  box-shadow: 0 10px 28px rgba(0,0,0,.14);
  max-width: 820px; width: 100%;
}
.footer .links { text-align:center; font-weight:600; }
.footer .links a {
  color: var(--ink); text-decoration:none; padding:0 8px;
}
.footer .links a:hover { text-decoration:underline; }
.footer .copy { text-align:center; color: var(--muted); font-size:13px; margin-top:4px; }
.footer .dot { color:#94a3b8; padding:0 4px; }
.badge-domain {
  display:inline-block; background:#e2f7ee; color:#065f46; border:1px solid #a7f3d0;
  padding:2px 6px; border-radius:8px; font-size:12px; margin-left:6px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- App Title ----------------
st.markdown("<h1>🍲 MoodFood App</h1>", unsafe_allow_html=True)
st.markdown("<p class='small'>Get quick food suggestions based on your mood & health</p>", unsafe_allow_html=True)

# ---------------- Session States ----------------
if "favorites" not in st.session_state: st.session_state["favorites"] = []
if "last" not in st.session_state: st.session_state["last"] = []

# ---------------- Inputs ----------------
with st.container():
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        mood = st.selectbox(
            "Your Mood Today",
            ['Happy','Sad','Stressed','Angry','Tired','Excited','Relaxed','Anxious','Bored'],
            help="Select your current mood"
        )
    with c2:
        health = st.selectbox(
            "Health Condition",
            ['None','Diabetes','High BP','Low BP','PCOS','Thyroid','Weight Loss','Heart Issues'],
            help="Pick a condition to tailor suggestions"
        )
    with c3:
        count = st.slider("How many suggestions?", 1, 5, 3, help="Get 1–5 ideas at once")

# ---------------- Datasets (50+ each) ----------------
recipes = {
    'Happy': [
        'Colorful Fruit Salad','Vegetable Pasta','Ice Cream','Smoothie Bowl','Fresh Juice',
        'Yogurt Parfait','Avocado Toast','Berry Mix','Dark Chocolate','Sweet Potato Fries',
        'Fresh Spring Rolls','Fruit Chaat','Pani Puri','Bhel Puri','Sev Puri',
        'Dahi Puri','Pav Bhaji','Vada Pav','Samosa','Kachori',
        'Jalebi','Gulab Jamun','Rasgulla','Rasmalai','Lassi',
        'Mango Shake','Butter Chicken','Chicken Tikka','Paneer Tikka','Veg Biryani',
        'Pulao','Fried Rice','Chole Bhature','Rajma Chawal','Dal Makhani',
        'Butter Naan','Garlic Naan','Aloo Paratha','Gobi Paratha','Masala Dosa',
        'Uttapam','Idli Sambar','Medu Vada','Rava Dosa','Pongal',
        'Upma','Poha','Khaman Dhokla','Khandvi','Misal Pav',
        'Dabeli','Kathi Roll','Frankie','Paneer Bhurji','Veg Sandwich'
    ],
    'Sad': [
        'Comfort Soup','Grilled Cheese','Mashed Potatoes','Hot Chocolate','Warm Milk',
        'Oatmeal','Khichdi','Dal Rice','Ghee Rice','Kheer',
        'Sooji Halwa','Moong Dal Khichdi','Curd Rice','Kadhi Chawal','Sambar Rice',
        'Rasam Rice','Yellow Dal','Tomato Soup','Sweet Corn Soup','Badam Milk',
        'Kesar Milk','Rava Kesari','Appam','Puttu','Adai',
        'Pesarattu','Jowar Roti','Bajra Roti','Makki ki Roti','Thepla',
        'Khakhra','Papad with Ghee','Achaar Rice','Raita Bowl','Yogurt with Honey',
        'Chaas','Buttermilk','Nimbu Pani','Shikanji','Aam Panna',
        'Kokum Sherbet','Veg Stew','Soft Idli','Butter Maggi','Veg Porridge',
        'Veg Upma','Soft Paratha with Curd','Paneer Pulao','Sabudana Khichdi','Moong Dal Soup'
    ],
    'Stressed': [
        'Herbal Tea','Green Tea','Dark Chocolate','Nuts Mix','Seeds Mix',
        'Banana','Oatmeal','Yogurt','Leafy Greens Salad','Grilled Salmon',
        'Whole Grain Khichdi','Fresh Fruits Bowl','Chamomile Tea','Tulsi Tea','Ginger Tea',
        'Lemon Tea','Turmeric Milk','Warm Water','Coconut Water','Vegetable Juice',
        'Kosambari','Sprouts Salad','Moong Salad','Chana Salad','Fruit Chaat',
        'Vegetable Chaat','Steamed Vegetables','Boiled Vegetables','Grilled Vegetables','Baked Vegetables',
        'Steamed Rice','Boiled Chicken','Grilled Fish','Baked Fish','Tandoori Paneer',
        'Phulka Roti','Chapati','Ragi Mudde','Millet Khichdi','Quinoa Salad',
        'Brown Rice Bowl','Hummus with Veggies','Roasted Chana','Makhana','Pumpkin Soup',
        'Tomato Basil Soup','Broccoli Soup','Khichdi with Ghee','Sweet Potato Mash','Masala Oats'
    ],
    'Angry': [
        'Cooling Juice','Cucumber Salad','Mint Lemonade','Plain Yogurt','Cold Smoothie',
        'Fresh Salad','Green Vegetables','Coconut Water','Watermelon','Muskmelon',
        'Buttermilk','Curd Rice','Cucumber Raita','Mint Chutney Sandwich','Coriander Chutney Dosa',
        'Tomato Cucumber Sandwich','Coconut Chutney Idli','Green Mango Chutney Roll','Tamarind Rice','Lemon Rice',
        'Coconut Rice','Puliyogare','Bisi Bele Bath','Sambar','Rasam',
        'Kootu','Porial','Thoran','Aviyal','Olan',
        'Parippu Curry','Mor Kuzhambu','Kadhi','Neer Mor','Sambharam',
        'Barley Water','Sabja Water','Aam Panna','Pudina Rice','Veg Raita',
        'Lauki Raita','Beet Raita','Cucumber Sticks','Celery Sticks','Coconut Lassi'
    ],
    'Tired': [
        'Energy Smoothie','Banana Shake','Nuts Mix','Dates','Dry Fruits',
        'Protein Shake','Boiled Eggs','Peanut Butter Toast','Whole Grain Bread','Brown Rice Bowl',
        'Lentil Soup','Chicken Soup','Mutton Soup','Vegetable Soup','Fruit Smoothie',
        'Green Smoothie','Detox Juice','Electrolyte Drink','Kanji','Fermented Rice Water',
        'Ragi Malt','Jowar Upma','Bajra Khichdi','Multigrain Paratha','Red Rice Bowl',
        'Quinoa Pulao','Millet Dosa','Buckwheat Khichdi','Amaranth Porridge','Barley Khichdi',
        'Oats Upma','Granola with Curd','Muesli Bowl','Trail Mix','Energy Bars',
        'Protein Bars','Date Bars','Peanut Chikki','Til Chikki','Sesame Ladoo',
        'Dry Fruit Ladoo','Besan Ladoo','Sattu Drink','Sattu Paratha','Sprouts Poha',
        'Paneer Sandwich','Egg Bhurji','Boiled Sweet Corn','Chickpea Salad','Paneer Wrap'
    ],
    'Excited': [
        'Spicy Food Platter','Tangy Salad','Chatpata Mix','Street Style Chaat','Tangy Juice',
        'Spicy Noodles','Bhel Puri','Pani Puri','Masala Fries','Spicy Curry',
        'Mirchi Bajji','Onion Bajji','Potato Bajji','Chilli Chicken','Chilli Paneer',
        'Gobi Manchurian','Baby Corn Manchurian','Veg Manchurian','Chicken Manchurian','Schezwan Noodles',
        'Schezwan Rice','Schezwan Fried Rice','Schezwan Paneer','Hakka Noodles','Manchow Soup',
        'Hot and Sour Soup','Thai Green Curry','Red Curry','Tom Yum Soup','Pad Thai',
        'Drunken Noodles','Basil Fried Rice','Vietnamese Pho','Banh Mi','Spring Rolls',
        'Summer Rolls','Kimchi Fried Rice','Bibimbap','Tteokbokki','Teriyaki Chicken',
        'Teriyaki Paneer','Katsu Curry','Ramen','Udon Stir-fry','Yakitori',
        'Mexican Tacos','Burrito Bowl','Quesadilla','Nachos Supreme','Peri Peri Wrap'
    ],
    'Relaxed': [
        'Warm Soup','Herbal Tea','Light Salad','Steamed Vegetables','Grilled Fish',
        'Boiled Eggs','Fresh Juice','Fruit Bowl','Green Salad','Sprouts',
        'Boiled Corn','Roasted Chicken','White Tea','Oolong Tea','Blooming Tea',
        'Fruit Tea','Decaf Coffee','Golden Milk','Turmeric Latte','Matcha Latte',
        'Smoothie Bowl','Acai Bowl','Porridge','Congee','Clear Broth',
        'Steamed Dumplings','Veg Momos','Spring Rolls','Sushi (Veg)','Cucumber Sushi',
        'Ceviche (veg alt)','Zoodles with Pesto','Crudites with Dip','Hummus Platter','Cheese Board (light)',
        'Fruit Platter','Charcuterie (light)','Antipasto','Mezze Platter','Tapas (light)',
        'Caprese Salad','Greek Salad','Quinoa Bowl','Lemon Coriander Soup','Pumpkin Soup',
        'Corn Soup','Spinach Soup','Tomato Basil Soup','Clear Veg Stew','Khichdi with Ghee'
    ],
    'Anxious': [
        'Chamomile Tea','Warm Milk','Banana','Oats Bowl','Nuts',
        'Seeds','Leafy Greens','Berries','Dark Chocolate (small)','Yogurt',
        'Whole Grains','Lavender Tea','Passionflower Tea','Lemon Balm Tea','Valerian Tea',
        'Magnesium-rich Mix','Zinc-rich Mix','Vitamin B-rich Bowl','Omega-3 Mix','Tryptophan Snack',
        'Complex Carbs Plate','Lean Protein Plate','Healthy Fats Plate','Fermented Foods','Probiotic Yogurt',
        'Prebiotic Salad','Bone Broth (veg alt ok)','Collagen Soup (veg alt)','Arrowroot Porridge','Sabudana Khichdi',
        'Water Chestnut Stir-fry','Lotus Seed (Makhana)','Sunflower Seed Mix','Pumpkin Seed Mix','Flaxseed Mix',
        'Chia Pudding','Hemp Seed Mix','Sesame Mix','Basil (Sabja) Seeds','Fenugreek Water',
        'Coriander Water','Cumin Water','Warm Lemon Water','Ginger Lemon Honey','Sprout Salad',
        'Moong Chilla','Besan Chilla','Veg Dalia','Masala Oats','Spinach Khichdi'
    ],
    'Bored': [
        'Try New Cuisine','Fusion Dish','Unique Smoothie','Creative Buddha Bowl','Food Combo',
        'DIY Taco Night','DIY Sushi (Veg)','DIY Pizza Night','DIY Wrap Bar','Molecular Twist (safe)',
        'Deconstructed Chaat','Reconstructed Dosa','Modernist Raita','Artistic Plating Salad','Edible Flowers Salad',
        'Microgreens Toast','Sprouted Seeds Mix','Wild Greens (safe)','Heirloom Tomato Salad','Ancient Grains Bowl',
        'Heritage Millet Khichdi','Regional Specialty Thali','Seasonal Special Salad','Festival Sweet (light)','Ceremonial Pongal',
        'Prasad Style Sheera','Meditative Kitchari','Yogic Satvic Thali','Ayurvedic Khichdi','Sattvic Pulao',
        'Rajasic Stir-fry (light)','Tamasic Avoid List (info)','Traditional Varieties Platter','Local Street Sampler','Pickle Tasting (mild)',
        'Fermentation Trial (curd)','New Spice Blend Trial','Roast-taste Test','No-recipe Cooking','5-ingredient Challenge',
        'Color-only Plate','Texture-only Plate','Breakfast-for-Dinner','Tapas Flight','Mezze Flight',
        'Pan-Asian Sampler','Tex-Mex Sampler','Middle-East Sampler','Mediterranean Bowl','Korean Bowl'
    ],
}

health_modifiers = {
    'Diabetes': [
        'Sugar-free ','Low-glycemic ','High-fiber ','Diabetic-friendly ','Blood-sugar balancing ',
        'Carb-controlled ','No-added-sugar ','Stevia-sweetened ','Low-carb ','Insulin-sensitive ',
        'Whole-grain ','Vegetable-rich ','Protein-packed ','Low-fat ','Natural-sweetener ',
        'Millet-based ','Brown-rice ','Oats-based ','Barley-based ','Quinoa-based ',
        'Chia-seed ','Flaxseed ','Nut-enriched ','Seed-enriched ','Greek-yogurt ',
        'Low-fat paneer ','Green-tea infused ','Cinnamon-spiced ','Fenugreek-rich ','Bitter-gourd infused ',
        'Drumstick-leaf ','Spinach-rich ','Broccoli-based ','Tomato-based ','Okra-based ',
        'Cabbage-rich ','Cauliflower-based ','Pumpkin-based ','Zucchini-rich ','Brinjal-based ',
        'Carrot-rich ','Beetroot-rich ','Sprouts-rich ','Low-oil ','Air-fried ',
        'Portion-controlled ','Slow-release carbs ','Evenly-balanced plate ','Hydration-focused ','Post-meal walk friendly '
    ],
    'High BP': [
        'Low-sodium ','Potassium-rich ','Heart-healthy ','Hypertension-friendly ','Vasodilating ',
        'Nitric-oxide boosting ','Magnesium-rich ','Calcium-aware ','No-added-salt ','Sodium-aware ',
        'Cardio-friendly ','Cholesterol-lowering ','Triglyceride-reducing ','Anti-hypertensive ','Vascular-friendly ',
        'Nitrate-rich ','Beetroot-enhanced ','Garlic-infused ','Celery-rich ','Pomegranate-enriched ',
        'Berry-infused ','Omega-3 enriched ','CoQ10-aware ','Olive-oil dressed ','Leafy-green loaded ',
        'Whole-grain base ','Legume-forward ','Low-fat dairy ','Herb-seasoned ','Low-sauce ',
        'Steam-cooked ','Grilled ','Baked ','Air-fried ','High-fiber ',
        'Salt-free masala ','Citrus-zest ','Potassium-sodium balance ','Hydrating ','No-pickle ',
        'No-papad add-on ','Low-processed ','No-MSG ','Mindful-portion ','Post-meal relaxation '
    ],
    'Low BP': [
        'Lightly salted ','Healthy salted ','Electrolyte-rich ','Mineral-rich ','Sodium-balanced ',
        'Hydrating ','Volume-supporting ','Energy-dense ','Iron-rich ','B12-rich ',
        'Folate-rich ','Protein-rich ','Healthy-fat rich ','Complex-carb rich ','Calorie-dense ',
        'Banana-added ','Dates-added ','Raisin-enriched ','Salted buttermilk ','Salt-lime water ',
        'Soup-broth ','Veg stew ','Sea-salt pinch ','Rock-salt pinch ','Balanced spice ',
        'Ginger-lime ','Cumin-water ','Jeera rice style ','Beet-carrot mix ','Nuts & seeds ',
        'Egg-protein ','Paneer-protein ','Lentil-forward ','Whole-grain base ','Yogurt-based ',
        'Fermented drink ','Coconut water ','ORS-style homemade ','Small frequent meals ','No long fasting ',
        'Iron + C combo ','Warm beverages ','Avoid sudden standing ','Steady carb release ','Mid-meal snack '
    ],
    'PCOS': [
        'High-fiber ','Low-carb ','Protein-rich ','PCOS-friendly ','Hormone-balancing ',
        'Insulin-sensitive ','Anti-inflammatory ','Antioxidant-rich ','Omega-3 rich ','Low-glycemic ',
        'Blood-sugar stabilizing ','Estrogen-balancing ','Androgen-aware ','Cortisol-balancing ','Thyroid-supporting ',
        'Adrenal-supporting ','Liver-supporting ','Detox-friendly ','Gut-healthy ','Probiotic-rich ',
        'Prebiotic-rich ','Low-dairy focus ','Dairy-free option ','Gluten-aware ','Soy-aware ',
        'Processed-food-free ','Natural ','Whole-food ','Millet-forward ','Legume-forward ',
        'Leafy-green loaded ','Cruciferous blend ','Berry-rich ','Seed-cycling aware ','Zinc-rich ',
        'Magnesium-rich ','Vitamin-D aware ','Inositol-supporting ','Cinnamon-spiced ','Fenugreek hint ',
        'Spearmint-tea pairing ','Steady carb release ','Portion-smart ','Stress-aware timing ','Sleep-supportive '
    ],
    'Thyroid': [
        'Iodine-aware ','Selenium-rich ','Balanced ','Thyroid-supporting ','Hypothyroid-friendly ',
        'Hyperthyroid-friendly ','Goitrogen-aware ','Metabolism-supporting ','Energy-boosting ','Weight-management ',
        'Temperature-regulating ','Hormone-balancing ','Immune-modulating ','Anti-inflammatory ','Antioxidant-rich ',
        'Zinc-rich ','Iron-aware ','Copper-aware ','Manganese-aware ','Vitamin-D aware ',
        'Vitamin-A aware ','Omega-3 rich ','Tyrosine-aware ','Protein-rich ','Amino-acid aware ',
        'Nutrient-dense ','Easy-digesting ','Seafood-aware (or iodized salt) ','Egg-inclusive ','Brazil-nut hint ',
        'Dairy-moderate ','Soy-moderate ','Cruciferous cooked ','Gluten-aware ','Selenium (dal/lentil) ',
        'Millet-moderate ','Hydration focus ','Regular meal timing ','B12 support ','Folate support ',
        'Iron + C combo ','Warm meals ','Less ultra-processed ','Low-sugar ','Whole-grain base '
    ],
    'Weight Loss': [
        'Low-calorie ','High-protein ','Light ','Weight-loss friendly ','Fat-burning ',
        'Metabolism-boosting ','Appetite-managing ','Satiety-promoting ','High-volume ','Water-rich ',
        'Fiber-rich ','Lean-protein ','Low-fat ','Low-sugar ','Low-carb ',
        'Ketogenic-friendly ','Calorie-controlled ','Portion-controlled ','Mindful-eating ','Slow-digesting ',
        'Thermogenic spices ','Fat-oxidizing ','Muscle-preserving ','Non-fried ','Air-fried ',
        'Steam-cooked ','Baked ','Grilled ','No refined sugar ','Whole-food ',
        'Minimal oil ','Millet-forward ','Legume-forward ','Veg-loaded ','Soup-first ',
        'Plate-method ','Walk-after-meal ','Hydration-first ','Protein-first breakfast ','No late-night snacking ',
        'Smart snack ','No sugary drinks ','High-fiber roti ','Brown rice swap ','Quinoa swap '
    ],
    'Heart Issues': [
        'Heart-healthy ','Low-fat ','Cholesterol-aware ','Cardio-friendly ','Artery-friendly ',
        'Omega-3 rich ','Anti-clotting aware ','Blood-pressure friendly ','LDL-lowering style ','HDL-supporting ',
        'Triglyceride-reducing ','Anti-atherosclerotic ','Steady sodium ','High-fiber ','Whole-grain ',
        'Legume-forward ','Olive-oil dressed ','Nuts-in-moderation ','Berries-added ','Leafy-green loaded ',
        'Garlic hint ','Turmeric hint ','Ginger hint ','Low-processed ','Low-sugar ',
        'No trans-fat ','Minimal saturated fat ','Baked/Grilled ','Steam-cooked ','Air-fried ',
        'Portion-smart ','Mediterranean-inspired ','DASH-inspired ','Salt-free masala ','No deep-fry ',
        'Avocado-in-moderation ','Oat-beta-glucan ','Stanols-aware ','CoQ10-aware ','Magnesium-aware ',
        'Potassium-aware ','Vitamin K1 leafy ','Hydration focus ','After-meal walk ','Stress-reduction pair '
    ],
    'None': ['']*50
}

fun_facts = [
    "🍌 Bananas can support a better mood day-to-day.",
    "🥗 Leafy greens are linked with lower stress.",
    "🍫 A small piece of dark chocolate may help you unwind.",
    "🥛 Warm, lightly sweetened milk can feel soothing.",
    "🥣 High-fiber bowls keep energy stable longer."
]

# ---------------- Actions ----------------
st.markdown("<div class='panel'>", unsafe_allow_html=True)
if st.button("🍽️ Get Food Recommendations", type="primary", use_container_width=True):
    if mood in recipes:
        chosen = random.sample(recipes[mood], k=count)
        st.session_state["last"] = []
        for food in chosen:
            mod_food = food
            if health != 'None':
                modifier = random.choice(health_modifiers[health]).strip()
                # presentable: modifier + Title Case food
                mod_food = (modifier + food.lower()).strip()
            st.session_state["last"].append(mod_food)
            st.markdown(
                f"<div class='rec-card'>"
                f"✅ <b>{mod_food}</b>"
                f"<span class='badge'>{mood}</span>"
                f"<span class='badge'>{health}</span><br>"
                f"<small>{random.choice(fun_facts)}</small>"
                f"</div>", unsafe_allow_html=True
            )
            if st.button(f"⭐ Save: {food}", key=f"save_{food}"):
                st.session_state["favorites"].append(mod_food)
                st.success("Added to Favorites!")
    else:
        st.error("Please select a mood to get recommendations")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- Favorites ----------------
with st.expander("💖 View Saved Favorites"):
    if st.session_state["favorites"]:
        for i, fav in enumerate(st.session_state["favorites"], 1):
            st.write(f"{i}. {fav}")
    else:
        st.caption("No favorites yet.")

# ---------------- Search (3D UI) ----------------
with st.expander("🔍 Search Your Own Food (3D Box)"):
    st.markdown("<div class='search-box'>", unsafe_allow_html=True)
    q = st.text_input("Type a dish or ingredient to explore ideas…", help="Example: Paneer wrap, millet dosa, quinoa")
    if q:
        # no external image (as requested). Just a styled acknowledgment.
        st.success(f"Showing ideas around **{q}**. Try combining with your mood/health for smarter picks! 🚀")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("""
    <style>
        :root {
          --primary: #00BFFF;      /* Deep Sky Blue */
          --secondary: #FF7F50;    /* Coral Orange */
          --background: #F0F8FF;   /* Alice Blue (light) */
          --text-dark: #1C1C1C;    /* Dark Charcoal */
          --success: #32CD32;      /* Lime Green */
          --highlight: #FFD700;    /* Golden */
        }

        /* Background */
        body {
            background-color: var(--background);
            color: var(--text-dark);
        }

        /* Headings / Labels */
        h1, h2, h3, h4, h5, h6, label, .stMarkdown p, .stSelectbox label {
            color: var(--primary) !important;
            font-weight: 600 !important;
        }

        /* Links (Saved Favorites, Search Box) */
        .stMarkdown a {
            display: inline-block;
            padding: 8px 14px;
            border: 2px solid var(--primary);
            border-radius: 8px;
            margin: 8px 4px;
            text-decoration: none !important;
            color: var(--primary) !important;
            font-weight: 700;
            background-color: white;
            box-shadow: 2px 2px 6px rgba(0, 191, 255, 0.4);
        }

        .stMarkdown a:hover {
            background-color: var(--primary);
            color: white !important;
            border-color: var(--highlight);
        }

        /* Footer Box */
        .footer-box {
            background-color: white;
            padding: 14px 20px;
            border-radius: 12px;
            box-shadow: 0px 4px 14px rgba(0,0,0,0.15);
            text-align: center;
            margin-top: 35px;
            border: 2px solid var(--secondary);
            font-weight: 700;
            color: var(--text-dark);
        }

        /* Footer Text Strong */
        .footer-box b {
            color: var(--primary);
        }
    </style>
""", unsafe_allow_html=True)


# Example Footer
st.markdown("""
<div class="footer-box">
    🌟 Thanks for using <b>Emobite App</b> • Stay Healthy & Happy 💙
</div>
""", unsafe_allow_html=True)

