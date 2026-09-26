from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def home(request):
    return render(request, 'core/home.html')


@login_required
def dashboard(request):
    """
    Single entry point after login/signup.
    Renders a different dashboard template depending on the user's role,
    so accounts/views.py can just always redirect here.
    """
    user = request.user

    if user.role == 'landlord':
        template = 'core/dashboard_landlord.html'
    elif user.role == 'admin':
        template = 'core/dashboard_admin.html'
    else:
        template = 'core/dashboard_tenant.html'

    return render(request, template, {'user': user})