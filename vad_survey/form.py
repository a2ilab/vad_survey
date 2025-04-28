# vad_survey/forms.py
from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.db import transaction
from .models import UserProfile

# 회원가입 뷰
def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            sona_id = form.cleaned_data['username']

            # username (sona_id) 중복 체크
            if User.objects.filter(username=sona_id).exists():
                messages.error(request, "이미 사용 중인 소나 ID입니다.")
                return redirect('signup')

            try:
                with transaction.atomic():
                    # User 저장
                    user = form.save()

                    # UserProfile 직접 생성
                    UserProfile.objects.create(
                        user=user,
                        sona_id=sona_id,
                        gender=form.cleaned_data['gender'],
                        age=form.cleaned_data['age'],
                    )

                return redirect('home')

            except Exception as e:
                messages.error(request, f"회원가입 중 오류 발생: {str(e)}")
                return redirect('signup')

    else:
        form = SignUpForm()

    return render(request, 'signup.html', {'form': form})

# 회원가입 폼
class SignUpForm(UserCreationForm):
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
    ]

    username = forms.IntegerField(
        label='소나 ID',
        min_value=1,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        })
    )

    age = forms.IntegerField(
        label='나이',
        min_value=1,
        max_value=100,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        })
    )

    gender = forms.ChoiceField(
        label='성별',
        choices=GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'age', 'gender')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)

        common_class = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm'
        self.fields['password1'].widget.attrs.update({'class': common_class})
        self.fields['password2'].widget.attrs.update({'class': common_class})
