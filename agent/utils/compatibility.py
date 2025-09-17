from django.http import JsonResponse
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
AI_API_KEY = os.getenv('AI_API_KEY')
genai.configure(api_key=AI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def compatibility_report(person1,person2):
    # Build system prompt
    system_prompt = f"""
    You are Astro AI, an expert astrologer.
    Compare the following two individuals for compatibility:

    Person A:
    - Name: {person1['Name']}
    - Birth Date: {person1['Date']}
    - Birth Time: {person1['Time']}
    - Birth Place: {person1['Place']}

    Person B:
    -Name: {person2['Name']}
    - Birth Date: {person2['Date']}
    - Birth Time: {person2['Time']}
    - Birth Place: {person2['Place']}

    Provide a compatibility analysis in terms of:
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
        compatibility_report(person1,person2)
        
# This is a conceptual example, as the exact function names may vary
# depending on the library you use.
from geopy.geocoders import Nominatim
from timezonefinderL import TimezoneFinder
import pytz
def geocode_place_timezone(place_name: str):
    try:
        geolocator = Nominatim(user_agent="astro_ai_app",timeout=10)
        location = geolocator.geocode(place_name)
        if location:
            lat,lon = float(location.latitude),float(location.longitude)
            # tzwhere_obj = tzwhere.tzwhere()
            # timezone_str = tzwhere_obj.tzNameAt(lat, lon)
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=77.2090, lat=28.6139)
            if timezone_str:
                tz = pytz.timezone(timezone_str)
                return lat, lon, tz
    except Exception as e:
        return None, None,None

from vedastro import *
def perform_kundali_matching(p1_birth_data, p2_birth_data):
    """
    Performs Kundali matching using the Ashtakoota Milan system.
    
    Args:
        p1_name (str): Name of the first person.
        p1_birth_data (dict): Dictionary with keys 'date', 'time', 'lat', 'lon', 'timezone'.
        p2_name (str): Name of the second person.
        p2_birth_data (dict): Dictionary with keys 'date', 'time', 'lat', 'lon', 'timezone'.
        
    Returns:
        dict: A dictionary containing the compatibility score and a detailed report.
    """
    lat1,lon1,tz1 = geocode_place_timezone(p1_birth_data['Place'])
    lat2,lon2,tz2 = geocode_place_timezone(p2_birth_data['Place'])
    # Create Time objects for both individuals
    p1_time_obj = Time(
        f"{p1_birth_data['Time']} {p1_birth_data['Date'].replace("-", "/")} {tz1}",
        GeoLocation(tz1, lat1, lon1)
    )

    p2_time_obj = Time(
        f"{p2_birth_data['Time']} {p2_birth_data['Date'].replace("-", "/")} {tz2}",
        GeoLocation(tz2, lat2, lon2)
    )
    # Get the compatibility report
    match_report = Calculate.MatchReport(p1_time_obj, p2_time_obj)

    # Extracting the total score and individual Koota scores 

    koota_names = ['Varna', 'Vashya', 'Tara', 'Yoni', 'Graha Maitri', 'Gana', 'Bhakoot', 'Nadi']
    max_scores = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]  # Standard Ashtakoota max scores
    embeddings = match_report.get('Embeddings', [])
    if len(embeddings) != 8:
        raise ValueError("Embeddings array does not contain 8 Kuta scores")
    koota_breakdown = {}
    for i, (name, score, max_score) in enumerate(zip(koota_names, embeddings, max_scores)):
        koota_breakdown[name] = {
                'score': float(score),
                'max_score': float(max_score)
            }

    # Step 8: Extract total score and additional predictions
    total_score = float(match_report.get('KutaScore', sum(embeddings)))
    prediction_list = match_report.get('PredictionList', [])
    additional_predictions = [
            {'Name': pred['Name'], 'Nature': pred['Nature'], 'Description': pred['Description']}
            for pred in prediction_list if pred['Name'] not in koota_names and pred['Name'] != 'Empty'
        ]

        # Step 9: Summarize result
    result = {
            'total_score': total_score,
            'match_status': ("Best Match" if total_score >= 32 else
                            "Good Match" if total_score >= 18 else
                            "Average Match" if total_score >= 10 else
                            "Poor Match"),
            'koota_breakdown': koota_breakdown,
            'additional_predictions': additional_predictions
        }
    return result
