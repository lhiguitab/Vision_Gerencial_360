
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import AllowedCedula, KPI

class Command(BaseCommand):
    help = 'Crea un superusuario y una lista de cédulas permitidas'

    def handle(self, *args, **options):
        User = get_user_model()

        # Crear superusuario
        if not User.objects.filter(cedula='12345').exists():
            self.stdout.write(self.style.SUCCESS('Creando superusuario 12345...'))
            User.objects.create_superuser(
                cedula='12345',
                password='Admin999*',
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role='lider'
            )
        else:
            self.stdout.write(self.style.WARNING('El superusuario 12345 ya existe.'))

        # Añadir cédulas permitidas
        allowed_cedulas = ['11111', '22222', '33333', '44444', '55555']
        self.stdout.write(self.style.SUCCESS('Añadiendo cédulas permitidas...'))
        for cedula in allowed_cedulas:
            if not AllowedCedula.objects.filter(cedula=cedula).exists():
                AllowedCedula.objects.create(cedula=cedula)
                self.stdout.write(self.style.SUCCESS(f'Cédula {cedula} añadida.'))
            else:
                self.stdout.write(self.style.WARNING(f'La cédula {cedula} ya existe en la lista de permitidos.'))

        # Crear KPIs por defecto
        self.stdout.write(self.style.SUCCESS('Creando KPIs por defecto...'))
        default_kpis = [
            {
                'name': 'Conversión de Ventas',
                'description': 'Porcentaje de clientes potenciales que se convierten en ventas efectivas',
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            {
                'name': 'Recaudación Mensual',
                'description': 'Monto total recaudado en el período evaluado',
                'kpi_type': 'amount',
                'min_value': 0.0,
                'max_value': 10000000.0,
                'unit': '$'
            },
            {
                'name': 'Tiempo Hablando',
                'description': 'Tiempo hablando con los clientes',
                'kpi_type': 'hours',
                'min_value': 0.0,
                'max_value': 200.0,
                'unit': 'horas'
            },
            {
                'name': 'Porcentajes de Cumplimiento de Recaudo',
                'description': 'Porcentaje de recaudación realizada en el período evaluado',
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            {
                'name': 'Porcentaje de Cumplimiento de Conversión',
                'description': 'Porcentaje de conversión realizada en el período evaluado',
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            },
            {
                'name': 'Porcentaje de Caídas de Acuerdos',
                'description': 'Porcentaje de caídas de acuerdos en el período evaluado',
                'kpi_type': 'percentage',
                'min_value': 0.0,
                'max_value': 100.0,
                'unit': '%'
            }
        ]
        
        for kpi_data in default_kpis:
            if not KPI.objects.filter(name=kpi_data['name']).exists():
                KPI.objects.create(
                    name=kpi_data['name'],
                    description=kpi_data['description'],
                    kpi_type=kpi_data['kpi_type'],
                    min_value=kpi_data['min_value'],
                    max_value=kpi_data['max_value'],
                    unit=kpi_data['unit']
                )
                self.stdout.write(self.style.SUCCESS(f'KPI creado: {kpi_data["name"]} ({kpi_data["kpi_type"]})'))
            else:
                self.stdout.write(self.style.WARNING(f'El KPI {kpi_data["name"]} ya existe.'))

        self.stdout.write(self.style.SUCCESS('¡Proceso completado!'))

