from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import AllowedEmail
import getpass

class Command(BaseCommand):
    help = 'Creates users (leaders and administrators) interactively.'

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write(self.style.SUCCESS('--- Creación de Usuarios ---'))

        while True:
            user_type = input("¿Qué tipo de usuario quieres crear? (lider/administrativo/salir): ").lower()
            if user_type == 'salir':
                break
            elif user_type not in ['lider', 'administrativo']:
                self.stdout.write(self.style.ERROR("Tipo de usuario no válido. Por favor, elige 'lider', 'administrativo' o 'salir'."))
                continue

            email = input(f"Introduce el correo electrónico para el {user_type}: ")
            cedula = input(f"Introduce la cédula para el {user_type}: ")
            password = getpass.getpass(f"Introduce la contraseña para el {user_type}: ")
            first_name = input(f"Introduce el nombre para el {user_type} (opcional): ")
            last_name = input(f"Introduce el apellido para el {user_type} (opcional): ")

            # Ensure email is allowed
            AllowedEmail.objects.get_or_create(email=email)

            try:
                if not User.objects.filter(email=email).exists():
                    User.objects.create_user(
                        email=email,
                        password=password,
                        cedula=cedula,
                        role=user_type,
                        first_name=first_name,
                        last_name=last_name
                    )
                    self.stdout.write(self.style.SUCCESS(f'Usuario {user_type} {email} creado exitosamente.'))
                else:
                    self.stdout.write(self.style.WARNING(f'El usuario {email} ya existe.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error al crear el usuario: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Proceso de creación de usuarios finalizado.'))
