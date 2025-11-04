from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import AllowedEmail, Negotiator, NegotiatorIndicator, KPI, Evaluation, EvaluationKPI, SerEvaluation
from datetime import timedelta
from random import randint, uniform
from pathlib import Path


class Command(BaseCommand):
    help = 'Siembra usuarios de roles, negociadores y datos simulados. Crea archivo usuarios_credenciales.txt con accesos.'

    def handle(self, *args, **options):
        User = get_user_model()

        created_accounts = []

        # Asegurar KPIs base para Evaluations (porcentaje)
        kpis_conf = [
            ('Conversión de Ventas', 'percentage', '%'),
            ('Porcentajes de Cumplimiento de Recaudo', 'percentage', '%'),
            ('Porcentaje de Cumplimiento de Conversión', 'percentage', '%'),
            ('Porcentaje de Caídas de Acuerdos', 'percentage', '%'),
        ]
        for name, ktype, unit in kpis_conf:
            KPI.objects.get_or_create(
                name=name,
                defaults=dict(description=name, kpi_type=ktype, min_value=0.0, max_value=100.0, unit=unit)
            )

        # Utilidad para crear usuarios respetando AllowedEmail
        def ensure_allowed(email: str):
            AllowedEmail.objects.get_or_create(email=email)

        def create_user(email: str, password: str, cedula: str, role: str, first_name: str, last_name: str, is_staff=False, is_superuser=False):
            ensure_allowed(email)
            if is_superuser:
                if not User.objects.filter(email=email).exists():
                    u = User.objects.create_superuser(
                        email=email,
                        password=password,
                        cedula=cedula,
                        first_name=first_name,
                        last_name=last_name,
                        is_staff=True,
                        is_superuser=True,
                        role=role,
                    )
                else:
                    u = User.objects.get(email=email)
                    u.is_staff = True
                    u.is_superuser = True
                    u.role = role
                    u.set_password(password)
                    u.save()
            else:
                if not User.objects.filter(email=email).exists():
                    u = User.objects.create_user(
                        email=email,
                        password=password,
                        cedula=cedula,
                        role=role,
                        first_name=first_name,
                        last_name=last_name,
                    )
                else:
                    u = User.objects.get(email=email)
                    u.role = role
                    u.set_password(password)
                    u.save()
            created_accounts.append((email, role, password, cedula))
            return u

        # 1) Admin principal (superusuario)
        admin = create_user(
            email='admin@admin.com',
            password='admin123',
            cedula='900000',
            role='administrativo',
            first_name='Admin',
            last_name='Principal',
            is_staff=True,
            is_superuser=True,
        )

        # 1b) Admin adicional solicitado: "admin@admin" (control total)
        admin2 = create_user(
            email='admin@admin',
            password='admin123',
            cedula='900001',
            role='administrativo',
            first_name='Admin',
            last_name='Control',
            is_staff=True,
            is_superuser=True,
        )

        # 2) Usuarios administrativos
        administrativo = create_user(
            email='administrativo@vg360.local',
            password='123456',
            cedula='100001',
            role='administrativo',
            first_name='Ana',
            last_name='Admin',
        )
        analista1 = create_user(
            email='analista1@vg360.local',
            password='123456',
            cedula='100002',
            role='administrativo',
            first_name='Alex',
            last_name='Analista',
        )
        reportes = create_user(
            email='reportes@vg360.local',
            password='123456',
            cedula='100003',
            role='administrativo',
            first_name='Rebe',
            last_name='Reportes',
        )
        soporte = create_user(
            email='soporte@vg360.local',
            password='123456',
            cedula='100004',
            role='administrativo',
            first_name='Sam',
            last_name='Soporte',
        )

        # 3) Líderes (6 en total)
        lideres = []
        for i in range(1, 7):
            lider = create_user(
                email=f'lider{i}@vg360.local',
                password='123456',
                cedula=f'20000{i}',
                role='lider',
                first_name=f'Lider{i}',
                last_name='Equipo',
            )
            lideres.append(lider)

        # 4) Negociadores por líder (3 cada uno)
        nego_counter = 300001
        all_negociadores = []
        for lider in lideres:
            for suf in ['A', 'B', 'C']:
                n, _ = Negotiator.objects.get_or_create(
                    leader=lider,
                    name=f'Negociador {suf} de {lider.first_name}',
                    defaults={'cedula': str(nego_counter)}
                )
                # si ya existe, asegurar cédula consistente
                if not n.cedula:
                    n.cedula = str(nego_counter)
                    n.save()
                all_negociadores.append(n)
                nego_counter += 1

        # 5) Indicadores históricos (últimos 12 meses, 1 punto por mes)
        for n in all_negociadores:
            for i in range(12):
                date = (timezone.now().date() - timedelta(days=30 * i))
                NegotiatorIndicator.objects.update_or_create(
                    negotiator=n,
                    date=date,
                    defaults={
                        'conversion_de_ventas': round(uniform(20, 85), 2),
                        'recaudacion_mensual': randint(800_000, 8_000_000),
                        'tiempo_hablando': round(uniform(20, 160), 1),
                        'porcentajes_cumplimiento_recaudo': round(uniform(60, 100), 2),
                        'porcentaje_cumplimiento_conversion': round(uniform(60, 100), 2),
                        'porcentaje_caidas_acuerdos': round(uniform(5, 25), 2),
                    }
                )

        # 6) Crear una evaluación de Hacer y del Ser reciente por negociador
        kpi_map = {
            'Conversión de Ventas': 'conversion_de_ventas',
            'Porcentajes de Cumplimiento de Recaudo': 'porcentajes_cumplimiento_recaudo',
            'Porcentaje de Cumplimiento de Conversión': 'porcentaje_cumplimiento_conversion',
            'Porcentaje de Caídas de Acuerdos': 'porcentaje_caidas_acuerdos',
        }
        percentage_kpis = {k.name: k for k in KPI.objects.filter(name__in=list(kpi_map.keys()))}
        for n in all_negociadores:
            latest = n.indicators.order_by('-date').first()
            if latest:
                overall = n.calcular_puntuacion_hacer() or 0.0
                ev = Evaluation.objects.create(
                    negotiator=n,
                    evaluator=n.leader,
                    overall_score=overall,
                    feedback='Buen avance general. Seguir fortaleciendo conversión y recaudo.'
                )
                for kpi_name, field in kpi_map.items():
                    if field and hasattr(latest, field):
                        EvaluationKPI.objects.create(
                            evaluation=ev,
                            kpi=percentage_kpis[kpi_name],
                            score=getattr(latest, field)
                        )
                # Evaluación del Ser
                SerEvaluation.objects.create(
                    negotiator=n,
                    evaluator=n.leader,
                    actitud=randint(3, 5),
                    trabajo_en_equipo=randint(3, 5),
                    sentido_pertenencia=randint(3, 5),
                    relacionamiento=randint(3, 5),
                    compromiso=randint(3, 5),
                )

        # 7) Escribir archivo de credenciales
        base_dir = Path(__file__).resolve().parents[3]
        out = base_dir / 'usuarios_credenciales.txt'
        # Quitar duplicados por email si el comando corre varias veces
        uniq = {}
        for email, role, password, cedula in created_accounts:
            uniq[email] = (email, role, password, cedula)
        with out.open('w', encoding='utf-8') as f:
            f.write('USUARIOS DE DEMO - Vision Gerencial 360\n')
            f.write('IMPORTANTE: Ambiente de desarrollo. Contraseñas simples.\n\n')
            f.write('Correo; Rol; Cédula; Contraseña\n')
            for email, role, password, cedula in uniq.values():
                f.write(f'{email}; {role}; {cedula}; {password}\n')
        self.stdout.write(self.style.SUCCESS(f'Usuarios y datos de demo creados. Credenciales en {out}'))
