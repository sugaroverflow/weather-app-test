# test_app.py
import unittest
from unittest.mock import patch, MagicMock
from app import app
import json


class WeatherAppTests(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_check(self):
        response = self.app.get('/api/health')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'ok')

    def test_index_route(self):
        """Test that the index route serves the HTML template"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<!DOCTYPE html>', response.data)
        self.assertIn(b'Weather Dashboard', response.data)

    def test_weather_endpoint_missing_city(self):
        """Test that the weather endpoint requires a city parameter"""
        response = self.app.get('/api/weather')
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], 'City parameter is required')

    @patch('app.requests.get')
    def test_weather_endpoint_success(self, mock_get):
        """Test that the weather endpoint returns formatted data"""
        # Mock the response from OpenWeatherMap API
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

        # Test the endpoint
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
        """Test that the weather endpoint handles city not found errors"""
        # Mock the response for city not found
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {'message': 'city not found'}
        mock_get.return_value = mock_response

        # Test the endpoint
        response = self.app.get('/api/weather?city=NonExistentCity')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['error'], 'city not found')

    @patch('app.requests.get')
    def test_weather_endpoint_network_error(self, mock_get):
        """Test that the weather endpoint handles network errors"""
        # Mock a network error
        mock_get.side_effect = Exception('Network error')

        # Test the endpoint
        response = self.app.get('/api/weather?city=London')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 500)
        self.assertTrue('Server error' in data['error'])


if __name__ == '__main__':
    unittest.main()
