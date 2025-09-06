
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import AllowedCedula

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

        self.stdout.write(self.style.SUCCESS('¡Proceso completado!'))

