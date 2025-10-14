
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SerEvaluationForm
from .models import SerEvaluation, Negotiator

@login_required
def start_ser_evaluation_view(request, cedula):
    if request.user.role != 'lider':
        return redirect('profile')
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    if request.method == 'POST':
        form = SerEvaluationForm(request.POST)
        if form.is_valid():
            SerEvaluation.objects.create(
                negotiator=negotiator,
                evaluator=request.user,
                actitud=form.cleaned_data['actitud'],
                trabajo_en_equipo=form.cleaned_data['trabajo_en_equipo'],
                sentido_pertenencia=form.cleaned_data['sentido_pertenencia'],
                relacionamiento=form.cleaned_data['relacionamiento'],
                compromiso=form.cleaned_data['compromiso'],
            )
            messages.success(request, '¡Evaluación del Ser registrada correctamente!')
            return redirect('negotiator_detail', cedula=cedula)
    else:
        form = SerEvaluationForm()
    return render(request, 'accounts/start_ser_evaluation.html', {
        'negotiator': negotiator,
        'form': form
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from .models import Negotiator, Evaluation, KPI, EvaluationKPI, NegotiatorIndicator
from .forms import EvaluationForm
from django.db.models import Avg, Count
from django.db.models.functions import Coalesce

def home_view(request):
    return render(request, 'accounts/home.html')

@login_required
def profile_view(request):
    if request.user.role == 'lider':
        return redirect('lider_dashboard')
    else:
        return redirect('administrativo_dashboard')

@login_required
def lider_dashboard_view(request):
    negotiators = Negotiator.objects.filter(leader=request.user)
    pending_negotiators = request.user.get_negotiators_with_pending_evaluations()
    
    context = {
        'negotiators': negotiators,
        'pending_negotiators': pending_negotiators,
        'total_pending': len(pending_negotiators)
    }
    return render(request, 'accounts/lider_dashboard.html', context)

@login_required
def pending_evaluations_view(request):
    """
    Vista para mostrar las evaluaciones pendientes del líder
    """
    if request.user.role != 'lider':
        return redirect('profile')
    
    pending_negotiators = request.user.get_negotiators_with_pending_evaluations()
    
    context = {
        'pending_negotiators': pending_negotiators,
        'total_pending': len(pending_negotiators)
    }
    return render(request, 'accounts/pending_evaluations.html', context)

@login_required
def last_evaluation_view(request, cedula):
    """
    Vista para mostrar la última evaluación de un negociador
    """
    if request.user.role != 'lider':
        return redirect('profile')
    
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    last_evaluation = negotiator.get_last_evaluation()
    
    evaluation_kpis = last_evaluation.kpis.all() if last_evaluation else []
    context = {
        'negotiator': negotiator,
        'last_evaluation': last_evaluation,
        'has_evaluations': negotiator.has_evaluations(),
        'evaluation_count': negotiator.get_evaluation_count(),
        'evaluation_kpis': evaluation_kpis
    }
    return render(request, 'accounts/last_evaluation.html', context)

@login_required
def start_evaluation_view(request, cedula):
    """
    Vista para iniciar una nueva evaluación de un negociador
    """
    if request.user.role != 'lider':
        return redirect('profile')
    
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            # Crear la evaluación
            # Crear la evaluación
            # Calcular la puntuación general automáticamente
            overall_score = negotiator.calcular_puntuacion_hacer()
            evaluation = Evaluation.objects.create(
                negotiator=negotiator,
                evaluator=request.user,
                overall_score=overall_score if overall_score is not None else 0.0,
                feedback=form.cleaned_data['feedback']
            )

            # Crear EvaluationKPI para cada KPI de tipo porcentaje usando el indicador histórico más reciente
            latest_indicator = negotiator.indicators.order_by('-date').first()
            if latest_indicator:
                kpis = KPI.objects.filter(kpi_type='percentage')
                for kpi in kpis:
                    # Mapear el nombre del KPI al campo del indicador
                    kpi_field_map = {
                        'Conversión de Ventas': 'conversion_de_ventas',
                        'Porcentajes de Cumplimiento de Recaudo': 'porcentajes_cumplimiento_recaudo',
                        'Porcentaje de Cumplimiento de Conversión': 'porcentaje_cumplimiento_conversion',
                        'Porcentaje de Caídas de Acuerdos': 'porcentaje_caidas_acuerdos',
                    }
                    field_name = kpi_field_map.get(kpi.name)
                    if field_name and hasattr(latest_indicator, field_name):
                        value = getattr(latest_indicator, field_name)
                        EvaluationKPI.objects.create(
                            evaluation=evaluation,
                            kpi=kpi,
                            score=value
                        )
            
            
            messages.success(request, f'Evaluación creada exitosamente para {negotiator.name}.')
            return redirect('negotiator_detail', cedula=cedula)
    else:
        form = EvaluationForm()
    
    context = {
        'negotiator': negotiator,
        'form': form
    }
    return render(request, 'accounts/start_evaluation.html', context)

@login_required
def negotiator_indicators_view(request, cedula):
    """
    Vista para mostrar indicadores históricos y actuales del negociador
    """
    if request.user.role != 'lider':
        return redirect('profile')
    
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    
    # Obtener indicadores de los últimos 6 meses
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=180)
    
    indicators = negotiator.indicators.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Obtener indicador más reciente
    latest_indicator = negotiator.indicators.order_by('-date').first()
    
    context = {
        'negotiator': negotiator,
        'indicators': indicators,
        'latest_indicator': latest_indicator,
        'has_indicators': indicators.exists()
    }
    return render(request, 'accounts/negotiator_indicators.html', context)

@login_required
def negotiator_indicators_api(request, cedula):
    """
    API endpoint para obtener datos de indicadores en formato JSON para los gráficos
    """
    if request.user.role != 'lider':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    
    # Obtener indicadores de los últimos 6 meses
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=180)
    
    indicators = negotiator.indicators.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    # Preparar datos para los gráficos con los nuevos KPIs
    data = {
        'labels': [],
        'conversion_de_ventas': [],
        'recaudacion_mensual': [],
        'tiempo_hablando': [],
        'porcentajes_cumplimiento_recaudo': [],
        'porcentaje_cumplimiento_conversion': [],
        'porcentaje_caidas_acuerdos': []
    }

    for indicator in indicators:
        data['labels'].append(indicator.date.strftime('%Y-%m-%d'))
        data['conversion_de_ventas'].append(indicator.conversion_de_ventas)
        data['recaudacion_mensual'].append(indicator.recaudacion_mensual)
        data['tiempo_hablando'].append(indicator.tiempo_hablando)
        data['porcentajes_cumplimiento_recaudo'].append(indicator.porcentajes_cumplimiento_recaudo)
        data['porcentaje_cumplimiento_conversion'].append(indicator.porcentaje_cumplimiento_conversion)
        data['porcentaje_caidas_acuerdos'].append(indicator.porcentaje_caidas_acuerdos)
    
    return JsonResponse(data)

