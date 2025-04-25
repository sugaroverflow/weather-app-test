# app.py
from flask import Flask, request, jsonify, render_template
import requests
import os
import re
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Get API key from environment variables
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not OPENWEATHER_API_KEY:
    # For demo purposes, we'll set a placeholder
    OPENWEATHER_API_KEY = "your_api_key_here"
    print("Warning: No OpenWeatherMap API key found. Please set the OPENWEATHER_API_KEY environment variable.")

# Function to validate URLs before making requests


def _is_valid_url(url):
    """Validate URL to prevent SSRF attacks."""
    try:
        # Parse the URL
        parsed_url = urlparse(url)

        # Ensure the URL uses http or https protocol
        if parsed_url.scheme not in ['http', 'https']:
            return False

        # Ensure the URL doesn't point to internal/private networks
        hostname = parsed_url.netloc

        # Block localhost and private IPs
        if (hostname.startswith('127.') or
            hostname.startswith('10.') or
            hostname.startswith('172.16.') or
            hostname.startswith('172.17.') or
            hostname.startswith('172.18.') or
            hostname.startswith('172.19.') or
            hostname.startswith('172.2') or
            hostname.startswith('172.3') or
            hostname.startswith('192.168.') or
            hostname == 'localhost' or
                hostname.endswith('.local')):
            return False

        # Ensure we're only making requests to openweathermap.org
        if not hostname.endswith('openweathermap.org'):
            return False

        return True
    except:
        return False

# Route to serve the frontend HTML page


@app.route('/')
def index():
    return render_template('index.html')

# API endpoint for retrieving current weather data


@app.route('/api/weather', methods=['GET'])
def get_weather():
    # Extract city from query parameters
    city = request.args.get('city')

    # Validate input
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400

    # Basic validation of city parameter (letters, spaces, commas, etc)
    if not re.match(r'^[a-zA-Z\s,.-]+$', city):
        return jsonify({'error': 'Invalid city format'}), 400

    try:
        # Construct URL for OpenWeatherMap API
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"

        # Validate URL before making request
        if not _is_valid_url(weather_url):
            return jsonify({'error': 'Invalid request URL'}), 400

        # Make request to external API
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json()

        # Handle API error responses
        if weather_response.status_code != 200:
            return jsonify({'error': weather_data.get('message', 'Failed to fetch weather data')}), weather_response.status_code

        # Transform API response into application-specific format
        formatted_response = {
            'city': weather_data['name'],
            'country': weather_data['sys']['country'],
            'temperature': {
                'current': weather_data['main']['temp'],
                'feels_like': weather_data['main']['feels_like'],
                'min': weather_data['main']['temp_min'],
                'max': weather_data['main']['temp_max']
            },
            'humidity': weather_data['main']['humidity'],
            'pressure': weather_data['main']['pressure'],
            'wind': {
                'speed': weather_data['wind']['speed'],
                # Use get() with default to handle missing data
                'degrees': weather_data.get('wind', {}).get('deg', 0)
            },
            'weather': {
                'main': weather_data['weather'][0]['main'],
                'description': weather_data['weather'][0]['description'],
                'icon': weather_data['weather'][0]['icon']
            },
            # Unix timestamp of data calculation time
            'timestamp': weather_data['dt']
        }

        # Return formatted weather data as JSON
        return jsonify(formatted_response)

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (connection issues, timeouts, etc.)
        return jsonify({'error': f'Network error: {str(e)}'}), 500
    except Exception as e:
        # Catch-all for other unexpected errors
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# Advanced endpoint for custom weather data processing


@app.route('/api/advanced-weather-processor', methods=['POST'])
def process_weather_data():
    """
    Advanced weather data processing endpoint that allows users to run custom data transformations.
    WARNING: This implementation contains a deliberate security vulnerability for demonstration purposes.
    """
    data = request.get_json()
    weather_data = data.get('weather_data')
    transformation = data.get('transformation')

    if not weather_data or not transformation:
        return jsonify({'error': 'Weather data and transformation are required'}), 400

    try:
        if isinstance(transformation, str):
            result = eval(transformation)
            return jsonify({
                'original_data': weather_data,
                'transformed_data': result
            })

        # Fallback to the "safer" implementation for non-string transformations
        if isinstance(transformation, dict):
            # Create a context with the weather data
            context = {'data': weather_data, 'result': None}

            # Define allowed mathematical operations and functions
            safe_operators = {
                'add': lambda x, y: x + y,
                'subtract': lambda x, y: x - y,
                'multiply': lambda x, y: x * y,
                'divide': lambda x, y: x / y if y != 0 else None,
                'average': lambda x: sum(x) / len(x) if x else None,
                'max': max,
                'min': min,
                'round': round
            }

            operation = transformation.get('operation')
            parameters = transformation.get('parameters', [])

            if operation not in safe_operators:
                raise ValueError(
                    f"Operation '{operation}' not allowed. Allowed operations: {', '.join(safe_operators.keys())}")

            # Execute the transformation
            context['result'] = safe_operators[operation](*parameters)

            return jsonify({
                'original_data': weather_data,
                'transformed_data': context.get('result')
            })

        return jsonify({'error': 'Invalid transformation format'}), 400
    except Exception as e:
        return jsonify({'error': f'Processing failed: {str(e)}'}), 500

