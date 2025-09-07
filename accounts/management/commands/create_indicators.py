from django.core.management.base import BaseCommand
from accounts.models import Negotiator, NegotiatorIndicator
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Crea datos de indicadores históricos para los negociadores'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creando datos de indicadores históricos...'))
        
        # Obtener todos los negociadores
        negotiators = Negotiator.objects.all()
        
        if not negotiators.exists():
            self.stdout.write(self.style.WARNING('No hay negociadores en el sistema. Ejecute primero create_users.'))
            return
        
        # Generar datos para los últimos 6 meses
        end_date = date.today()
        start_date = end_date - timedelta(days=180)
        
        for negotiator in negotiators:
            self.stdout.write(self.style.SUCCESS(f'Generando datos para {negotiator.name}...'))
            
            # Generar datos diarios para los últimos 6 meses
            current_date = start_date
            while current_date <= end_date:
                # Solo generar datos para días laborales (lunes a viernes)
                if current_date.weekday() < 5:
                    # Crear o actualizar indicador para esta fecha
                    indicator, created = NegotiatorIndicator.objects.get_or_create(
                        negotiator=negotiator,
                        date=current_date,
                        defaults={
                            'conversion_rate': round(random.uniform(15, 85), 1),
                            'total_revenue': round(random.uniform(50000, 500000), 0),
                            'absenteeism_rate': round(random.uniform(0, 10), 1),
                            'call_duration': round(random.uniform(5, 45), 1),
                            'calls_made': random.randint(20, 80),
                            'deals_closed': random.randint(2, 15),
                            'deals_failed': random.randint(1, 8),
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'  - Creado indicador para {current_date}'))
                
                current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS('¡Datos de indicadores creados exitosamente!'))
        
        # Mostrar resumen
        total_indicators = NegotiatorIndicator.objects.count()
        self.stdout.write(self.style.SUCCESS(f'Total de indicadores creados: {total_indicators}'))
        
        for negotiator in negotiators:
            count = negotiator.indicators.count()
            self.stdout.write(self.style.SUCCESS(f'{negotiator.name}: {count} indicadores'))
