from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
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


class CustomPasswordChangeForm(PasswordChangeForm):
    """Formulaire personnalisé pour changer le mot de passe avec labels et help_text en français"""
    old_password = forms.CharField(
        label='Ancien mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Entrez votre mot de passe actuel'}),
        error_messages={'required': 'Ce champ est obligatoire.'}
    )
    new_password1 = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Entrez votre nouveau mot de passe'}),
        help_text='<ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 12px; color: #6B7280;"><li>Votre mot de passe ne doit pas être trop similaire à vos autres informations personnelles.</li><li>Votre mot de passe doit contenir au moins 8 caractères.</li><li>Votre mot de passe ne peut pas être un mot de passe couramment utilisé.</li><li>Votre mot de passe ne peut pas être entièrement numérique.</li></ul>',
        error_messages={'required': 'Ce champ est obligatoire.'}
    )
    new_password2 = forms.CharField(
        label='Confirmation du nouveau mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmez votre nouveau mot de passe'}),
        help_text='Entrez le même mot de passe qu\'avant, pour vérification.',
        error_messages={'required': 'Ce champ est obligatoire.'}
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les messages d'erreur
        self.error_messages = {
            'password_incorrect': 'Votre ancien mot de passe est incorrect. Veuillez réessayer.',
            'password_mismatch': 'Les deux champs de mot de passe ne correspondent pas.',
        }
    
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Les deux champs de mot de passe ne correspondent pas.')
        return password2
