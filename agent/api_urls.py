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
    path('profile/', api_views.UserProfileAPI.as_view(), name='api-profile'),
    path('signup/', api_views.signup_api, name='api-signup'),
    path('login/', api_views.login_api, name='api-login'),
    path('logout/', api_views.logout_api, name='api-logout'),
]