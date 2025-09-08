from django.core.management.base import BaseCommand
from accounts.models import KPI

class Command(BaseCommand):
    help = 'Actualiza los KPIs existentes con los rangos, tipos y unidades correctos.'

    def handle(self, *args, **options):
        mapping = {
            'Conversión de Ventas': {
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            'Recaudación Mensual': {
                'kpi_type': 'amount',
                'min_value': 0.0,
                'max_value': 10000000000.0,
                'unit': '$'
            },
            'Tiempo Hablando': {
                'kpi_type': 'hours',
                'min_value': 0.0,
                'max_value': 200.0,
                'unit': 'horas'
            },
            'Porcentajes de Cumplimiento de Recaudo': {
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            'Porcentaje de Cumplimiento de Conversión': {
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            'Porcentaje de Caídas de Acuerdos': {
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
        }
        updated = 0
        for k in KPI.objects.all():
            if k.name in mapping:
                for key, val in mapping[k.name].items():
                    setattr(k, key, val)
                k.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"KPI '{k.name}' actualizado."))
            else:
                self.stdout.write(self.style.WARNING(f"KPI '{k.name}' no está en el mapeo y no fue actualizado."))
        self.stdout.write(self.style.SUCCESS(f"KPIs actualizados: {updated}"))
