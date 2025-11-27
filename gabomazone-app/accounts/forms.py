from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordResetForm
from django.core import validators
from captcha.fields import CaptchaField

class CaptchaPasswordResetForm(PasswordResetForm):
    captcha = CaptchaField()

class UserCreationForm(forms.ModelForm):
    # username = forms.CharField(label='اسم المستخدم')
    # email = forms.EmailField(max_length=100, label="البريد الالكترونى")
    # first_name = forms.CharField(max_length=100, label="الاسم الأول")
    # last_name = forms.CharField(max_length=100, label="الاسم الثانى")
    username = forms.CharField(
        label=('Username'),
        max_length=150,

        help_text=(
            "usernames can't contain spaces or  @/./+/-/_ characters ."),
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-]+$', "usernames can't contain spaces ,This value may contain only letters, numbers ''and @/./+/-/_ characters.", 'invalid'),
        ],
        error_messages={'unique': (
            "A user with that username already exists.")},
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='password', widget=forms.PasswordInput(), min_length=8)
    password2 = forms.CharField(
        label='password confirmation', widget=forms.PasswordInput(), min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        # fields = ('username', 'email', 'first_name',
        #           'last_name', 'password1', 'password2')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('your password not match !')
        return cd['password2']

    def clean_username(self):
        cd = self.cleaned_data
        if User.objects.filter(username=cd['username']).exists():
            raise forms.ValidationError('username is exists ! ')
        return cd['username']

    def clean_email(self):
        cd = self.cleaned_data
        if User.objects.filter(email=cd['email']).exists():
            raise forms.ValidationError('email is exists !')
        return cd['email']


class LoginForm(forms.ModelForm):
    username = forms.CharField(label='Username or Email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ('username', 'password')
