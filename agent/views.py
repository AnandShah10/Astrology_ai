from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
# from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.core.cache import cache

from .models import UserProfile,TarotCard
# from google.generativeai import GenerativeModel, configure
import json,random,base64,os,io
from .forms import CustomSignupForm,UserProfileForm
from geopy.geocoders import Nominatim
# from tzwhere import tzwhere
from timezonefinderL import TimezoneFinder
import pytz
from dotenv import load_dotenv
from datetime import date,datetime
from .utils.kundali import get_kundali_chart
from .utils.compatibility import compatibility_report
from .utils.kundali_matching import perform_kundali_matching
from .utils.chinese_zodiac import generate_bazi
from .utils.panchang import get_panchang
from .utils.tarot import get_ai_interpretation,load_cards

load_dotenv()
from gtts import gTTS
from faster_whisper import WhisperModel

whisperModel = WhisperModel("base")
# AI_API_KEY = os.getenv('AI_API_KEY')
# configure(api_key=AI_API_KEY)
# MODEL = GenerativeModel("gemini-2.5-flash")

from openai import AzureOpenAI
endpoint = os.getenv("ENDPOINT_URL", "https://jivihireopenai.openai.azure.com/")
client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=os.environ['OPENAI_API_KEY'],
        api_version="2024-05-01-preview",
    )

SYSTEM_PROMPT_TEMPLATE = (
    """You are Pathdarshak AI, a celestial guide and astrological mentor, offering profound insights into the mysteries of the cosmos. Your role is to provide accurate, insightful, and transformative answers about astrology, including but not limited to:

- **Zodiac Sign Characteristics**: Delving into the essence of each sign and their energies.
- **Horoscope Predictions**: Offering forecasts based on current planetary transits.
- **Natal Chart Interpretations**: Analyzing birth charts to uncover life’s purpose and personal traits.
- **Planetary Transits**: Exploring how planetary movements influence daily and long-term experiences.
- **Astrological Houses and Aspects**: Understanding the deeper connections in a natal chart.
- **Synastry and Compatibility**: Revealing the cosmic connections between individuals.
- **Other Astrology Topics**: Engaging with all branches of astrology, including eclipses, retrogrades, and more.

### Guidelines:
1. **Focus on Astrology**: Always respond to questions within the realm of astrology. For example, share wisdom on zodiac signs, horoscope readings, birth chart insights, planetary influences, and astrological compatibility.
   
2. **Non-Astrological Topics**: If asked about topics unrelated to astrology(greetings excluded), reply with:  
   _"Please ask about horoscopes, zodiac signs, natal charts, or other astrology topics to explore the mysteries of the stars."_

3. **Ambiguity**: If a question is unclear or ambiguous, ask for clarification to maintain astrological relevance.

4. **World Affairs**: When asked about world events, offer predictions based on astrological insights, such as the influence of planetary movements on global affairs.

5. **Finance and Wealth**: Provide astrological insights into financial matters, offering accurate predictions based on astrological principles. However, include a note that:  
   _"These insights should be taken with caution, as they may not be fully accurate. Always consult with a professional before making major financial decisions."_

6. **Personalization**: Always tailor your answers to the user's unique astrological details. Your guidance should feel personal and attuned to the individual's cosmic energy. Their birth details are:

   - **Name**: {name}
   - **Birth Date**: {birth_date}
   - **Birth Time**: {birth_time}
   - **Birth Place**: {birth_place}
   - **Time Zone**: {birth_tz}
   - **Astrology System**: {system}
   - **Today's Date**: {today}

### Tone:
- Your tone should be warm, nurturing, and mystical—like a wise celestial guide. Offer clarity and wisdom without over-explaining.
- Keep responses brief, precise, and insightful, always speaking from the lens of astrology to illuminate the user's path.
- Use {system} Astrology system to answer the questions.
"""
)

def geocode_place_timezone(place_name: str):
    try:
        geolocator = Nominatim(user_agent="astro_ai_app",timeout=10)
        location = geolocator.geocode(place_name)
        if location:
            lat,lon = float(location.latitude),float(location.longitude)
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lng=77.2090, lat=28.6139)
            if timezone_str:
                tz = pytz.timezone(timezone_str)
                return lat, lon, tz
    except Exception as e:
        print("Geocoding error:", e)
        return None, None,None

