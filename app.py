from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
import os
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed to use sessions

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"  # Update with your MongoDB URI
client = MongoClient(MONGO_URI)
db = client['travel_db']  # Database name
users_collection = db['users']  # Collection for user data

# Define paths and API keys
json_file_path = os.path.join(app.static_folder, 'maharashtra_cities.json')

# Load the JSON file
if not os.path.exists(json_file_path):
    raise FileNotFoundError(f"The file {json_file_path} does not exist")

with open(json_file_path) as json_file:
    try:
        cities_weather_data = json.load(json_file)
        if not isinstance(cities_weather_data, dict):
            raise ValueError("The JSON data is not in the expected format.")
    except json.JSONDecodeError as e:
        raise ValueError("Error decoding JSON file") from e

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        email = request.form.get('username')
        password = request.form.get('password')
        user = users_collection.find_one({'email': email, 'password': password})
        if user:
            session['user_id'] = str(user['_id'])
            session['username'] = user['first_name']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login2.html', error="Invalid email or password.")
    return render_template('login2.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        password = request.form.get('password')
        travel_preferences = request.form.get('travelPreferences')

        # Check if user already exists
        if users_collection.find_one({'email': email}):
            return render_template('register2.html', error="Email already exists.")

        try:
            # Insert new user
            user_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'password': password,  # Remember to hash passwords in a real application
                'travel_preferences': travel_preferences
            }
            result = users_collection.insert_one(user_data)
            session['user_id'] = str(result.inserted_id)
            session['username'] = first_name
            return redirect(url_for('dashboard'))
        except Exception as e:
            return render_template('register2.html', error="An error occurred while registering.")
        
    return render_template('register2.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Render the dashboard and provide city-based weather recommendations and package options."""
    weather_data = None
    recommendations = None
    username = session.get('username', 'Guest')

    if request.method == 'POST':
        budget = request.form.get('budget', type=int)
        if budget is not None:
            recommendations = get_package_recommendations(budget)
    
    return render_template('dashboard.html', username=username, weather_data=weather_data, recommendations=recommendations)

def get_package_recommendations(budget):
    """
    Get package recommendations based on budget for all cities.
    """
    recommendations = []
    for city, data in cities_weather_data.items():
        packages = data.get('packages', {})
        city_recommendations = {
            'city': city,
            'temperature': data.get('temperature', 'N/A'),
            'humidity': data.get('humidity', 'N/A'),
            'wind_speed': data.get('wind_speed', 'N/A'),
            'packages': {
                pkg: price for pkg, price in packages.items() if price is not None and budget >= price
            }
        }
        if city_recommendations['packages']:
            recommendations.append(city_recommendations)
    return recommendations

@app.route('/service')
def service():
    """Display the service page."""
    return render_template('service.html')

@app.route('/about')
def about():
    """Display the about page."""
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
