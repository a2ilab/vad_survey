# vad_survey/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('O', '기타'),
    ]

    PERSONALITY_CHOICES = [
        ('E', '외향적'),
        ('I', '내향적'),
        ('B', '둘 다 아님'),
    ]

    age = forms.IntegerField(
        label='나이',
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'})
    )

    gender = forms.ChoiceField(
        label='성별',
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'})
    )

    personality_type = forms.ChoiceField(
        label='성격 유형',
        choices=PERSONALITY_CHOICES,
        widget=forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'})
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'age', 'gender', 'personality_type')