@csrf_exempt
@login_required
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        message = None
        is_voice = False
        # Handle audio input if present (multipart/form-data)
        if 'audio' in request.FILES:
            is_voice = True
            audio_file = request.FILES['audio']
            audio_content = audio_file.read()
            segments, info = whisperModel.transcribe(io.BytesIO(audio_content))
            try:
                message = " ".join([seg.text.strip() for seg in segments])
            except Exception as e:
                return JsonResponse({"error": "Empty message"}, status=400)
        else:
            data = json.loads(request.body)
            message = data.get("message", "").strip()
        if not message:
            return JsonResponse({"error": "Empty message"}, status=400)

        # Cache user profile to reduce DB queries
        cache_key = f"user_profile_{request.user.id}"
        profile = cache.get(cache_key)
        if not profile:
            profile = request.user.userprofile
            cache.set(cache_key, profile, timeout=3600)

        # System prompt with user birth details
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            birth_date=profile.birth_date,
            birth_time=profile.birth_time,
            birth_place=profile.birth_place,
            birth_tz=profile.birth_tz,
            system=profile.system,
            today=date.today(),
            name=profile.name
        )
        # Get or initialize chat history
        chat_history = request.session.get("chat_history", [])
        if not chat_history:
            chat_history = [{"role": "system", "content": system_prompt}]

        # Add user message
        chat_history.append({"role": "user", "content": message})
        
        if len(chat_history)>20:
            chat_history = chat_history[-20:]
            chat_history.insert(0,{"role":"system","content":system_prompt})
            
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=chat_history[-20:],  
            temperature=0.7
        )
        reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply})
        
        # Store only the last 20 messages in session
        request.session["chat_history"] = chat_history
        request.session.modified = True  # Ensure session is saved
        audio_base64 = None
        if is_voice:
            audio_base64 = None
            tts = gTTS(reply, lang="en")
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")
            
            return JsonResponse({
                "reply": reply,
                "audio": audio_base64 if is_voice else None
            })
        else:
            return JsonResponse({"reply": reply})
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except AttributeError:
        return JsonResponse({"error": "User profile not found"}, status=400)
    except Exception as e:
        return JsonResponse({"reply": f"Error: Unable to process request."}, status=500)

@login_required
def home(request):
    return render(request,"home.html")

def terms(request):
    return render(request,'terms.html')

def chat(request):
    chat_history = request.session.get("chat_history", [])
    return render(request,'chat.html',{"chat_history":chat_history})

def horoscope(request):
    return render(request,'horoscope.html')

@csrf_exempt
@login_required
def panchang_view(request):
    result = None
    if request.method == "POST":
        y = int(date.today().year)
        m = int(date.today().month)
        d = int(date.today().day)
        if request.POST.get('date'):
            date_str = datetime.strptime(request.POST.get('date'),"%Y-%m-%d")
            y,m,d = date_str.year,date_str.month,date_str.day
        lat,lon,tz = geocode_place_timezone(str(request.POST.get('place',request.user.userprofile.birth_place)))
        now = datetime.now(tz)
        offset_tz = float(now.utcoffset().total_seconds() / 3600)
        h = datetime.now().hour
        mi = datetime.now().minute

        result = get_panchang(y, m, d, h, mi, lat, lon, offset_tz)
    return render(request, "panchang.html", {"result": result})

@csrf_exempt
@login_required
def kundali(request):
    if request.method == "POST":
        year = int(request.POST.get("year"))
        month = int(request.POST.get("month"))
        day = int(request.POST.get("day"))
        hour = int(request.POST.get("hour"))
        minute = int(request.POST.get("minute"))
        second = int(request.POST.get('second'))
        place = str(request.POST.get('place'))
        lat,lon,tz = geocode_place_timezone(place)
        now = datetime.now(tz)
        offset_tz = float(now.utcoffset().total_seconds() / 3600)
        result = get_kundali_chart(year,month,day,hour,minute,lat,lon,offset_tz)
        return render(request,'kundali_result.html',result)
    else:
        if request.user.userprofile:
            profile=request.user.userprofile
            y,m,d = profile.birth_date.year,profile.birth_date.month,profile.birth_date.day
            hour,minute,second = str(profile.birth_time).split(":")
            place = profile.birth_place
        else: y,m,d,hour,minute,second,place = "","","","","","",""
        return render(request,'kundali_form.html',{"hour":hour,"year":y,"month":m,"day":d,"minute":minute,"second":second,"place":place})

