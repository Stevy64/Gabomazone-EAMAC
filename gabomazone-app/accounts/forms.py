from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordResetForm, PasswordChangeForm
from django.core import validators
from captcha.fields import CaptchaField

class CaptchaPasswordResetForm(PasswordResetForm):
    captcha = CaptchaField()

class UserCreationForm(forms.ModelForm):
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        help_text="Lettres, chiffres et @/./+/-/_ uniquement.",
        validators=[
            validators.RegexValidator(
                r'^[\w.@+-]+$',
                "Ce nom ne peut contenir que des lettres, chiffres et les caractères @/./+/-/_.",
                'invalid'
            ),
        ],
        error_messages={'unique': "Ce nom d'utilisateur existe déjà."},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Entrez votre nom d'utilisateur"})
    )
    email = forms.EmailField(
        label='Adresse email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'votre@email.com'})
    )
    phone_number = forms.CharField(
        label='Numéro de téléphone (Airtel/Moov)',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+241 XX XX XX XX'}),
        help_text='Nécessaire pour les paiements mobile money'
    )
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Minimum 8 caractères'}),
        min_length=8
    )
    password2 = forms.CharField(
        label='Confirmation du mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Répétez le mot de passe'}),
        min_length=8
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'phone_number', 'password1', 'password2')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password1'] != cd['password2']:
            raise forms.ValidationError('Les mots de passe ne correspondent pas.')
        return cd['password2']

    def clean_username(self):
        cd = self.cleaned_data
        if User.objects.filter(username=cd['username']).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà pris.")
        return cd['username']

    def clean_email(self):
        cd = self.cleaned_data
        if User.objects.filter(email=cd['email']).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée.')
        return cd['email']


class LoginForm(forms.ModelForm):
    username = forms.CharField(label="Nom d'utilisateur ou Email")
    password = forms.CharField(label='Mot de passe', widget=forms.PasswordInput())

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
