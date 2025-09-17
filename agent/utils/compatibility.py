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
        
