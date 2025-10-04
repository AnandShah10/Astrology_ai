from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    SYSTEM_CHOICES = [
        ("vedic", "Vedic Astrology"),
        ("western", "Western Astrology"),
        ("chinese", "Chinese Astrology"),
        ("numerology","Numerology"),
        ("korean","Korean Astrology"),
        ("vastu","Vastu Shastra")
    ]

    TIMEZONE_CHOICES = [
        ("Asia/Kolkata", "Asia/Kolkata (UTC+5:30)"),
        ("UTC", "UTC"),
        ("America/New_York", "America/New_York (UTC-5)"),
        ("Europe/London", "Europe/London (UTC+0)"),
        ("Asia/Dubai", "Asia/Dubai (UTC+4)"),
        ("Australia/Sydney", "Australia/Sydney (UTC+10)"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    name= models.CharField(max_length=50,default="")
    
    gender = models.CharField(default='male',choices=[('male','Male'),('female','Female'),('other','Other')])

    # Astrology fields
    birth_date = models.DateField(null=True, blank=True)
    birth_time = models.TimeField(null=True, blank=True)
    birth_place = models.CharField(max_length=128, null=True, blank=True)

    # These now use choices
    birth_tz = models.CharField(max_length=64, choices=TIMEZONE_CHOICES, default="Asia/Kolkata")
    system = models.CharField(max_length=16, choices=SYSTEM_CHOICES, default="vedic")

    # Auto-filled fields (from geocoding)
    birth_lat = models.FloatField(null=True, blank=True)
    birth_lng = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"Profile({self.user.username})"

class TarotCard(models.Model):
    name = models.CharField(max_length=100)
    suit = models.CharField(max_length=50)
    meaning_upright = models.TextField()
    meaning_reversed = models.TextField()
    image = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name