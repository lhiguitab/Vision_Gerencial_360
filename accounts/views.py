from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Negotiator, Evaluation

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
    return render(request, 'accounts/lider_dashboard.html', {'negotiators': negotiators})

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