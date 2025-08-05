import pytest
import requests_mock
from src.services.weather_service import WeatherService
from src.config import Config
from unittest.mock import patch

class TestWeatherService:
    """Test cases for WeatherService."""
    
    @pytest.fixture
    def weather_service(self):
        with patch('src.config.Config.OPENWEATHERMAP_API_KEY', 'test_api_key'):
            return WeatherService()
    
    def test_get_weather_data_success(self, weather_service):
        """Test successful weather data retrieval."""
        with requests_mock.Mocker() as m:
            mock_response = {
                "name": "London",
                "sys": {"country": "GB"},
                "main": {
                    "temp": 15.5,
                    "feels_like": 14.2,
                    "humidity": 78,
                    "pressure": 1013
                },
                "weather": [{"description": "light rain"}],
                "wind": {"speed": 3.5},
                "visibility": 10000
            }
            m.get(Config.WEATHER_API_BASE_URL, json=mock_response)
            
            result = weather_service.get_weather_data("London")
            
            assert result["status"] == "success"
            assert result["city"] == "London"
            assert result["country"] == "GB"
            assert result["temperature"] == 15.5
            assert result["feels_like"] == 14.2
            assert result["humidity"] == 78
            assert result["pressure"] == 1013
            assert result["description"] == "light rain"
            assert result["wind_speed"] == 3.5
            assert result["visibility"] == 10000
    
    def test_get_weather_data_api_error(self, weather_service):
        """Test weather data retrieval with API error."""
        with requests_mock.Mocker() as m:
            m.get(Config.WEATHER_API_BASE_URL, status_code=404)
            
            result = weather_service.get_weather_data("InvalidCity")
            
            assert result["status"] == "error"
            assert "Request failed" in result["error"]
    
    def test_get_weather_data_malformed_response(self, weather_service):
        """Test weather data retrieval with malformed API response."""
        with requests_mock.Mocker() as m:
            m.get(Config.WEATHER_API_BASE_URL, json={"invalid": "data"})

            result = weather_service.get_weather_data("London")
            
            assert result["status"] == "error"
            assert "Unexpected API response format" in result["error"]

    def test_get_weather_data_with_country(self, weather_service):
        """Test weather data retrieval with country specified."""
        with requests_mock.Mocker() as m:
            mock_response = {
                "name": "Paris",
                "sys": {"country": "FR"},
                "main": {"temp": 20, "feels_like": 19, "humidity": 65, "pressure": 1013},
                "weather": [{"description": "clear sky"}],
                "wind": {"speed": 2},
                "visibility": 10000
            }
            m.get(Config.WEATHER_API_BASE_URL, json=mock_response)
            
            result = weather_service.get_weather_data("Paris", "FR")
            
            assert result["status"] == "success"
            assert result["city"] == "Paris"
            assert result["country"] == "FR"   

    def test_format_weather_response_success(self, weather_service):
        """Test weather response formatting for successful data."""
        weather_data = {
            "status": "success",
            "city": "London",
            "country": "GB",
            "temperature": 15.5,
            "feels_like": 14.2,
            "description": "light rain",
            "humidity": 78,
            "pressure": 1013,
            "wind_speed": 3.5,
            "visibility": 10000
        }
        
        formatted = weather_service.format_weather_response(weather_data)
        
        assert "London, GB" in formatted
        assert "15.5°C" in formatted
        assert "feels like 14.2°C" in formatted
        assert "Light Rain" in formatted
        assert "78%" in formatted
        assert "1013 hPa" in formatted
        assert "3.5 m/s" in formatted
        assert "10000 meters" in formatted
    
    def test_format_weather_response_error(self, weather_service):
        """Test weather response formatting for error data."""
        weather_data = {
            "status": "error",
            "error": "City not found"
        }
        
        formatted = weather_service.format_weather_response(weather_data)
        
        assert "Error fetching weather data" in formatted
        assert "City not found" in formatted
    
    def test_format_weather_response_missing_fields(self, weather_service):
        """Test weather response formatting with missing optional fields."""
        weather_data = {
            "status": "success",
            "city": "Berlin",
            "country": "DE",
            "temperature": 18,
            "description": "cloudy",
            "humidity": 65
        }
        
        formatted = weather_service.format_weather_response(weather_data)
        
        assert "Berlin, DE" in formatted
        assert "18°C" in formatted
        assert "Cloudy" in formatted
        assert "65%" in formatted
