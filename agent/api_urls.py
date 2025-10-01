# yourapp/api_urls.py
from django.urls import path
from . import api_views

urlpatterns = [
    path('chat/', api_views.chat_api, name='api-chat'),
    path('compatibility/', api_views.compatibility_api, name='api-compatibility'),
    path('kundali/', api_views.kundali_api, name='api-kundali'),
    path('panchang/', api_views.panchang_api, name='api-panchang'),
    path('kundali-matching/', api_views.kundali_matching_api, name='api-kundali-matching'),
    path('bazi/', api_views.bazi_api, name='api-bazi'),
    path('create-profile/',api_views.create_profile_api,name="api-create-profile"),
    path('update-profile/',api_views.update_profile_api,name="api-update-profile"),
    path('horoscope/', api_views.horoscope_api, name='api-horoscope'),
    path('signup/', api_views.signup_api, name='api-signup'),
    path('login/', api_views.login_api, name='api-login'),
    path('logout/', api_views.logout_api, name='api-logout'),
    path("tarot/draw-card/", api_views.draw_card, name="draw_card"),
    path("tarot/three-card/", api_views.three_card_spread, name="three_card_spread"),
]