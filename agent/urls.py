from django.urls import path
from . import views

urlpatterns = [
    path("signup", views.signup, name="signup"),
    path('login/',views.loginUser,name='login'),
    path('logout',views.logoutUser,name='logout'),
    path('',views.home,name='home'),
    path("profile", views.edit_profile, name="save_profile"),
    path("chat_api", views.chat_api, name="chat_api"),
    path('chat',views.chat,name='chat'),
    path('terms',views.terms,name='terms'),
    path('horoscope',views.horoscope,name='horoscope'),
    path('kundali',views.kundali,name='kundali'),
    path('kundali_match',views.kundali_matching,name='kundali-match'),
    path('compatibility',views.compatibility,name='compatibility'),
    path('bazi',views.bazi_view,name='bazi'),
    path('panchang',views.panchang_view,name='panchang'),
    path("tarot", views.tarot_page, name="tarot"),
    path("tarot/draw-card/", views.draw_card, name="draw_card"),
    path("tarot/three-card/", views.three_card_spread, name="three_card_spread"),
]
