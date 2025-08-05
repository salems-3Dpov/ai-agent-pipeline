import requests
import json
from typing import Dict, Optional
from src.config import Config

class WeatherService:
    """Service for fetching real-time weather data from OpenWeatherMap API."""
    
    def __init__(self):
        if not Config.OPENWEATHERMAP_API_KEY:
            raise ValueError("OPENWEATHERMAP_API_KEY is required for WeatherService")
        self.api_key = Config.OPENWEATHERMAP_API_KEY
        self.base_url = Config.WEATHER_API_BASE_URL

    
    def get_weather_data(self, city: str, country: Optional[str] = None) -> Dict:
        """Fetch weather data for a given city."""
        try:
            # Construct the query parameter
            query = city
            if country:
                query += f",{country}"
            
            params = {
                'q': query,
                'appid': self.api_key,
                'units': 'metric'  # Use Celsius
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate required fields
            if not all(key in data for key in ['name', 'sys', 'main', 'weather']):
                return {
                    'status': 'error',
                    'error': "Unexpected API response format: missing required fields"
                }
                
            if not isinstance(data['weather'], list) or len(data['weather']) == 0:
                return {
                    'status': 'error',
                    'error': "Unexpected API response format: invalid weather data"
                }
            
            # Extract relevant weather information
            weather_info = {
                'status': 'success',
                'city': data['name'],
                'country': data['sys']['country'],
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'wind_speed': data.get('wind', {}).get('speed', 'N/A'),
                'visibility': data.get('visibility', 'N/A')
            }
            
            return weather_info
            
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f"Unexpected error: {str(e)}"
            }

        
    def format_weather_response(self, weather_data: Dict) -> str:
        """Format weather data into a human-readable string."""
        if weather_data['status'] == 'error':
            return f"Error fetching weather data: {weather_data['error']}"
        
        # Build response with fallbacks for missing fields
        response_lines = [
            f"Weather Information for {weather_data['city']}, {weather_data['country']}:",
            f"🌡️ Temperature: {weather_data['temperature']}°C"
        ]
        
        if weather_data.get('feels_like', 'N/A') != 'N/A':
            response_lines.append(f" (feels like {weather_data['feels_like']}°C)")
        
        response_lines.extend([
            f"🌤️ Condition: {weather_data['description'].title()}",
            f"💧 Humidity: {weather_data['humidity']}%"
        ])
        
        if weather_data.get('pressure', 'N/A') != 'N/A':
            response_lines.append(f"📊 Pressure: {weather_data['pressure']} hPa")
        
        if weather_data.get('wind_speed', 'N/A') != 'N/A':
            response_lines.append(f"💨 Wind Speed: {weather_data['wind_speed']} m/s")
        
        if weather_data.get('visibility', 'N/A') != 'N/A':
            response_lines.append(f"👁️ Visibility: {weather_data['visibility']} meters")
        
        return "\n".join(response_lines)