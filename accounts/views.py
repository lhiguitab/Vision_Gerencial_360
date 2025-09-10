from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import Negotiator, Evaluation, KPI, EvaluationKPI, NegotiatorIndicator
from .forms import EvaluationForm

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
    return render(request, 'accounts/administrativo_dashboard.html')

@login_required
def negotiator_detail_view(request, cedula):
    negotiator = get_object_or_404(Negotiator, cedula=cedula, leader=request.user)
    last_evaluation = Evaluation.objects.filter(negotiator=negotiator).order_by('-date').first()
    context = {
        'negotiator': negotiator,
        'last_evaluation': last_evaluation
    }
    return render(request, 'accounts/negotiator_detail.html', context)