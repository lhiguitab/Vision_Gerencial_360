from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, AllowedEmail, KPI, Evaluation, EvaluationKPI
from django import forms
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    cedula = forms.CharField(max_length=12, label='Cédula', widget=forms.TextInput(attrs={'placeholder': 'Cédula'}))
    first_name = forms.CharField(max_length=255, label='Nombre', required=False)
    last_name = forms.CharField(max_length=255, label='Apellido', required=False)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        
        if email and not AllowedEmail.objects.filter(email__iexact=email).exists():
            self.add_error('email', "Este correo electrónico no está permitido para registrarse.")

        if email and User.objects.filter(email__iexact=email).exists():
            self.add_error('email', "Un usuario con este correo electrónico ya existe.")

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
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role', 'password', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not AllowedEmail.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo electrónico no está permitido para registrarse.")
        return email

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role')

class EvaluationForm(forms.Form):
    """
    Formulario para crear una nueva evaluación (solo feedback, la puntuación se calcula automáticamente)
    """
    feedback = forms.CharField(
        label='Comentarios y Retroalimentación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escribe tus comentarios sobre el desempeño del negociador...'
        }),
        required=False
    )
    

# Formulario para la Evaluación del Ser
class SerEvaluationForm(forms.Form):
    actitud = forms.ChoiceField(
        label='Actitud', choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, required=True
    )
    trabajo_en_equipo = forms.ChoiceField(
        label='Trabajo en equipo', choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, required=True
    )
    sentido_pertenencia = forms.ChoiceField(
        label='Sentido de pertenencia', choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, required=True
    )
    relacionamiento = forms.ChoiceField(
        label='Relacionamiento', choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, required=True
    )
    compromiso = forms.ChoiceField(
        label='Compromiso con la empresa', choices=[(i, i) for i in range(1, 6)], widget=forms.RadioSelect, required=True
    )