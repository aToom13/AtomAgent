import os
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@tool
def get_weather(city: str) -> str:
    """
    Get current weather information for a specific city.
    
    Args:
        city: Name of the city (e.g., "Istanbul", "London")
        
    Returns:
        Weather report string
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return "❌ OpenWeatherMap API key format bulunamadı. Lütfen .env dosyasına OPENWEATHERMAP_API_KEY ekleyin."
    
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric",
        "lang": "tr"
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            
            return (
                f"🌍 **{city.title()} Hava Durumu**\n"
                f"🌡️ Sıcaklık: {temp}°C\n"
                f"☁️ Durum: {weather_desc.capitalize()}\n"
                f"💧 Nem: %{humidity}\n"
                f"💨 Rüzgar: {wind_speed} m/s"
            )
        elif response.status_code == 404:
            return f"❌ Şehir bulunamadı: {city}"
        else:
            return f"❌ Hava durumu alınırken hata oluştu: {data.get('message', 'Bilinmeyen hata')}"
            
    except Exception as e:
        return f"❌ Bağlantı hatası: {str(e)}"