@login_required
def administrativo_dashboard_view(request):
    # Solo roles administrativos o superusuarios
    if request.user.role != 'administrativo' and not request.user.is_superuser:
        return redirect('profile')

    # Parámetros de filtro: año y semestre
    try:
        year = int(request.GET.get('anio') or timezone.now().year)
    except ValueError:
        year = timezone.now().year
    semestre = request.GET.get('semestre') or '1'
    if semestre not in ['1', '2']:
        semestre = '1'

    # Rango de fechas por semestre
    if semestre == '1':
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 6, 30).date()
    else:
        start_date = datetime(year, 7, 1).date()
        end_date = datetime(year, 12, 31).date()

    # Consolidar KPIs por líder en el rango
    qs = (
        NegotiatorIndicator.objects
        .filter(date__gte=start_date, date__lte=end_date)
        .values(
            'negotiator__leader__cedula',
            'negotiator__leader__first_name',
            'negotiator__leader__last_name',
            'negotiator__leader__email'
        )
        .annotate(
            equipos=Count('negotiator', distinct=True),
            avg_conversion=Avg('conversion_de_ventas'),
            avg_recaudo=Avg('recaudacion_mensual'),
            avg_tiempo=Avg('tiempo_hablando'),
            avg_cump_recaudo=Avg('porcentajes_cumplimiento_recaudo'),
            avg_cump_conv=Avg('porcentaje_cumplimiento_conversion'),
            avg_caidas=Avg('porcentaje_caidas_acuerdos'),
        )
    )

    leaders_data = []
    for row in qs:
        desempeno_componentes = []
        if row['avg_conversion'] is not None:
            desempeno_componentes.append(row['avg_conversion'])
        if row['avg_cump_recaudo'] is not None:
            desempeno_componentes.append(row['avg_cump_recaudo'])
        if row['avg_cump_conv'] is not None:
            desempeno_componentes.append(row['avg_cump_conv'])
        if row['avg_caidas'] is not None:
            desempeno_componentes.append(max(0.0, 100.0 - row['avg_caidas']))
        desempeno = round(sum(desempeno_componentes) / len(desempeno_componentes), 2) if desempeno_componentes else None
        leaders_data.append({
            'cedula': row['negotiator__leader__cedula'],
            'nombre': f"{row['negotiator__leader__first_name']} {row['negotiator__leader__last_name']}",
            'email': row['negotiator__leader__email'],
            'equipos': row['equipos'],
            'avg_conversion': row['avg_conversion'],
            'avg_recaudo': row['avg_recaudo'],
            'avg_tiempo': row['avg_tiempo'],
            'avg_cump_recaudo': row['avg_cump_recaudo'],
            'avg_cump_conv': row['avg_cump_conv'],
            'avg_caidas': row['avg_caidas'],
            'desempeno': desempeno,
        })

    # Ordenamiento
    ordenar_por = request.GET.get('ordenar_por') or 'desempeno'
    direccion = request.GET.get('direccion') or 'desc'
    reverse = True if direccion == 'desc' else False
    leaders_data.sort(key=lambda x: (x[ordenar_por] is None, x[ordenar_por]), reverse=reverse)

    context = {
        'leaders_data': leaders_data,
        # Datos para gráficos: etiquetas, conteos y porcentaje de participación
        'chart_labels': [l['nombre'] for l in leaders_data],
        'chart_counts': [l['equipos'] for l in leaders_data],
        'chart_shares': [],  # se calculará abajo
        'chart_avg_desempeno': [l['desempeno'] if l['desempeno'] is not None else 0 for l in leaders_data],
        # Promedios KPI adicionales para gráficos
        'chart_avg_recaudo': [round(l['avg_recaudo'] or 0, 2) for l in leaders_data],
        'chart_avg_tiempo': [round(l['avg_tiempo'] or 0, 2) for l in leaders_data],
        'chart_avg_conversion': [round(l['avg_conversion'] or 0, 2) for l in leaders_data],
        'chart_avg_cump_recaudo': [round(l['avg_cump_recaudo'] or 0, 2) for l in leaders_data],
        'chart_avg_cump_conv': [round(l['avg_cump_conv'] or 0, 2) for l in leaders_data],
        'chart_avg_caidas': [round(l['avg_caidas'] or 0, 2) for l in leaders_data],
        'anio': year,
        'semestre': semestre,
        'ordenar_por': ordenar_por,
        'direccion': direccion,
        'start_date': start_date,
        'end_date': end_date,
    }
    # Calcular participación relativa (porcentaje) respecto al total de negociadores
    total_negociadores = sum([l['equipos'] for l in leaders_data]) or 0
    if total_negociadores > 0:
        context['chart_shares'] = [round(100.0 * l['equipos'] / total_negociadores, 2) for l in leaders_data]
    else:
        context['chart_shares'] = [0 for _ in leaders_data]

    return render(request, 'accounts/administrativo_dashboard.html', context)

