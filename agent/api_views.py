# yourapp/api_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import generics,status
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from .models import UserProfile,TarotCard
from .serializers import UserProfileSerializer,PanchangSerializer
from datetime import date,datetime,timedelta
import os,base64,io,random
# from google.generativeai import GenerativeModel, configure
# from dotenv import load_dotenv
from .utils.kundali import get_kundali_chart
from .utils.compatibility import compatibility_report
from .utils.kundali_matching import perform_kundali_matching
from .utils.chinese_zodiac import generate_bazi
from .views import geocode_place_timezone
from .utils.panchang import get_panchang
# from gtts import gTTS
from faster_whisper import WhisperModel
from .utils.tarot import get_ai_interpretation,load_cards
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from openai import AzureOpenAI
def get_permanent_token(user):
    token = AccessToken.for_user(user)
    # token.set_exp(lifetime=timedelta(days=365*100))  # 100 years
    token["exp"] = datetime.now() + timedelta(days=365*100)
    print(token.lifetime)
    return str(token)

# load_cards()
whisperModel = WhisperModel("base")
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
# load_dotenv()
# AI_API_KEY = os.getenv('AI_API_KEY')
# configure(api_key=AI_API_KEY)
# MODEL = GenerativeModel("gemini-2.5-flash")

endpoint = os.getenv("ENDPOINT_URL", "https://jivihireopenai.openai.azure.com/")
client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=os.environ['OPENAI_API_KEY'],
        api_version="2024-05-01-preview",
    )
    
# ==================== Chat API ====================
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_api(request):
    print(request.data)
    is_voice = False
    if 'audio' in request.FILES:
        is_voice = True
        audio_file = request.FILES['audio']
        # print(audio_file)
        audio_content = audio_file.read()
        segments, info = whisperModel.transcribe(io.BytesIO(audio_content))
        print(segments)
        try:
                message = " ".join(seg.text.strip() for seg in segments)
        except Exception as e:
                return Response({"error": "Empty message"+e}, status=400)
    else:
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
        today=date.today(),
        name=profile.name or request.user.username,
    )

    chat_history = request.session.get("chat_history", [])

    if not chat_history:
        chat_history = [{"role": "system", "content": system_prompt}]

    # Add user message
    chat_history.append({"role": "user", "content": message})

    # Call OpenAI GPT model
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
        messages=chat_history[-20:],  # last 20 messages
        temperature=0.7
    )

    reply = response.choices[0].message.content.strip()

    # Save in session
    chat_history.append({"role": "assistant", "content": reply})
    request.session["chat_history"] = chat_history[-20:]
    request.session.modified = True

    # audio_base64 = None
    # if is_voice:
    #     audio_base64 = None
    #     tts = gTTS(reply, lang="en")
    #     audio_buffer = io.BytesIO()
    #     tts.write_to_fp(audio_buffer)
    #     audio_buffer.seek(0)
    #     audio_base64 = base64.b64encode(audio_buffer.read()).decode("utf-8")
    #     # print(reply,audio_base64)
    #     return Response({
    #             "reply": reply,
    #             "audio": audio_base64 if is_voice else None
    #         })
    # else:
    #     return Response({"reply": reply})
    return Response({"reply": reply})
    
# ==================== Horoscope API ===================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def horoscope_api(request):
    sign = request.data.get("sign", "").capitalize()

    if not sign:
        return Response({"error": "Please provide a zodiac sign."}, status=400)

    # Prompt for GPT
    prompt = f"Give me today's horoscope for the zodiac sign {sign} in 3-4 sentences. Keep it positive and inspiring."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert astrologer who gives daily horoscopes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        horoscope = response.choices[0].message.content.strip()

        return Response({
            "sign": sign,
            "horoscope": horoscope
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)

# ==================== Panchang API ====================
@api_view(["POST"])
@permission_classes([IsAuthenticated])  # you can change to [IsAuthenticated] if login required
def panchang_api(request):
    try:    
        year = int(date.today().year)
        month = int(date.today().month)
        day = int(date.today().day)
        if request.POST.get('date'):
            date_str = datetime.strptime(request.POST.get('date'),"%Y-%m-%d")
            year,month,day = date_str.year,date_str.month,date_str.day
        if request.POST.get('place'):
            place =request.POST.get('place')
        else:
            place = request.user.userprofile.birth_place
        lat,lon,tz = geocode_place_timezone(place)
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
    
# ================== Tarot cards API ==================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
    return Response({
        "card": data,
        "interpretation": interpretation
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
    return Response({
        "spread": spread,
        "interpretation": interpretation
    })

# ==================== User Profile API ====================
class UserProfileAPI(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user.userprofile
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_profile_api(request):
    lat,lon,tz = geocode_place_timezone(request.data.get('birth_place'))
    serializer = UserProfileSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user,birth_lat=lat,birth_lng=lon)  # ✅ link profile to logged-in user
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_profile_api(request):
    user_profile = UserProfile.objects.get(user=request.user)  # retrieve profile for current user
    serializer = UserProfileSerializer(user_profile, data=request.data)
    if serializer.is_valid():
        serializer.save()  # This will update the profile, saving changes to the existing model instance.
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==================== Signup API ====================
@csrf_exempt
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
    # tokens = get_tokens_for_user(user)
    token = get_permanent_token(user)
    # login(request, user)
    return Response({"success": True, "user_id": user.id,"token":token})

# ==================== Login API ====================
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is not None:
        # login(request, user)
        # tokens = get_tokens_for_user(user)
        token = get_permanent_token(user)
        return Response({"success": True, "user_id": user.id,"token":token})
    else:
        return Response({"error": "Invalid credentials"}, status=400)

# ==================== Logout API ====================
@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=400)

        token = RefreshToken(refresh_token)
        token.blacklist()  # invalidate this token

        return Response({"success": True, "message": "Logged out successfully"})
    except Exception as e:
        return Response({"error": str(e)}, status=400)
