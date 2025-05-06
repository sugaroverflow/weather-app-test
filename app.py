# app.py
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import os
import re
import json
from dotenv import load_dotenv
from urllib.parse import urlparse
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Initialize Flask application
app = Flask(__name__)

# Get API key from environment variables
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

if not OPENWEATHER_API_KEY:
    # For demo purposes, we'll set a placeholder
    OPENWEATHER_API_KEY = "your_api_key_here"
    print(
        "Warning: No OpenWeatherMap API key found. Please set the OPENWEATHER_API_KEY environment variable."
    )

# CONSTANTS
ALLOWED_OPERATIONS = {
    "add": lambda x, y: x + y,
    "subtract": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "divide": lambda x, y: x / y if y != 0 else None,
    "average": lambda x: sum(x) / len(x) if x else None,
    "max": max,
    "min": min,
    "round": round,
}

AQI_LEVELS = [
    {
        "level": "Good",
        "description": "Air quality is satisfactory, and air pollution poses little or no risk.",
    },
    {
        "level": "Fair",
        "description": "Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.",
    },
    {
        "level": "Moderate",
        "description": "Members of sensitive groups may experience health effects. The general public is less likely to be affected.",
    },
    {
        "level": "Poor",
        "description": "Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.",
    },
    {
        "level": "Very Poor",
        "description": "Health alert: The risk of health effects is increased for everyone.",
    },
]


# Helper functions
def _is_valid_url(url):
    """
    Validate URL to prevent SSRF attacks.

    Args:
        url (str): The URL to validate

    Returns:
        bool: True if the URL is valid and safe, False otherwise
    """
    try:
        # Parse the URL
        parsed_url = urlparse(url)

        # Ensure the URL uses http or https protocol
        if parsed_url.scheme not in ["http", "https"]:
            return False

        # Ensure the URL doesn't point to internal/private networks
        hostname = parsed_url.netloc

        # Block localhost and private IPs
        private_networks = [
            "127.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.2",
            "172.3",
            "192.168.",
            "localhost",
            ".local",
        ]

        if any(
            hostname.startswith(prefix) for prefix in private_networks
        ) or hostname.endswith(".local"):
            return False

        # Ensure we're only making requests to openweathermap.org
        if not hostname.endswith("openweathermap.org"):
            return False

        return True
    except Exception:
        return False


