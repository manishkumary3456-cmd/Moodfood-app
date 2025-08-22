import streamlit as st
import random

# --- SEO SETTINGS START ---
st.set_page_config(
    page_title="MoodFood Health App - Personalized Food Recommendations Based on Mood & Health",
    page_icon="🥗",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Adding meta tags for Google
st.markdown("""
<meta name="description" content="Get personalized food recommendations based on your current mood and health conditions. MoodFood helps you find the perfect meals for happiness, stress, depression, diabetes, BP, and more." />
<meta name="keywords" content="mood food, health food, food recommendations, diet planner, mental health nutrition, diabetes diet, blood pressure diet, healthy recipes, personalized nutrition, mood-based diet, health condition food" />
<meta name="author" content="Manish Yadav" />
<meta name="robots" content="index, follow" />
""", unsafe_allow_html=True)

# Structured data for SEO (JSON-LD)
st.markdown("""
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebApplication",
  "name": "MoodFood Health App",
  "description": "Personalized food recommendations based on mood and health conditions",
  "applicationCategory": "HealthApplication",
  "operatingSystem": "Web Browser",
  "author": {
    "@type": "Person",
    "name": "Manish Yadav"
  },
  "offers": {
    "@type": "Offer",
    "price": "0",
    "priceCurrency": "USD"
  }
}
</script>
""", unsafe_allow_html=True)
# --- SEO SETTINGS END ---

# --- APP CONTENT START ---
# Header with H1 tag for SEO
st.title("MoodFood Health App")
st.subheader("Personalized Food Recommendations Based on Your Mood & Health Conditions")

# Main content
st.write("""
Discover the perfect meals tailored to your emotional state and health requirements. 
Our AI-powered recommendations help you eat better for both mental and physical well-being.
""")

# Create two columns for mood and health selection
col1, col2 = st.columns(2)

with col1:
    st.header("How are you feeling today?")
    mood = st.selectbox(
        "Select your mood:",
        ['Happy', 'Stressed', 'Sad/Depressed', 'Anxious', 'Tired', 'Energetic', 'Relaxed']
    )

with col2:
    st.header("Any health conditions?")
    health_condition = st.selectbox(
        "Select health condition:",
        ['None', 'Diabetes', 'High Blood Pressure', 'Low Blood Pressure', 'PCOS', 'Thyroid', 'Heart Disease', 'Weight Loss']
    )

# Recipe database with health considerations
recipes = {
    'Happy': {
        'None': ['Colorful Veggie Pasta', 'Fruit Salad', 'Ice Cream Sandwich'],
        'Diabetes': ['Berry Yogurt Bowl', 'Vegetable Stir Fry', 'Sugar-free Smoothie'],
        'High Blood Pressure': ['Banana Oatmeal', 'Leafy Green Salad', 'Baked Salmon'],
        'Low Blood Pressure': ['Saltine Crackers', 'Cheese Sandwich', 'Nut Mix'],
        'PCOS': ['Cinnamon Oatmeal', 'Flaxseed Smoothie', 'Vegetable Omelette'],
        'Thyroid': ['Brazil Nut Trail Mix', 'Grilled Chicken', 'Seaweed Salad'],
        'Heart Disease': ['Oatmeal with Berries', 'Baked Fish', 'Steamed Vegetables'],
        'Weight Loss': ['Green Salad', 'Grilled Chicken', 'Vegetable Soup']
    },
    'Stressed': {
        'None': ['Herbal Tea', 'Dark Chocolate', 'Oatmeal'],
        'Diabetes': ['Chamomile Tea', 'Sugar-free Hot Chocolate', 'Nuts'],
        'High Blood Pressure': ['Magnesium-rich Foods', 'Leafy Greens', 'Yogurt'],
        'Low Blood Pressure': ['Salty Snacks', 'Cheese', 'Olives'],
        'PCOS': ['Stress-reducing Tea', 'Complex Carbs', 'Lean Proteins'],
        'Thyroid': ['Selenium-rich Foods', 'Zinc-rich Foods', 'Vitamin B-rich Foods'],
        'Heart Disease': ['Low-sodium Soup', 'Fresh Fruits', 'Whole Grains'],
        'Weight Loss': ['Green Tea', 'Apple Slices', 'Carrot Sticks']
    },
    'Sad/Depressed': {
        'None': ['Comfort Food', 'Chicken Soup', 'Mashed Potatoes'],
        'Diabetes': ['Sugar-free Comfort Food', 'Vegetable Soup', 'Greek Yogurt'],
        'High Blood Pressure': ['Low-sodium Soup', 'Baked Sweet Potato', 'Fresh Fruits'],
        'Low Blood Pressure': ['Comfort Food with Salt', 'Cheesy Dishes', 'Pickles'],
        'PCOS': ['Omega-3 Rich Foods', 'Complex Carbs', 'Lean Proteins'],
        'Thyroid': ['Iron-rich Foods', 'Vitamin D Foods', 'Omega-3 Foods'],
        'Heart Disease': ['Heart-healthy Comfort Food', 'Steamed Vegetables', 'Fresh Salad'],
        'Weight Loss': ['Low-calorie Comfort Food', 'Vegetable Broth', 'Grilled Chicken']
    },
    'Anxious': {
        'None': ['Chamomile Tea', 'Dark Chocolate', 'Oatmeal'],
        'Diabetes': ['Herbal Tea', 'Nuts', 'Greek Yogurt'],
        'High Blood Pressure': ['Banana', 'Leafy Greens', 'Yogurt'],
        'Low Blood Pressure': ['Salty Snacks', 'Cheese', 'Olives'],
        'PCOS': ['Complex Carbs', 'Lean Proteins', 'Healthy Fats'],
        'Thyroid': ['Brazil Nuts', 'Seafood', 'Dairy Products'],
        'Heart Disease': ['Oatmeal', 'Fresh Fruits', 'Vegetables'],
        'Weight Loss': ['Green Tea', 'Apple', 'Carrot Sticks']
    },
    'Tired': {
        'None': ['Energy Smoothie', 'Nuts and Seeds', 'Banana Shake'],
        'Diabetes': ['Sugar-free Smoothie', 'Nuts', 'Greek Yogurt'],
        'High Blood Pressure': ['Banana', 'Leafy Greens', 'Oatmeal'],
        'Low Blood Pressure': ['Salty Snacks', 'Cheese', 'Olives'],
        'PCOS': ['Complex Carbs', 'Lean Proteins', 'Healthy Fats'],
        'Thyroid': ['Brazil Nuts', 'Seafood', 'Dairy Products'],
        'Heart Disease': ['Oatmeal', 'Fresh Fruits', 'Vegetables'],
        'Weight Loss': ['Green Tea', 'Apple', 'Carrot Sticks']
    },
    'Energetic': {
        'None': ['Spicy Tacos', 'Energy Bites', 'Avocado Toast'],
        'Diabetes': ['Vegetable Stir Fry', 'Nuts', 'Greek Yogurt'],
        'High Blood Pressure': ['Banana', 'Leafy Greens', 'Oatmeal'],
        'Low Blood Pressure': ['Salty Snacks', 'Cheese', 'Olives'],
        'PCOS': ['Complex Carbs', 'Lean Proteins', 'Healthy Fats'],
        'Thyroid': ['Brazil Nuts', 'Seafood', 'Dairy Products'],
        'Heart Disease': ['Oatmeal', 'Fresh Fruits', 'Vegetables'],
        'Weight Loss': ['Green Salad', 'Grilled Chicken', 'Vegetable Soup']
    },
    'Relaxed': {
        'None': ['Mashed Potatoes', 'Oatmeal', 'Comfort Food'],
        'Diabetes': ['Sugar-free Dessert', 'Vegetable Soup', 'Greek Yogurt'],
        'High Blood Pressure': ['Low-sodium Soup', 'Baked Sweet Potato', 'Fresh Fruits'],
        'Low Blood Pressure': ['Comfort Food with Salt', 'Cheesy Dishes', 'Pickles'],
        'PCOS': ['Omega-3 Rich Foods', 'Complex Carbs', 'Lean Proteins'],
        'Thyroid': ['Iron-rich Foods', 'Vitamin D Foods', 'Omega-3 Foods'],
        'Heart Disease': ['Heart-healthy Comfort Food', 'Steamed Vegetables', 'Fresh Salad'],
        'Weight Loss': ['Low-calorie Comfort Food', 'Vegetable Broth', 'Grilled Chicken']
    }
}

# Display recommendation
if st.button("Get Food Recommendation"):
    if mood in recipes and health_condition in recipes[mood]:
        recommendations = recipes[mood][health_condition]
        selected_recipe = random.choice(recommendations) if isinstance(recommendations, list) else recommendations
        
        st.success(f"### Recommended for you: {selected_recipe}")
        
        # Explanation
        st.write(f"""
        **Why this recommendation?**
        - **Mood ({mood}):** This food helps balance your emotional state
        - **Health ({health_condition}):** This choice considers your dietary needs
        """)
    else:
        st.warning("Please select both mood and health condition for personalized recommendations.")

# Additional SEO content
st.markdown("---")
st.markdown("""
### Why Choose MoodFood Health App?

- **Personalized Recommendations:** Get food suggestions based on both mood and health conditions
- **Health-Conscious:** All recommendations consider dietary restrictions and health needs
- **Science-Backed:** Our suggestions are based on nutritional science and health research
- **Free Forever:** No charges, no subscriptions - completely free service

### Popular Searches
Mood-based diet | Health condition food recommendations | Diabetes diet plan | Blood pressure foods | 
PCOS diet | Thyroid nutrition | Mental health food | Emotional eating solutions | 
Personalized nutrition | Healthy eating guide
""")

# Footer
st.markdown("---")
st.markdown("""
*MoodFood Health App - Eating well for mind and body. Created by Manish Yadav.*
""")
# --- APP CONTENT END ---