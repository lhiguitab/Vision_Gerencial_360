
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
        Retorna los negociadores de este líder que tienen evaluaciones pendientes y cuántas pendientes tienen
        """
        negotiators = self.negotiators.all()
        pending_negotiators = []
        for negotiator in negotiators:
            # Definir la lógica de "pendiente": si nunca ha sido evaluado o si la última evaluación fue hace más de 6 meses
            last_evaluation = negotiator.evaluations.order_by('-date').first()
            days_since_last = None
            pending_count = 0
            if not last_evaluation:
                # Nunca ha sido evaluado, cuenta como 1 pendiente
                pending_count = 1
            else:
                days_since_last = (timezone.now() - last_evaluation.date).days
                # Si han pasado más de 180 días desde la última evaluación, cuenta como 1 pendiente
                if days_since_last > 180:
                    pending_count = 1
            if pending_count > 0:
                pending_negotiators.append({
                    'negotiator': negotiator,
                    'last_evaluation_date': last_evaluation.date if last_evaluation else None,
                    'days_since_last': days_since_last,
                    'pending_count': pending_count
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

    def get_last_evaluation(self):
        """
        Retorna la última evaluación del negociador
        """
        return self.evaluations.order_by('-date').first()

    def has_evaluations(self):
        """
        Retorna True si el negociador tiene al menos una evaluación
        """
        return self.evaluations.exists()

    def get_evaluation_count(self):
        """
        Retorna el número total de evaluaciones del negociador
        """
        return self.evaluations.count()

    def calcular_puntuacion_hacer(self, periodo_dias=30):
        """
        Calcula la puntuación general del hacer (0-100) como el promedio de los KPIs porcentuales
        (excluyendo recaudo) del último periodo_dias días. Cada KPI tiene el mismo peso.
        """
        from datetime import timedelta
        from django.utils import timezone
        kpi_fields = [
            'conversion_de_ventas',
            'porcentajes_cumplimiento_recaudo',
            'porcentaje_cumplimiento_conversion',
            'porcentaje_caidas_acuerdos',
        ]
        fecha_inicio = timezone.now().date() - timedelta(days=periodo_dias)
        indicadores = self.indicators.filter(date__gte=fecha_inicio)
        if not indicadores.exists():
            return None
        promedios = []
        for kpi in kpi_fields:
            valores = indicadores.values_list(kpi, flat=True)
            valores = [v for v in valores if v is not None]
            if valores:
                promedios.append(sum(valores) / len(valores))
        if not promedios:
            return None
        puntuacion_hacer = sum(promedios) / len(promedios)
        return round(puntuacion_hacer, 2)

class KPI(models.Model):
    KPI_TYPE_CHOICES = [
        ('score', 'Puntuación (0-10)'),
        ('percentage', 'Porcentaje (0-100%)'),
        ('amount', 'Monto (pesos)'),
        ('hours', 'Horas'),
        ('count', 'Cantidad'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    kpi_type = models.CharField(max_length=20, choices=KPI_TYPE_CHOICES, default='score')
    min_value = models.FloatField(default=0.0, help_text='Valor mínimo permitido')
    max_value = models.FloatField(default=10.0, help_text='Valor máximo permitido')
    unit = models.CharField(max_length=20, blank=True, help_text='Unidad de medida (ej: %, $, horas)')

    def __str__(self):
        return self.name

    def get_display_value(self, value):
        """
        Retorna el valor formateado según el tipo de KPI
        """
        if self.kpi_type == 'percentage':
            return f"{value:.1f}%"
        elif self.kpi_type == 'amount':
            return f"${value:,.0f}"
        elif self.kpi_type == 'hours':
            return f"{value:.1f} horas"
        elif self.kpi_type == 'count':
            return f"{value:.0f}"
        else:  # score
            return f"{value:.1f}/10"

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

class NegotiatorIndicator(models.Model):
    """
    Historical indicators for a negotiator (real-time in production from Databricks).
    Field names aligned with the KPI names used by create_fake_indicators.py.
    """
    negotiator = models.ForeignKey('Negotiator', on_delete=models.CASCADE, related_name='indicators')
    date = models.DateField()

    # === Required KPIs ===
    conversion_de_ventas = models.FloatField(default=0.0, help_text='Conversión de ventas (%)')
    recaudacion_mensual = models.FloatField(default=0.0, help_text='Recaudación mensual ($)')
    tiempo_hablando = models.FloatField(default=0.0, help_text='Tiempo hablando (horas)')
    porcentajes_cumplimiento_recaudo = models.FloatField(default=0.0, help_text='Porcentaje de cumplimiento de recaudo (%)')
    porcentaje_cumplimiento_conversion = models.FloatField(default=0.0, help_text='Porcentaje de cumplimiento de conversión (%)')
    porcentaje_caidas_acuerdos = models.FloatField(default=0.0, help_text='Porcentaje de caídas de acuerdos (%)')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        unique_together = ('negotiator', 'date')

    def __str__(self):
        return f'{self.negotiator.name} - {self.date}'

    # Optional helper properties (keep if useful; they use the above KPIs)
    @property
    def success_rate(self):
        """
        If you later track deals_closed/deals_failed again, you can restore this.
        Currently not computable with the given KPIs alone.
        """
        return None

    @property
    def revenue_per_hour(self):
        """Average revenue per hour talking; safe if tiempo_hablando is zero."""
        if self.tiempo_hablando == 0:
            return 0.0
        return self.recaudacion_mensual / self.tiempo_hablando