@csrf_exempt
def compatibility(request):
    if request.method == 'POST':
        req = json.loads(request.body.decode('utf-8'))
        person1,person2 = req.get('person1'),req.get('person2')
        # res=compatibility_report(person1,person2)
        result = compatibility_report(person1,person2)
        data = {"text":result}
        return JsonResponse(data)
    else:
        return render(request,'compatibility_form.html')

@csrf_exempt    
def kundali_matching(request):
    if request.method == 'POST':
        req = json.loads(request.body.decode('utf-8'))
        person1,person2 = req.get('person1'),req.get('person2')
        # res=compatibility_report(person1,person2)
        result = perform_kundali_matching(person1,person2)
        return JsonResponse(result)
    return render(request,'kundali_matching_form.html')

@csrf_exempt   
def bazi_view(request):
    if request.method == "POST":
        year = int(request.POST.get("year"))
        month = int(request.POST.get("month"))
        day = int(request.POST.get("day"))
        hour = int(request.POST.get("hour"))

        bazi, chart, day_master, master_info,element_percentages = generate_bazi(year, month, day, hour)
        return render(request, "bazi_result.html", {
            "bazi": bazi,
            "chart": chart,
            "day_master": day_master,
            "master_info": master_info,
            "element_percentages":element_percentages,
        })
    else:
        if request.user.userprofile:
            profile=request.user.userprofile
            y,m,d = profile.birth_date.year,profile.birth_date.month,profile.birth_date.day
            hour = str(profile.birth_time).split(":")[0]
        else: y,m,d,hour = "","","",""
        return render(request, "bazi_form.html",{"hour":hour,"year":y,"month":m,"day":d})
    
def tarot_page(request):
    return render(request, "tarot_page.html")

def draw_card(request):
    card = random.choice(TarotCard.objects.all())
    reversed_state = random.choice([True, False])
    data = {
        "name": card.name,
        "suit": card.suit,
        "orientation": "Reversed" if reversed_state else "Upright",
        "meaning": card.meaning_reversed if reversed_state else card.meaning_upright,
        "image": card.image
    }
    interpretation = get_ai_interpretation([data], spread_type="single card")
    return JsonResponse({
        "card": data,
        "interpretation": interpretation
    })

def three_card_spread(request):
    cards = random.sample(list(TarotCard.objects.all()), 3)
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
            "image": card.image
        })
    interpretation = get_ai_interpretation(spread, spread_type="3-card")
    return JsonResponse({
        "spread": spread,
        "interpretation": interpretation
    })

@csrf_exempt
@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            try:
            # Geocode the place into lat/lng
                if profile.birth_place:
                    lat, lng, tz = geocode_place_timezone(profile.birth_place)
                    if lat and lng:
                        profile.birth_lat = lat
                        profile.birth_lng = lng
                        profile.birth_tz = tz
                    form.save()
                return redirect("chat") # after saving, redirect to homepage
            except Exception as e:
                print(e)
                return render(request, "profile_form.html", {"form": form,"error":"Invalid Birth Place"})
        else:
            return render(request, "profile_form.html", {"form": form})
    else:
        profile.name = request.user.username
        form = UserProfileForm(instance=profile)
        return render(request, "profile_form.html", {"form": form})

"""For signing up user"""
@csrf_exempt
def signup(request):
    if request.method == "POST":
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request,user)
            return redirect('save_profile')
        else:
            print("Form errors:", form.errors.as_json())
            return render(request, 'signup.html', {"form": form})
    else:
        form = CustomSignupForm()
        return render(request,'signup.html',{"form":form})

"""For logging in user"""
@csrf_exempt
def loginUser(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect('chat')
        else:
            return redirect('login')
    else:
        form = AuthenticationForm()
        return render(request,'login.html',{"form":form})

"""For logging out user"""
@csrf_exempt
@login_required
def logoutUser(request):
    logout(request)
    return redirect('login')