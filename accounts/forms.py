
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User, AllowedCedula, KPI, Evaluation, EvaluationKPI
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
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role', 'password', 'password2')

    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if not AllowedCedula.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula no está permitida para registrarse.")
        return cedula

class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('cedula', 'email', 'first_name', 'last_name', 'role')

class EvaluationForm(forms.Form):
    """
    Formulario para crear una nueva evaluación
    """
    overall_score = forms.FloatField(
        label='Puntuación General',
        min_value=0.0,
        max_value=10.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.1',
            'placeholder': 'Ej: 8.5'
        })
    )
    
    feedback = forms.CharField(
        label='Comentarios y Retroalimentación',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Escribe tus comentarios sobre el desempeño del negociador...'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener todos los KPIs disponibles
        kpis = KPI.objects.all()
        
        # Crear un campo para cada KPI
        for kpi in kpis:
            field_name = f'kpi_{kpi.id}'
            
            # Determinar el placeholder según el tipo de KPI
            if kpi.kpi_type == 'percentage':
                placeholder = f'Ej: 85.5 (0-100%)'
            elif kpi.kpi_type == 'amount':
                placeholder = f'Ej: 1500000 (0-{kpi.max_value:,.0f})'
            elif kpi.kpi_type == 'hours':
                placeholder = f'Ej: 45.5 (0-{kpi.max_value} horas)'
            elif kpi.kpi_type == 'count':
                placeholder = f'Ej: 25 (0-{kpi.max_value:,.0f})'
            else:  # score
                placeholder = f'Ej: 8.5 (0-10)'
            
            self.fields[field_name] = forms.FloatField(
                label=f'{kpi.name} ({kpi.unit})',
                help_text=f'{kpi.description} - Rango: {kpi.min_value} - {kpi.max_value} {kpi.unit}',
                min_value=kpi.min_value,
                max_value=kpi.max_value,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.1' if kpi.kpi_type in ['score', 'percentage', 'hours'] else '1',
                    'placeholder': placeholder
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        
        # Validar que al menos se haya evaluado un KPI
        kpi_scores = []
        for field_name, value in cleaned_data.items():
            if field_name.startswith('kpi_') and value is not None:
                kpi_scores.append(value)
        
        if not kpi_scores:
            raise forms.ValidationError("Debe evaluar al menos un KPI.")
        
        return cleaned_data

