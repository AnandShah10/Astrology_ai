from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path('login/',views.loginUser,name='login'),
    path('logout/',views.logoutUser,name='logout'),
    path('',views.home,name='home'),
    path("profile/", views.edit_profile, name="save_profile"),
    path("api/", views.chat_api, name="chat_api"),
    path('chat',views.chat,name='chat'),
    path('terms',views.terms,name='terms'),
    path('horoscope',views.horoscope,name='horoscope'),
    path('kundali',views.kundali,name='kundali'),
    path('compatibility',views.compatibility,name='compatibility'),
    path('bazi',views.bazi_view,name='bazi'),
]
