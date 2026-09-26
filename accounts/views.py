from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings

from .forms import RegistrationForm, EmailLoginForm
from .models import User, OTPVerification


def _send_otp(user):
    otp = OTPVerification.objects.create(user=user, code=OTPVerification.generate_code())
    send_mail(
        subject='Your Room Finder verification code',
        message=f'Your verification code is: {otp.code}\nThis code expires in 5 minutes.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.set_password(form.cleaned_data['password1'])
            user.is_active = False
            user.email_verified = False
            user.save()

            _send_otp(user)
            request.session['pending_user_id'] = user.id
            return redirect('accounts:verify_otp')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def verify_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('accounts:register')

    if request.method == 'POST':
        entered_code = request.POST.get('otp_code', '')
        latest_otp = user.otp_codes.order_by('-created_at').first()

        if not latest_otp:
            messages.error(request, 'No verification code found. Please request a new one.')
        elif latest_otp.is_expired():
            messages.error(request, 'Your code has expired. Please request a new one.')
        elif latest_otp.code != entered_code:
            messages.error(request, 'Incorrect code. Please try again.')
        else:
            user.email_verified = True
            user.is_active = True
            user.save()
            del request.session['pending_user_id']
            login(request, user)
            messages.success(request, 'Your account has been verified!')
            return redirect('core:dashboard')

    return render(request, 'accounts/verify_otp.html', {'email': user.email})


def resend_otp(request):
    user_id = request.session.get('pending_user_id')
    if not user_id:
        return redirect('accounts:register')
    user = User.objects.get(id=user_id)
    _send_otp(user)
    messages.success(request, 'A new code has been sent to your email.')
    return redirect('accounts:verify_otp')


def login_view(request):
    if request.method == 'POST':
        form = EmailLoginForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('core:dashboard')
    else:
        form = EmailLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('core:home')