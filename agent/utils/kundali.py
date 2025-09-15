from vedastro import *
from geopy.geocoders import Nominatim
from timezonefinderL import TimezoneFinder
import pytz
def geocode_place_timezone(place_name: str):
    try:
        geolocator = Nominatim(user_agent="astro_ai_app",timeout=10)
        location = geolocator.geocode(place_name)
        if location:
            lat,lon = float(location.latitude),float(location.longitude)
            print(".....",lat,lon)
            # tzwhere_obj = tzwhere.tzwhere()
            # timezone_str = tzwhere_obj.tzNameAt(lat, lon)
            # print(timezone_str)
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=77.2090, lat=28.6139)
            print(timezone_str)  # Asia/Kolkata
            if timezone_str:
                tz = pytz.timezone(timezone_str)
                return lat, lon, tz
    except Exception as e:
        print("Geocoding error:", e)
        return None, None,None
    
def kundali_generate(data):
    try:
        # Step 1: Validate input data
        required_keys = ['Date', 'Time', 'place']
        if not all(key in data for key in required_keys):
            raise ValueError(f"Missing required keys in birth data: {required_keys}")

        # Step 2: Geocode place and get timezone
        lat, lon, tz = geocode_place_timezone(data['place'])

        # Step 3: Format time string
        date = data['Date'].replace("-", "/")
        time_str = f"{data['Time']} {date} {tz}"

        # Step 4: Create GeoLocation and Time objects
        geolocation = GeoLocation(data['place'], lon, lat)
        time_obj = Time(time_str, geolocation)
        print("Time Object:", time_obj)  # Debug

        # Step 5: Calculate Kundali components
        # Planets (Navagraha)
        planets = [PlanetName.Sun, PlanetName.Moon, PlanetName.Mars, PlanetName.Mercury, 
                   PlanetName.Jupiter, PlanetName.Venus, PlanetName.Saturn, PlanetName.Rahu, 
                   PlanetName.Ketu]
        planet_data = {}
        for planet in planets:
            data = Calculate.AllPlanetData(planet, time_obj)
            planet_data[str(planet)] = {
                'longitude': float(data.get('Longitude', 0.0)),
                'sign': str(data.get('Sign', 'Unknown')),
                'shadbala': float(data.get('Shadbala', 0.0)),
                'is_retrograde': bool(data.get('IsRetrograde', False))
            }

        # Houses (1-12)
        house_data = {}
        for house_num in range(1, 13):
            house = HouseName[f"House{house_num}"]
            data = Calculate.AllHouseData(house, time_obj)
            house_data[f"House{house_num}"] = {
                'sign': str(data.get('Sign', 'Unknown')),
                'lord': str(data.get('Lord', 'Unknown'))
            }

        # Zodiac Signs
        signs = [ZodiacName.Aries, ZodiacName.Taurus, ZodiacName.Gemini, ZodiacName.Cancer, 
                 ZodiacName.Leo, ZodiacName.Virgo, ZodiacName.Libra, ZodiacName.Scorpio, 
                 ZodiacName.Sagittarius, ZodiacName.Capricorn, ZodiacName.Aquarius, ZodiacName.Pisces]
        zodiac_data = {}
        for sign in signs:
            data = Calculate.AllZodiacSignData(sign, time_obj)
            zodiac_data[str(sign)] = {
                'ruling_planet': str(data.get('RulingPlanet', 'Unknown')),
                'element': str(data.get('Element', 'Unknown'))
            }

        # Step 6: Summarize result
        result = {
            'name': data.get('Name', 'Unknown'),
            'birth_time': time_str,
            'place': data['place'],
            'planet_data': planet_data,
            'house_data': house_data,
            'zodiac_data': zodiac_data
        }

        return result

    except Exception as e:
        print(f"Error in generate_kundali: {str(e)}")
        return None
    
    
    
from django.http import JsonResponse
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
AI_API_KEY = os.getenv('AI_API_KEY')
genai.configure(api_key=AI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def kundali_report(person):
    # Build system prompt
    system_prompt = f"""
    You are Astro AI, an expert astrologer.
    Create a kundali for following person:

    Person:
    - Name: {person['Name']}
    - Birth Date: {person['Date']}
    - Birth Time: {person['Time']}
    - Birth Place: {person['place']}

    Provide a kundali analysis in terms of:
    - Love & Relationship
    - Career/Partnership
    - Emotional Connection
    - Long-term Potential

    End with an overall compatibility score (0-100%).
    """
    try:
        response = model.generate_content(system_prompt)
        return response.text
    except Exception as e:
        kundali_report(person)