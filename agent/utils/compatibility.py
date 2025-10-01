# import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
# AI_API_KEY = os.getenv('AI_API_KEY')
# genai.configure(api_key=AI_API_KEY)
# model = genai.GenerativeModel("gemini-2.5-flash")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
from openai import AzureOpenAI
endpoint = os.getenv("ENDPOINT_URL", "https://jivihireopenai.openai.azure.com/")
client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=OPENAI_API_KEY,
        api_version="2024-05-01-preview",
    )

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
        # response = model.generate_content(system_prompt)
        # return response.text
        response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
        messages= [{"role": "user", "content": system_prompt}],
        temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        compatibility_report(person1,person2)
        
