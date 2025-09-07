from django.core.management.base import BaseCommand
from accounts.models import Negotiator, NegotiatorIndicator
from django.utils import timezone
from random import randint, uniform
from datetime import timedelta

class Command(BaseCommand):
    help = 'Create simulated historical indicator data for negotiators'

    def handle(self, *args, **kwargs):
        for negotiator in Negotiator.objects.all():
            for i in range(12):  # last 12 months
                date = timezone.now().date() - timedelta(days=30 * i)
                NegotiatorIndicator.objects.update_or_create(
                    negotiator=negotiator,
                    date=date,
                    defaults={
                        'conversion_de_ventas': round(uniform(10, 90), 2),
                        'recaudacion_mensual': randint(1_000_000, 10_000_000),
                        'tiempo_hablando': round(uniform(10, 200), 2),
                        'porcentajes_cumplimiento_recaudo': round(uniform(50, 100), 2),
                        'porcentaje_cumplimiento_conversion': round(uniform(50, 100), 2),
                        'porcentaje_caidas_acuerdos': round(uniform(0, 30), 2),
                    }
                )
        self.stdout.write(self.style.SUCCESS(
            'Fake indicators created for all negotiators with the correct KPIs.'
        ))
