# yourapp/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import generics
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .models import UserProfile
from .serializers import UserProfileSerializer,PanchangSerializer
from datetime import date,datetime
import os
from google.generativeai import GenerativeModel, configure
from dotenv import load_dotenv
from .utils.kundali import get_kundali_chart
from .utils.compatibility import compatibility_report
from .utils.kundali_matching import perform_kundali_matching
from .utils.chinese_zodiac import generate_bazi
from .views import geocode_place_timezone
from .utils.panchang import get_panchang
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
load_dotenv()
AI_API_KEY = os.getenv('AI_API_KEY')
configure(api_key=AI_API_KEY)
MODEL = GenerativeModel("gemini-2.5-flash")

# ==================== Chat API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    message = request.data.get("message", "").strip()
    if not message:
        return Response({"error": "Empty message"}, status=400)

    profile = getattr(request.user, 'userprofile', None)
    if not profile:
        return Response({"error": "User profile not found"}, status=400)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        birth_date=profile.birth_date,
        birth_time=profile.birth_time,
        birth_place=profile.birth_place,
        birth_tz=profile.birth_tz,
        system=profile.system,
        today=date.today()
    )

    chat_history = request.session.get("chat_history", [])
    if not chat_history:
        chat_history = [{"role": "model", "parts": [{"text": system_prompt}]}]

    chat_history.append({"role": "user", "parts": [{"text": message}]})

    # response = MODEL.generate_content(contents=chat_history[-20:])
    # reply = response.text
    chat = MODEL.start_chat(history=chat_history)        
    user_message_part = {"role": "user", "parts": [{"text": message}]}
    chat_history.append(user_message_part)        
    response_stream = chat.send_message(user_message_part, stream=True)
    reply = "".join(chunk.text for chunk in response_stream)

    chat_history.append({"role": "model", "parts": [{"text": reply}]})
    request.session["chat_history"] = chat_history[-20:]
    request.session.modified = True

    return Response({"reply": reply})

# ==================== Panchang API ====================

@api_view(["GET"])
@permission_classes([AllowAny])  # you can change to [IsAuthenticated] if login required
def panchang_api(request):
    try:    
        year = int(date.today().year)
        month = int(date.today().month)
        day = int(date.today().day)
        if request.POST.get('date'):
            date_str = datetime.strptime(request.POST.get('date'),"%Y-%m-%d")
            year,month,day = date_str.year,date_str.month,date_str.day
        lat,lon,tz = geocode_place_timezone(request.user.userprofile.birth_place)
        now = datetime.now(tz)
        offset_tz = float(now.utcoffset().total_seconds() / 3600)
        h = datetime.now().hour
        mi = datetime.now().minute
        result = get_panchang(year, month, day, h,  mi, lat, lon, offset_tz)

        serializer = PanchangSerializer(result)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=400)

# ==================== Compatibility API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def compatibility_api(request):
    person1 = request.data.get("person1")
    person2 = request.data.get("person2")
    if not person1 or not person2:
        return Response({"error": "Missing persons"}, status=400)
    result = compatibility_report(person1, person2)
    return Response({"text": result})


# ==================== Kundali API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def kundali_api(request):
    try:
        data = request.data
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
        minute = int(data['minute'])
        second = int(data['second'])
        place = data['place']

        lat, lon, tz = geocode_place_timezone(place)
        from datetime import datetime
        now = datetime.now(tz)
        offset_tz = float(now.utcoffset().total_seconds() / 3600)
        result = get_kundali_chart(year, month, day, hour, minute, lat, lon, offset_tz)
        return Response(result)
    except KeyError:
        return Response({"error": "Missing parameters"}, status=400)


# ==================== Kundali Matching API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def kundali_matching_api(request):
    person1 = request.data.get("person1")
    person2 = request.data.get("person2")
    if not person1 or not person2:
        return Response({"error": "Missing persons"}, status=400)
    result = perform_kundali_matching(person1, person2)
    return Response(result)


# ==================== Bazi API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bazi_api(request):
    try:
        data = request.data
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])

        bazi, chart, day_master, master_info, element_percentages = generate_bazi(year, month, day, hour)
        return Response({
            "bazi": bazi,
            "chart": chart,
            "day_master": day_master,
            "master_info": master_info,
            "element_percentages": element_percentages,
        })
    except KeyError:
        return Response({"error": "Missing parameters"}, status=400)


# ==================== User Profile API ====================
class UserProfileAPI(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.userprofile


# ==================== Signup API ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def signup_api(request):
    username = request.data.get("username")
    email = request.data.get("email")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Username and password required"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password)
    login(request, user)
    return Response({"success": True, "user_id": user.id})


# ==================== Login API ====================
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({"success": True, "user_id": user.id})
    else:
        return Response({"error": "Invalid credentials"}, status=400)


# ==================== Logout API ====================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    from django.contrib.auth import logout
    logout(request)
    return Response({"success": True})
