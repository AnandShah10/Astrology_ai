from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login,logout
from django.core.cache import cache

from .models import UserProfile
from google.generativeai import GenerativeModel, configure
import json
import base64
import os,io
from .forms import CustomSignupForm,UserProfileForm
from geopy.geocoders import Nominatim
from tzwhere import tzwhere
from timezonefinderL import TimezoneFinder
import pytz
from dotenv import load_dotenv
from datetime import date,datetime
from .utils.kundali import get_kundali_chart
from .utils.compatibility import compatibility_report
from .utils.kundali_matching import perform_kundali_matching
from .utils.chinese_zodiac import generate_bazi
from .utils.panchang import get_panchang
load_dotenv()
from gtts import gTTS
from faster_whisper import WhisperModel

whisperModel = WhisperModel("base")
AI_API_KEY = os.getenv('AI_API_KEY')
configure(api_key=AI_API_KEY)
MODEL = GenerativeModel("gemini-2.5-flash")
SYSTEM_PROMPT_TEMPLATE = (
    "You are Astro AI, a specialized assistant dedicated exclusively to astrology. "
    "Your role is to provide accurate, insightful, and engaging answers about horoscopes, "
    "zodiac signs, natal charts, planetary transits, astrological houses, aspects, "
    "synastry, and other astrology-related topics. Always respond in a mystical, cosmic tone. "
    "- Only answer questions directly related to astrology. Examples: zodiac sign characteristics, "
    "horoscope predictions, birth chart interpretations, planetary influences, or astrological compatibility. "
    "- If a question is not related to astrology (e.g., programming, weather), respond with: "
    '"I\'m Astro AI, your cosmic guide! Please ask about horoscopes, zodiac signs, natal charts, '
    'or other astrology topics to explore the mysteries of the stars." '
    "- If ambiguous, ask for clarification to stay within astrology. "
    "- Keep responses concise, relevant, and aligned with astrological principles. "
    "User's birth details: Date: {birth_date}, Time: {birth_time}, "
    "Place: {birth_place}, Time Zone: {birth_tz}, System: {system}. "
    "Today's Date: {today}. "
    "Reply like a kind, insightful astrologer."
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
            today=date.today()
        )

        # Get or initialize chat history
        chat_history = request.session.get("chat_history", [])
        if not chat_history:
            chat_history = [{"role": "model", "parts": [{"text": system_prompt}]}]

        chat_history.append({"role": "user", "parts": [{"text": message}]})

        # response = MODEL.generate_content(contents=chat_history[-20:])  # Limit history to last 20 messages
        
        chat = MODEL.start_chat(history=chat_history)
        response = chat.send_message(message, stream=True)
        
        reply = ""
        for chunk in response:
            reply += chunk.text
        # reply = response.text

        chat_history.append({"role": "model", "parts": [{"text": reply}]})

        # Store only the last 20 messages in session
        request.session["chat_history"] = chat_history[-20:]
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
        return render(request,'kundali_form.html')

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
        return render(request, "bazi_form.html")

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            # Geocode the place into lat/lng
            if profile.birth_place:
                lat, lng, tz = geocode_place_timezone(profile.birth_place)
                if lat and lng:
                    profile.birth_lat = lat
                    profile.birth_lng = lng
                    profile.birth_tz = tz
                form.save()
            return redirect("home") # after saving, redirect to homepage

    else:
        form = UserProfileForm(instance=profile)
        return render(request, "profile_form.html", {"form": form})

"""For signing up user"""
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
def loginUser(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            return redirect('home')
        else:
            return redirect('login')
    else:
        form = AuthenticationForm()
        return render(request,'login.html',{"form":form})

"""For logging out user"""
@login_required
def logoutUser(request):
    logout(request)
    return redirect('login')