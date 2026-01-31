import requests
from config import WEATHER_API_KEY

def get_weather_data(lat, lon):
    """
    Fetch weather data from OpenWeatherMap 5 day / 3 hour forecast API.
    """
    if not WEATHER_API_KEY:
        return {"error": "Weather API key not configured"}

    # OpenWeatherMap Forecast API 2.5
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric"
    
    try:
        print(f"[WEATHER] Fetching weather forecast for lat={lat}, lon={lon}...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print(f"[WEATHER] Response from OpenWeatherMap Forecast: {data}")
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"[WEATHER] HTTP Error: {http_err}")
        return {"error": f"HTTP error occurred: {http_err}"}
    except Exception as err:
        print(f"[WEATHER] Unexpected Error: {err}")
        return {"error": f"Other error occurred: {err}"}
