
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, AllowedCedula
from django import forms
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    cedula = forms.CharField(max_length=12, label='Cédula', widget=forms.TextInput(attrs={'placeholder': 'Cédula'}))
    first_name = forms.CharField(max_length=255, label='Nombre', required=False)
    last_name = forms.CharField(max_length=255, label='Apellido', required=False)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        cedula = cleaned_data.get("cedula")

        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error('email', "Un usuario con este correo electrónico ya existe.")

        if cedula and User.objects.filter(cedula=cedula).exists():
            self.add_error('cedula', "Un usuario con esta cédula ya existe.")

        if self.errors:
            raise forms.ValidationError("Por favor, corrige los errores a continuación.")

        return cleaned_data

    def signup(self, request, user):
        user.cedula = self.cleaned_data['cedula']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        return user

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role')

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not AllowedCedula.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula no está permitida para registrarse.")
        return cedula

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role')