def require_api_key(f):
    """
    Decorator to check if API key is valid.

    Args:
        f (function): The function to decorate

    Returns:
        function: The decorated function that checks for a valid API key
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if OPENWEATHER_API_KEY == "your_api_key_here":
            return (
                jsonify(
                    {
                        "error": "No valid API key provided. Please set your API key in the .env file."
                    }
                ),
                401,
            )
        return f(*args, **kwargs)

    return decorated_function


def validate_city_param(city):
    """
    Validate the city parameter.

    Args:
        city (str): The city name to validate

    Returns:
        tuple: (is_valid, error_message)
            - is_valid (bool): True if the city is valid, False otherwise
            - error_message (str or None): Error message if validation fails, None otherwise
    """
    if not city:
        return False, "City parameter is required"

    # Basic validation of city parameter (letters, spaces, commas, etc)
    if not re.match(r"^[a-zA-Z\s,.-]+$", city):
        return False, "Invalid city format"

    return True, None


def get_air_quality_level(aqi):
    """
    Get air quality level based on AQI index (1-5).

    Args:
        aqi (int): Air Quality Index (1-5)

    Returns:
        dict: Dictionary containing 'level' and 'description' of the air quality
    """
    if 1 <= aqi <= 5:
        return AQI_LEVELS[aqi - 1]
    return {
        "level": "Unknown",
        "description": "Air quality information is not available.",
    }


# Route to serve the frontend HTML page
@app.route("/")
def index():
    """
    Serve the main index page.

    Returns:
        rendered template: The main index.html template
    """
    return render_template("index.html", openweather_api_key=OPENWEATHER_API_KEY)


# Route to serve static files
@app.route("/static/<path:filename>")
def serve_static(filename):
    """
    Serve static files from the static directory.

    Args:
        filename (str): Path to the static file

    Returns:
        file: The requested static file
    """
    # Make sure this is called with exactly 'static' and filename as arguments
    # to match the test's expectations
    return send_from_directory("static", filename)


# API endpoint for retrieving current weather data
@app.route("/api/weather", methods=["GET"])
@require_api_key
def get_weather():
    """
    Get current weather data for a specified city.

    Query Parameters:
        city (str): The name of the city to get weather data for

    Returns:
        JSON: Weather data for the specified city or error message
    """
    # Extract city from query parameters
    city = request.args.get("city")

    # Validate input
    is_valid, error_message = validate_city_param(city)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    try:
        # First, get coordinates for the city
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"

        # Validate geo URL before making request
        if not _is_valid_url(geo_url):
            return jsonify({"error": "Invalid geocoding request URL"}), 400

        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()

        # Check if location was found
        if not geo_data:
            return jsonify({"error": "Location not found"}), 404

        # Extract coordinates with proper error checking
        try:
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
        except (IndexError, KeyError) as e:
            return jsonify({"error": "Could not extract location coordinates"}), 500

        # Construct URL for OpenWeatherMap API using coordinates
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"

        # Validate URL before making request
        if not _is_valid_url(weather_url):
            return jsonify({"error": "Invalid request URL"}), 400

        # Make request to external API
        weather_response = requests.get(weather_url, timeout=10)
        weather_data = weather_response.json()

        # Handle API error responses
        if weather_response.status_code != 200:
            return (
                jsonify(
                    {
                        "error": weather_data.get(
                            "message", "Failed to fetch weather data"
                        )
                    }
                ),
                weather_response.status_code,
            )

        # Transform API response into application-specific format
        formatted_response = {
            "city": weather_data["name"],
            "country": weather_data["sys"]["country"],
            "coordinates": {
                "lat": lat,
                "lon": lon
            },
            "temperature": {
                "current": weather_data["main"]["temp"],
                "feels_like": weather_data["main"]["feels_like"],
                "min": weather_data["main"]["temp_min"],
                "max": weather_data["main"]["temp_max"],
            },
            "humidity": weather_data["main"]["humidity"],
            "pressure": weather_data["main"]["pressure"],
            "wind": {
                "speed": weather_data["wind"]["speed"],
                # Use get() with default to handle missing data
                "degrees": weather_data.get("wind", {}).get("deg", 0),
            },
            "weather": {
                "main": weather_data["weather"][0]["main"],
                "description": weather_data["weather"][0]["description"],
                "icon": weather_data["weather"][0]["icon"],
            },
            # Unix timestamp of data calculation time
            "timestamp": weather_data["dt"],
        }

        # Return formatted weather data as JSON
        return jsonify(formatted_response)

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (connection issues, timeouts, etc.)
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        # Catch-all for other unexpected errors
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# New API endpoint for 5-day forecast
@app.route("/api/forecast", methods=["GET"])
@require_api_key
def get_forecast():
    """
    Get 5-day forecast data for a specified city.

    Query Parameters:
        city (str): The name of the city to get forecast data for

    Returns:
        JSON: Forecast data for the specified city or error message
    """
    # Extract city from query parameters
    city = request.args.get("city")

    # Validate input
    is_valid, error_message = validate_city_param(city)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    try:
        # Construct URL for OpenWeatherMap 5-day forecast API
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"

        # Validate URL before making request
        if not _is_valid_url(forecast_url):
            return jsonify({"error": "Invalid request URL"}), 400

        # Make request to external API
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_response.json()

        # Handle API error responses
        if forecast_response.status_code != 200:
            return (
                jsonify(
                    {
                        "error": forecast_data.get(
                            "message", "Failed to fetch forecast data"
                        )
                    }
                ),
                forecast_response.status_code,
            )

        # Group forecast by day
        daily_forecasts = {}

        for item in forecast_data["list"]:
            # Get date from timestamp (without time)
            date = item["dt_txt"].split(" ")[0]

            if date not in daily_forecasts:
                daily_forecasts[date] = {
                    "date": date,
                    "temps": [],
                    "weather": [],
                    "humidity": [],
                    "wind_speed": [],
                }

            # Append data for aggregation
            daily_forecasts[date]["temps"].append(item["main"]["temp"])
            daily_forecasts[date]["weather"].append(
                {
                    "main": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                }
            )
            daily_forecasts[date]["humidity"].append(item["main"]["humidity"])
            daily_forecasts[date]["wind_speed"].append(item["wind"]["speed"])

        # Transform daily data (calculate averages, select most frequent weather condition)
        formatted_forecasts = []

        for date, data in daily_forecasts.items():
            # Calculate average temperature and round to 1 decimal
            avg_temp = round(sum(data["temps"]) / len(data["temps"]), 1)

            # Get the most frequent weather condition
            weather_counts = {}
            for w in data["weather"]:
                icon = w["icon"]
                if icon not in weather_counts:
                    weather_counts[icon] = 0
                weather_counts[icon] += 1

            most_frequent_icon = max(weather_counts.items(), key=lambda x: x[1])[0]
            most_frequent_weather = next(
                w for w in data["weather"] if w["icon"] == most_frequent_icon
            )

            # Calculate average humidity and wind speed
            avg_humidity = round(sum(data["humidity"]) / len(data["humidity"]))
            avg_wind_speed = round(sum(data["wind_speed"]) / len(data["wind_speed"]), 1)

            # Format the forecast for this day
            formatted_forecast = {
                "date": date,
                "temp": avg_temp,
                "weather": most_frequent_weather,
                "humidity": avg_humidity,
                "wind_speed": avg_wind_speed,
            }

            formatted_forecasts.append(formatted_forecast)

        # Sort forecasts by date and limit to 5 days
        formatted_forecasts.sort(key=lambda x: x["date"])
        formatted_forecasts = formatted_forecasts[:5]

        # Return the formatted response
        return jsonify(
            {
                "city": forecast_data["city"]["name"],
                "country": forecast_data["city"]["country"],
                "forecasts": formatted_forecasts,
            }
        )

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except Exception as e:
        # Catch-all for other unexpected errors
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# Advanced endpoint for custom weather data processing
@app.route("/api/advanced-weather-processor", methods=["POST"])
@require_api_key
def process_weather_data():
    """
    Process weather data with custom transformations.

    This endpoint allows users to apply predefined operations to weather data.

    Request Body:
        JSON object containing:
        - weather_data (object): The weather data to process
        - transformation (object): Object with 'operation' and 'parameters' fields
            - operation (str): One of the allowed operations
            - parameters (list): Parameters for the operation

    Returns:
        JSON: Original and transformed weather data
    """
    try:
        # Handle invalid JSON payload
        try:
            data = request.get_json()
            if (
                data is None
            ):  # This will catch when request.get_json() returns None for invalid JSON
                return jsonify({"error": "Invalid JSON payload"}), 400
        except Exception:
            # Explicit handling for invalid JSON
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Check if required data is present
        weather_data = data.get("weather_data")
        transformation = data.get("transformation")

        if not weather_data or not transformation:
            return (
                jsonify({"error": "Weather data and transformation are required"}),
                400,
            )

        # Process with the safer dictionary-based transformations approach
        if isinstance(transformation, dict):
            # Create a context with the weather data
            context = {"data": weather_data, "result": None}

            operation = transformation.get("operation")
            parameters = transformation.get("parameters", [])

            if operation not in ALLOWED_OPERATIONS:
                raise ValueError(
                    f"Operation '{operation}' not allowed. Allowed operations: {', '.join(ALLOWED_OPERATIONS.keys())}"
                )

            # Execute the transformation safely
            context["result"] = ALLOWED_OPERATIONS[operation](*parameters)

            return jsonify(
                {
                    "original_data": weather_data,
                    "transformed_data": context.get("result"),
                }
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Invalid transformation format. Must be a dictionary with operation and parameters"
                    }
                ),
                400,
            )

    except ValueError as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


# Implementation for the air quality endpoint with efficient processing and proper error handling
@app.route("/api/air-quality", methods=["GET"])
@require_api_key
def get_air_quality():
    """
    Get air quality data for a specified city.

    Query Parameters:
        city (str): The name of the city to get air quality data for

    Returns:
        JSON: Air quality data for the specified city including AQI and pollutant levels,
              or error message
    """
    # Extract city from query parameters
    city = request.args.get("city")

    # Validate input
    is_valid, error_message = validate_city_param(city)
    if not is_valid:
        return jsonify({"error": error_message}), 400

    try:
        # First, get coordinates for the city
        geo_url = f"https://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"

        # Validate geo URL before making request
        if not _is_valid_url(geo_url):
            return jsonify({"error": "Invalid geocoding request URL"}), 400

        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()

        # Check if location was found
        if not geo_data:
            return jsonify({"error": "Location not found"}), 404

        # Extract coordinates with proper error checking
        try:
            lat = geo_data[0]["lat"]
            lon = geo_data[0]["lon"]
        except (IndexError, KeyError) as e:
            return jsonify({"error": "Could not extract location coordinates"}), 500

        # Construct URL for OpenWeatherMap Air Pollution API
        air_quality_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"

        # Validate air quality URL
        if not _is_valid_url(air_quality_url):
            return jsonify({"error": "Invalid air quality request URL"}), 400

        # Make request to external API
        air_quality_response = requests.get(air_quality_url, timeout=10)

        # Check response status
        if air_quality_response.status_code != 200:
            return (
                jsonify({"error": "Failed to fetch air quality data"}),
                air_quality_response.status_code,
            )

        air_quality_data = air_quality_response.json()

        # Check if data exists in the response
        if "list" not in air_quality_data or not air_quality_data["list"]:
            return jsonify({"error": "No air quality data available"}), 404

        # Get the latest air quality data
        latest_data = air_quality_data["list"][0]

        # Efficient data processing - use lookup function
        aqi = latest_data["main"]["aqi"]
        aqi_info = get_air_quality_level(aqi)

        # Efficient property extraction
        components = latest_data.get("components", {})

        # Transform API response into application-specific format efficiently
        formatted_response = {
            "city": city,
            "coordinates": {"lat": lat, "lon": lon},
            "air_quality_index": aqi,
            "air_quality_level": aqi_info["level"],
            "air_quality_description": aqi_info["description"],
            "components": components,
            "timestamp": latest_data.get("dt"),
        }

        # Return formatted air quality data as JSON
        return jsonify(formatted_response)

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        return jsonify({"error": f"Network error: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        # Handle JSON parsing errors
        return (
            jsonify({"error": f"Invalid response from weather service: {str(e)}"}),
            500,
        )
    except Exception as e:
        # Catch-all for other unexpected errors
        return jsonify({"error": f"Server error: {str(e)}"}), 500


# Health check endpoint for monitoring and load balancers
@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for monitoring service status.

    Returns:
        JSON: Service status and version information
    """
    return jsonify({"status": "ok", "version": "1.1.0"}), 200


# Run the application if executed directly
if __name__ == "__main__":
    # Use environment variables if available, otherwise use defaults
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")

    app.run(debug=debug_mode, host=host, port=port)
