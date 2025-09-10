from django import forms
from .models import UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["birth_date", "birth_time", "birth_place", "system"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "birth_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "birth_place": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., Mumbai, India"}),
            "system": forms.Select(attrs={"class": "form-select"}),    # dropdown
        }
class CustomSignupForm(UserCreationForm):
    terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms & Conditions",
        error_messages={'required': 'You must accept the Terms & Conditions to register.'}
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "terms")    