from rest_framework import serializers
from .models import UserProfile,TarotCard
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'birth_date', 'birth_time', 'birth_place', 'birth_lat', 'birth_lng', 'birth_tz', 'system']

class TimeRangeSerializer(serializers.Serializer):
    name = serializers.CharField()
    time = serializers.CharField()

class PanchangSerializer(serializers.Serializer):
    tithi = serializers.CharField()
    paksha = serializers.CharField()
    nakshatra = serializers.CharField()
    yoga = serializers.CharField()
    karana = serializers.CharField()
    vara = serializers.CharField()
    sunrise = serializers.CharField()
    sunset = serializers.CharField()
    moonrise = serializers.CharField()
    moonset = serializers.CharField()
    rahu_kaal = serializers.CharField()
    gulika_kaal = serializers.CharField()
    yamaganda = serializers.CharField()
    abhijit_muhurta = serializers.CharField()
    choghadiya_day = TimeRangeSerializer(many=True)
    choghadiya_night = TimeRangeSerializer(many=True)
    
    
class TarotCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = TarotCard
        fields = ["id", "name", "suit", "meaning_upright", "meaning_reversed", "image"]