@login_required
def exportar_resultados_excel(request):
    if request.user.role != 'administrativo' and not request.user.is_superuser:
        return redirect('profile')

    try:
        year = int(request.GET.get('anio') or timezone.now().year)
    except ValueError:
        year = timezone.now().year
    semestre = request.GET.get('semestre') or '1'
    if semestre not in ['1', '2']:
        semestre = '1'
    if semestre == '1':
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year, 6, 30).date()
    else:
        start_date = datetime(year, 7, 1).date()
        end_date = datetime(year, 12, 31).date()

    # Datos consolidados
    qs = (
        NegotiatorIndicator.objects
        .filter(date__gte=start_date, date__lte=end_date)
        .values(
            'negotiator__leader__cedula',
            'negotiator__leader__first_name',
            'negotiator__leader__last_name',
            'negotiator__leader__email'
        )
        .annotate(
            equipos=Count('negotiator', distinct=True),
            avg_conversion=Avg('conversion_de_ventas'),
            avg_recaudo=Avg('recaudacion_mensual'),
            avg_tiempo=Avg('tiempo_hablando'),
            avg_cump_recaudo=Avg('porcentajes_cumplimiento_recaudo'),
            avg_cump_conv=Avg('porcentaje_cumplimiento_conversion'),
            avg_caidas=Avg('porcentaje_caidas_acuerdos'),
        )
    )

    # Generar Excel con openpyxl
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
    except Exception:
        return HttpResponse('Falta dependencia openpyxl. Instálala e inténtalo de nuevo.', status=500)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = f'Semestre {semestre} {year}'
    headers = [
        'Cédula Líder', 'Nombre Líder', 'Email', 'Negociadores',
        'Conv. Ventas (%)', 'Recaudo ($)', 'Tiempo Hablando (h)',
        'Cumpl. Recaudo (%)', 'Cumpl. Conversión (%)', 'Caídas Acuerdos (%)', 'Desempeño'
    ]
    ws.append(headers)

    for row in qs:
        desempeno_componentes = []
        if row['avg_conversion'] is not None:
            desempeno_componentes.append(row['avg_conversion'])
        if row['avg_cump_recaudo'] is not None:
            desempeno_componentes.append(row['avg_cump_recaudo'])
        if row['avg_cump_conv'] is not None:
            desempeno_componentes.append(row['avg_cump_conv'])
        if row['avg_caidas'] is not None:
            desempeno_componentes.append(max(0.0, 100.0 - row['avg_caidas']))
        desempeno = round(sum(desempeno_componentes) / len(desempeno_componentes), 2) if desempeno_componentes else None

        nombre = f"{row['negotiator__leader__first_name']} {row['negotiator__leader__last_name']}"
        ws.append([
            row['negotiator__leader__cedula'],
            nombre,
            row['negotiator__leader__email'],
            row['equipos'],
            _round(row['avg_conversion']),
            _round(row['avg_recaudo']),
            _round(row['avg_tiempo']),
            _round(row['avg_cump_recaudo']),
            _round(row['avg_cump_conv']),
            _round(row['avg_caidas']),
            _round(desempeno),
        ])

    # Ajuste simple de ancho
    for idx, _ in enumerate(headers, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = 20

    # Respuesta HTTP
    from io import BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f'resultados_semestre_{semestre}_{year}.xlsx'
    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

def _round(val):
    if val is None:
        return None
    try:
        return round(float(val), 2)
    except Exception:
        return val

@login_required
def exportar_evaluacion_pdf(request, cedula):
    # Solo líderes pueden exportar sus evaluaciones
    if request.user.role != 'lider':
        return redirect('profile')

    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    last_eval = negotiator.evaluations.order_by('-date').first()
    last_ser = negotiator.ser_evaluations.order_by('-date').first()

    if not last_eval:
        messages.warning(request, 'No hay evaluación para exportar.')
        return redirect('negotiator_detail', cedula=cedula)

    # Datos KPI de la evaluación
    kpis = list(last_eval.kpis.select_related('kpi').all())

    # Construir PDF con reportlab
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet
    except Exception:
        return HttpResponse('Falta dependencia reportlab. Instálala e inténtalo de nuevo.', status=500)

    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph('Evaluación Final con Retroalimentación', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Negociador: <b>{negotiator.name}</b> (Cédula: {negotiator.cedula})', styles['Normal']))
    story.append(Paragraph(f'Líder: <b>{request.user.first_name} {request.user.last_name}</b> ({request.user.email})', styles['Normal']))
    story.append(Paragraph(f'Fecha: {last_eval.date.strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
    story.append(Spacer(1, 12))

    # Tabla KPIs
    data = [['Indicador', 'Valor (%)']]
    for ek in kpis:
        data.append([ek.kpi.name, f"{_round(ek.score)}"])
    t = Table(data, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Porcentajes generales
    hacer_pct = _round(last_eval.overall_score)
    ser_pct = _round((last_ser.promedio * 20) if last_ser else None)
    total_pct = None
    if hacer_pct is not None and ser_pct is not None:
        total_pct = _round(hacer_pct * 0.7 + ser_pct * 0.3)

    resumen = [['Hacer (0-100)', hacer_pct], ['Ser (x20 → 0-100)', ser_pct], ['Total (70/30)', total_pct]]
    t2 = Table(resumen, hAlign='LEFT')
    t2.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(t2)
    story.append(Spacer(1, 12))

    # Retroalimentación
    if last_eval.feedback:
        story.append(Paragraph('Retroalimentación', styles['Heading3']))
        story.append(Paragraph(last_eval.feedback, styles['BodyText']))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="evaluacion_{negotiator.cedula}.pdf"'
    return response

@login_required
def negotiator_detail_view(request, cedula):
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    last_evaluation = Evaluation.objects.filter(negotiator=negotiator).order_by('-date').first()
    context = {
        'negotiator': negotiator,
        'last_evaluation': last_evaluation
    }
    return render(request, 'accounts/negotiator_detail.html', context)
