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
    
    # Obtener los KPIs de la última evaluación si existe
    evaluation_kpis = []
    if last_evaluation:
        evaluation_kpis = last_evaluation.kpis.all().select_related('kpi')
    
    context = {
        'negotiator': negotiator,
        'last_evaluation': last_evaluation,
        'evaluation_kpis': evaluation_kpis,
        'has_evaluations': negotiator.has_evaluations(),
        'evaluation_count': negotiator.get_evaluation_count()
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
    
    # Validar que no haya una evaluación reciente (menos de 7 días)
    recent_evaluation = negotiator.evaluations.filter(
        date__gte=timezone.now() - timezone.timedelta(days=7)
    ).first()
    
    if recent_evaluation:
        messages.warning(request, f'Ya existe una evaluación reciente para {negotiator.name} del {recent_evaluation.date.strftime("%d/%m/%Y")}. No se puede crear una nueva evaluación tan pronto.')
        return redirect('negotiator_detail', cedula=cedula)
    
    if request.method == 'POST':
        form = EvaluationForm(request.POST)
        if form.is_valid():
            # Crear la evaluación
            evaluation = Evaluation.objects.create(
                negotiator=negotiator,
                evaluator=request.user,
                overall_score=form.cleaned_data['overall_score'],
                feedback=form.cleaned_data['feedback']
            )
            
            # Crear los EvaluationKPI
            for field_name, value in form.cleaned_data.items():
                if field_name.startswith('kpi_') and value is not None:
                    kpi_id = field_name.split('_')[1]
                    kpi = KPI.objects.get(id=kpi_id)
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
        'form': form,
        'has_recent_evaluation': recent_evaluation is not None,
        'recent_evaluation': recent_evaluation
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
    
    # Preparar datos para los gráficos
    data = {
        'labels': [],
        'conversion_rate': [],
        'total_revenue': [],
        'absenteeism_rate': [],
        'call_duration': [],
        'calls_made': [],
        'deals_closed': [],
        'deals_failed': [],
        'success_rate': [],
        'revenue_per_call': []
    }
    
    for indicator in indicators:
        data['labels'].append(indicator.date.strftime('%Y-%m-%d'))
        data['conversion_rate'].append(indicator.conversion_rate)
        data['total_revenue'].append(indicator.total_revenue)
        data['absenteeism_rate'].append(indicator.absenteeism_rate)
        data['call_duration'].append(indicator.call_duration)
        data['calls_made'].append(indicator.calls_made)
        data['deals_closed'].append(indicator.deals_closed)
        data['deals_failed'].append(indicator.deals_failed)
        data['success_rate'].append(indicator.success_rate)
        data['revenue_per_call'].append(indicator.revenue_per_call)
    
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