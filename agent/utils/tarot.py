from django.http import JsonResponse
import google.generativeai as genai
from dotenv import load_dotenv
import os,random
from .. import models
load_dotenv()
AI_API_KEY = os.getenv('AI_API_KEY')
genai.configure(api_key=AI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

def get_ai_interpretation(spread, spread_type="3-card"):
    """
    spread = list of dicts: [{"position": "Past", "name": "The Fool", "orientation": "Upright", "meaning": "..."}]
    """
    prompt = f"""
    You are a professional tarot reader.
    The user drew a {spread_type} tarot spread with these cards:

    {spread}

    Please write a meaningful interpretation:
    - Connect the cards together (not just separate meanings).
    - Explain the story of Past, Present, Future.
    - Be clear, warm, and inspiring.
    """

    response = model.generate_content(prompt)
    return response.text.strip()

def draw_card(req):
    card = random.choice(models.TarotCard.objects.all())
    reversed_state = random.choice([True, False])

    data = {
        "name": card.name,
        "suit": card.suit,
        "orientation": "Reversed" if reversed_state else "Upright",
        "meaning": card.meaning_reversed if reversed_state else card.meaning_upright,
        "image": req.build_absolute_uri(card.image.url)
    }

    interpretation = get_ai_interpretation([data], spread_type="single card")

    return {
        "card": data,
        "interpretation": interpretation
    }

def three_card_spread(request):
    cards = random.sample(list(models.TarotCard.objects.all()), 3)
    positions = ["Past", "Present", "Future"]
    spread = []

    for i, card in enumerate(cards):
        reversed_state = random.choice([True, False])
        spread.append({
            "position": positions[i],
            "name": card.name,
            "suit": card.suit,
            "orientation": "Reversed" if reversed_state else "Upright",
            "meaning": card.meaning_reversed if reversed_state else card.meaning_upright,
            "image": request.build_absolute_uri(card.image.url)
        })

    interpretation = get_ai_interpretation(spread, spread_type="3-card")

    return {
        "spread": spread,
        "interpretation": interpretation
    }