# yourapp/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

class UserAPITest(APITestCase):

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username='testuser', email='test@test.com', password='testpass')
        # Create UserProfile
        self.profile = UserProfile.objects.create(
            user=self.user,
            birth_date="1990-01-01",
            birth_time="12:00:00",
            birth_place="Delhi",
            birth_lat=28.6139,
            birth_lng=77.2090,
            birth_tz="Asia/Kolkata",
            system="Vedic"
        )
        # Login client
        self.client.login(username='testuser', password='testpass')

    # -------------------- Profile Tests --------------------
    def test_get_user_profile(self):
        response = self.client.get('/api/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_update_user_profile(self):
        data = {'birth_place': 'Mumbai', 'birth_lat': 19.0760, 'birth_lng': 72.8777}
        response = self.client.patch('/api/profile/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['birth_place'], 'Mumbai')

    # -------------------- Chat Tests --------------------
    def test_chat_api(self):
        data = {'message': 'Hello Astro AI!'}
        response = self.client.post('/api/chat/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('reply', response.data)
        
    @patch("agent.api_views.whisperModel.transcribe")  # Mock whisper model
    def test_voice_chat_api(self, mock_transcribe):
        mock_transcribe.return_value = (
            [type("seg", (), {"text": "Hello from voice"})()],  # fake segment object
            {}
        )
        audio_file = SimpleUploadedFile("test.wav", b"fake-audio-content", content_type="audio/wav")
        response = self.client.post(
            "/api/chat/",
            {"audio": audio_file},
            format="multipart"  # important: multipart for file upload
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reply", response.data)
        self.assertIn("audio", response.data)
        
    # -------------------- Panchang Tests --------------------
    def test_panchang_api(self):
        data = {'date': '2025-09-29',"place":"Ahmedabad,Gujarat,India"}
        response = self.client.post('/api/panchang/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tithi', response.data)
        
    # -------------------- Compatibility Tests --------------------
    def test_compatibility_api(self):
        data = {'person1': {'Name':'Anand','Date':'10-07-2004','Time':'13:20','Place':'Ahmedabad,Gujarat,India'}, 'person2': {'Name':'Dhyani','Date':'06-12-2002','Time':'20:20','Place':'Ahmedabad,Gujarat,India'}}
        response = self.client.post('/api/compatibility/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('text', response.data)
        
    # -------------------- Kundali match Tests --------------------
    def test_kundali_match_api(self):
        data = {'person1': {'Name':'Anand','Date':'2004-07-10','Time':'13:20','Place':'Ahmedabad,Gujarat,India'}, 'person2': {'Name':'Dhyani','Date':'2002-12-06','Time':'20:20','Place':'Ahmedabad,Gujarat,India'}}
        response = self.client.post('/api/kundali-matching/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('breakdown', response.data)

    # -------------------- Kundali Tests --------------------
    def test_kundali_api(self):
        data = {
            'year': 1990, 'month': 1, 'day': 1,
            'hour': 12, 'minute': 0, 'second': 0,
            'place': 'Delhi'
        }
        response = self.client.post('/api/kundali/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, dict)

    # -------------------- Bazi Tests --------------------
    def test_bazi_api(self):
        data = {'year': 1990, 'month': 1, 'day': 1, 'hour': 12}
        response = self.client.post('/api/bazi/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('bazi', response.data)
        
    # -------------------- Tarot Card Tests --------------------
    def test_draw_card_api(self):
        response = self.client.get('/api/tarot/draw-card/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('interpretation', response.data)
        
    def test_three_card_spread_api(self):
        response = self.client.get('/api/tarot/three-card/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('interpretation', response.data)

    # -------------------- Signup/Login/Logout Tests --------------------
    def test_signup_api(self):
        data = {'username': 'newuser', 'email': 'new@test.com', 'password': 'newpass123'}
        response = self.client.post('/api/signup/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('user_id' in response.data)

    def test_login_api(self):
        data = {'username': 'testuser', 'password': 'testpass'}
        self.client.logout()  # Ensure logged out
        response = self.client.post('/api/login/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('user_id' in response.data)

    def test_logout_api(self):
        response = self.client.post('/api/logout/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get('success'))
