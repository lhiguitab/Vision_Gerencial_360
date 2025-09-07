
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):
    def create_user(self, cedula, password=None, **extra_fields):
        if not cedula:
            raise ValueError('La Cédula es obligatoria')
        
        # Validar contra la lista de cédulas permitidas
        if not AllowedCedula.objects.filter(cedula=cedula).exists():
            raise ValueError('La cédula no está permitida para registrarse.')

        user = self.model(cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, cedula, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Para el superusuario, no validamos contra la lista de cédulas permitidas
        user = self.model(cedula=cedula, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    cedula_validator = RegexValidator(
        regex=r'^\d{5,12}$',
        message='La cédula debe tener entre 5 y 12 dígitos numéricos.'
    )
    cedula = models.CharField(
        max_length=12,
        unique=True,
        validators=[cedula_validator],
        primary_key=True,
        help_text='Documento de identidad'
    )
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    ROLE_CHOICES = (
        ('lider', 'Líder'),
        ('administrativo', 'Administrativo'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='administrativo')

    objects = UserManager()

    USERNAME_FIELD = 'cedula'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.cedula

    @property
    def username(self):
        return self.cedula

    def get_negotiators_with_pending_evaluations(self):
        """
        Retorna los negociadores de este líder que tienen evaluaciones pendientes
        """
        negotiators = self.negotiators.all()
        pending_negotiators = []
        
        for negotiator in negotiators:
            if negotiator.get_evaluation_status == "Pendiente":
                last_evaluation = negotiator.evaluations.order_by('-date').first()
                days_since_last = None
                
                if last_evaluation:
                    days_since_last = (timezone.now() - last_evaluation.date).days
                
                pending_negotiators.append({
                    'negotiator': negotiator,
                    'last_evaluation_date': last_evaluation.date if last_evaluation else None,
                    'days_since_last': days_since_last
                })
        
        return pending_negotiators

class AllowedCedula(models.Model):
    cedula = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.cedula

from django.utils import timezone
from datetime import timedelta

class Negotiator(models.Model):
    leader = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='negotiators',
        limit_choices_to={'role': 'lider'}
    )
    name = models.CharField(max_length=255)
    cedula = models.CharField(max_length=12, unique=True)

    def __str__(self):
        return self.name

    @property
    def get_evaluation_status(self):
        last_evaluation = self.evaluations.order_by('-date').first()
        if not last_evaluation:
            return "Pendiente"
        
        six_months_ago = timezone.now() - timedelta(days=180)
        if last_evaluation.date < six_months_ago:
            return "Pendiente"
        
        return "Al día"

class KPI(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Evaluation(models.Model):
    negotiator = models.ForeignKey(Negotiator, on_delete=models.CASCADE, related_name='evaluations')
    evaluator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='evaluations_made')
    date = models.DateTimeField(auto_now_add=True)
    overall_score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True)

    def __str__(self):
        return f'Evaluación de {self.negotiator.name} en {self.date.strftime("%Y-%m-%d")}'

class EvaluationKPI(models.Model):
    evaluation = models.ForeignKey(Evaluation, on_delete=models.CASCADE, related_name='kpis')
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('evaluation', 'kpi')

    def __str__(self):
        return f'{self.kpi.name} - {self.score}'