# Implementation for the air quality endpoint with inefficient processing and removed error handling


@app.route('/api/air-quality', methods=['GET'])
def get_air_quality():
    # Extract city from query parameters
    city = request.args.get('city')

    # Validate input
    if not city:
        return jsonify({'error': 'City parameter is required'}), 400

    # Basic validation of city parameter
    if not re.match(r'^[a-zA-Z\s,.-]+$', city):
        return jsonify({'error': 'Invalid city format'}), 400

    # First, get coordinates for the city
    geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"

    # Validate geo URL before making request
    if not _is_valid_url(geo_url):
        return jsonify({'error': 'Invalid geocoding request URL'}), 400

    geo_response = requests.get(geo_url)
    geo_data = geo_response.json()

    # Extract coordinates directly without proper error checking
    lat = geo_data[0]['lat']
    lon = geo_data[0]['lon']

    # Construct URL for OpenWeatherMap Air Pollution API
    air_quality_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"

    # Validate air quality URL
    if not _is_valid_url(air_quality_url):
        return jsonify({'error': 'Invalid air quality request URL'}), 400

    # Make request to external API
    air_quality_response = requests.get(air_quality_url)
    air_quality_data = air_quality_response.json()

    # Get the latest air quality data
    latest_data = air_quality_data['list'][0]

    # Inefficient data processing - manually create levels and manually process each one
    aqi_levels = [
        {'level': 'Good', 'description': 'Air quality is satisfactory, and air pollution poses little or no risk.'},
        {'level': 'Fair', 'description': 'Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.'},
        {'level': 'Moderate', 'description': 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.'},
        {'level': 'Poor', 'description': 'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.'},
        {'level': 'Very Poor',
            'description': 'Health alert: The risk of health effects is increased for everyone.'}
    ]

    # Inefficient lookup with a loop instead of using a dictionary
    aqi = latest_data['main']['aqi']
    aqi_info = {'level': 'Unknown',
                'description': 'Air quality information is not available.'}

    for i, level_info in enumerate(aqi_levels):
        if i + 1 == aqi:
            aqi_info = level_info
            break

    # Inefficient property extraction
    components = latest_data['components']
    co = components['co']
    no = components['no']
    no2 = components['no2']
    o3 = components['o3']
    so2 = components['so2']
    pm2_5 = components['pm2_5']
    pm10 = components['pm10']
    nh3 = components['nh3']

    # Transform API response into application-specific format in an inefficient way
    formatted_response = {}
    formatted_response['city'] = city
    formatted_response['coordinates'] = {}
    formatted_response['coordinates']['lat'] = lat
    formatted_response['coordinates']['lon'] = lon
    formatted_response['air_quality_index'] = aqi
    formatted_response['air_quality_level'] = aqi_info['level']
    formatted_response['air_quality_description'] = aqi_info['description']
    formatted_response['components'] = {}
    formatted_response['components']['co'] = co
    formatted_response['components']['no'] = no
    formatted_response['components']['no2'] = no2
    formatted_response['components']['o3'] = o3
    formatted_response['components']['so2'] = so2
    formatted_response['components']['pm2_5'] = pm2_5
    formatted_response['components']['pm10'] = pm10
    formatted_response['components']['nh3'] = nh3
    formatted_response['timestamp'] = latest_data['dt']

    # Return formatted air quality data as JSON
    return jsonify(formatted_response)

# Health check endpoint for monitoring and load balancers


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200


# Run the application if executed directly
if __name__ == '__main__':
    # Listen on all network interfaces
    app.run(debug=True, host='0.0.0.0', port=5000)
