# test_app.py
import unittest
from unittest.mock import patch, MagicMock
from app import app, validate_city_param, get_air_quality_level
import json
import os


class WeatherAppTests(unittest.TestCase):
    """Tests for the Weather App application."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment before any tests run."""
        # Mock the environment variable before app is imported
        cls.env_patcher = patch.dict(
            os.environ, {'OPENWEATHER_API_KEY': 'test_api_key'})
        cls.env_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.env_patcher.stop()

    def setUp(self):
        """Set up test client before each test."""
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        """Clean up after each test."""
        pass

    def test_health_check(self):
        """Test that the health check endpoint returns OK status."""
        response = self.app.get('/api/health')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')
        self.assertIn('version', data)

    def test_index_route(self):
        """Test that the index route serves the HTML template."""
        response = self.app.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'Weather Dashboard', response.data)

    def test_static_route(self):
        """Test that static files are served correctly."""
        # We don't use patch here because Flask's test client handles static routes differently
        # Just check if the route exists and returns a proper status code
        response = self.app.get('/static/css/styles.css')
        self.assertEqual(response.status_code, 200)

    def test_weather_endpoint_missing_city(self):
        """Test that the weather endpoint requires a city parameter."""
        response = self.app.get('/api/weather')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'City parameter is required')

    def test_weather_endpoint_invalid_city_format(self):
        """Test that the weather endpoint validates city format."""
        response = self.app.get('/api/weather?city=123')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'Invalid city format')

    @patch('app.requests.get')
    def test_weather_endpoint_success(self, mock_get):
        """Test that the weather endpoint returns formatted data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'name': 'London',
            'sys': {'country': 'GB'},
            'main': {
                'temp': 15.5,
                'feels_like': 14.2,
                'temp_min': 13.8,
                'temp_max': 16.9,
                'humidity': 76,
                'pressure': 1012
            },
            'wind': {'speed': 4.2, 'deg': 250},
            'weather': [{'main': 'Clouds', 'description': 'scattered clouds', 'icon': '03d'}],
            'dt': 1649312400
        }
        mock_get.return_value = mock_response

        response = self.app.get('/api/weather?city=London')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(data['country'], 'GB')
        self.assertEqual(data['temperature']['current'], 15.5)
        self.assertEqual(data['temperature']['feels_like'], 14.2)
        self.assertEqual(data['weather']['description'], 'scattered clouds')
        self.assertEqual(data['weather']['icon'], '03d')

    @patch('app.requests.get')
    def test_weather_endpoint_city_not_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'message': 'city not found'}
        mock_get.return_value = mock_response

        response = self.app.get('/api/weather?city=NonExistentCity')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'city not found')

    @patch('app.requests.get')
    def test_weather_endpoint_network_error(self, mock_get):
        mock_get.side_effect = Exception('Network error')
        response = self.app.get('/api/weather?city=London')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error' in data['error'])

    def test_validate_city_param(self):
        self.assertTrue(validate_city_param('London')[0])
        self.assertTrue(validate_city_param('New York')[0])
        self.assertTrue(validate_city_param('San Francisco, CA')[0])
        self.assertFalse(validate_city_param('')[0])
        self.assertFalse(validate_city_param(None)[0])
        self.assertFalse(validate_city_param('123')[0])
        self.assertFalse(validate_city_param('City#$%')[0])

    def test_get_air_quality_level(self):
        for i in range(1, 6):
            result = get_air_quality_level(i)
            self.assertIn('level', result)
            self.assertIn('description', result)
        result = get_air_quality_level(10)
        self.assertEqual(result['level'], 'Unknown')

    @patch('app.requests.get')
    def test_air_quality_endpoint_success(self, mock_get):
        mock_geo_response = MagicMock()
        mock_geo_response.status_code = 200
        mock_geo_response.json.return_value = [
            {'name': 'London', 'lat': 51.5074, 'lon': -0.1278}
        ]

        mock_air_response = MagicMock()
        mock_air_response.status_code = 200
        mock_air_response.json.return_value = {
            'list': [{
                'main': {'aqi': 2},
                'components': {
                    'co': 230.31,
                    'no': 0.38,
                    'no2': 14.05,
                    'o3': 68.64,
                    'so2': 2.66,
                    'pm2_5': 5.59,
                    'pm10': 9.84,
                    'nh3': 0.51
                },
                'dt': 1649312400
            }]
        }

        def get_side_effect(url, **kwargs):
            if 'geo/1.0/direct' in url:
                return mock_geo_response
            elif 'air_pollution' in url:
                return mock_air_response
            return None

        mock_get.side_effect = get_side_effect

        response = self.app.get('/api/air-quality?city=London')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['city'], 'London')
        self.assertEqual(data['coordinates']['lat'], 51.5074)
        self.assertEqual(data['coordinates']['lon'], -0.1278)
        self.assertEqual(data['air_quality_index'], 2)
        self.assertEqual(data['air_quality_level'], 'Fair')
        self.assertIn('pm2_5', data['components'])
        self.assertIn('pm10', data['components'])

    @patch('app.requests.get')
    def test_air_quality_endpoint_location_not_found(self, mock_get):
        mock_geo_response = MagicMock()
        mock_geo_response.status_code = 200
        mock_geo_response.json.return_value = []
        mock_get.return_value = mock_geo_response

        response = self.app.get('/api/air-quality?city=NonExistentCity')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'Location not found')

    @patch('app.requests.get')
    def test_air_quality_endpoint_no_data(self, mock_get):
        mock_geo_response = MagicMock()
        mock_geo_response.status_code = 200
        mock_geo_response.json.return_value = [
            {'name': 'London', 'lat': 51.5074, 'lon': -0.1278}
        ]

        mock_air_response = MagicMock()
        mock_air_response.status_code = 200
        mock_air_response.json.return_value = {'list': []}

        def get_side_effect(url, **kwargs):
            if 'geo/1.0/direct' in url:
                return mock_geo_response
            elif 'air_pollution' in url:
                return mock_air_response
            return None

        mock_get.side_effect = get_side_effect

        response = self.app.get('/api/air-quality?city=London')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'No air quality data available')

    def test_advanced_weather_processor_missing_data(self):
        response = self.app.post('/api/advanced-weather-processor',
                                 json={},
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            data['error'], 'Weather data and transformation are required')

    def test_advanced_weather_processor_valid_operation(self):
        test_payload = {
            'weather_data': {'temp': 20, 'humidity': 80},
            'transformation': {
                'operation': 'add',
                'parameters': [10, 5]
            }
        }

        response = self.app.post('/api/advanced-weather-processor',
                                 json=test_payload,
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['transformed_data'], 15)
        self.assertEqual(data['original_data'], test_payload['weather_data'])

    def test_advanced_weather_processor_invalid_operation(self):
        test_payload = {
            'weather_data': {'temp': 20, 'humidity': 80},
            'transformation': {
                'operation': 'invalid_op',
                'parameters': [10, 5]
            }
        }

        response = self.app.post('/api/advanced-weather-processor',
                                 json=test_payload,
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertIn('not allowed', data['error'])

    def test_advanced_weather_processor_average_operation(self):
        test_payload = {
            'weather_data': {'temps': [20, 25, 30]},
            'transformation': {
                'operation': 'average',
                'parameters': [[20, 25, 30]]
            }
        }

        response = self.app.post('/api/advanced-weather-processor',
                                 json=test_payload,
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertAlmostEqual(data['transformed_data'], 25.0)

    def test_advanced_weather_processor_round_operation(self):
        test_payload = {
            'weather_data': {'value': 22.76},
            'transformation': {
                'operation': 'round',
                'parameters': [22.76]
            }
        }

        response = self.app.post('/api/advanced-weather-processor',
                                 json=test_payload,
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['transformed_data'], 23)

    def test_advanced_weather_processor_missing_parameters(self):
        test_payload = {
            'weather_data': {'temp': 20},
            'transformation': {
                'operation': 'add'
            }
        }

        response = self.app.post('/api/advanced-weather-processor',
                                 json=test_payload,
                                 content_type='application/json')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 500)
        self.assertIn('Processing failed', data['error'])

    def test_advanced_weather_processor_invalid_json(self):
        response = self.app.post('/api/advanced-weather-processor',
                                 data="not a json",
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
