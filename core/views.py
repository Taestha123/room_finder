from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.models import User


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
    context = {'user': user}

    if user.role == 'landlord':
        template = 'core/dashboard_landlord.html'

    elif user.role == 'admin':
        template = 'core/dashboard_admin.html'

        # 'total_users' is real — it comes straight from the accounts app.
        # The listings numbers/list below are MOCK DATA matching the Figma
        # design. Once listings.models has a real Listing model, replace
        # this whole block with real querysets, e.g.:
        #   pending_qs = Listing.objects.filter(status='pending')
        #   context['pending_listings_count'] = pending_qs.count()
        #   context['pending_listings'] = pending_qs
        #   context['total_listings'] = Listing.objects.count()
        #   context['approved_listings'] = Listing.objects.filter(status='approved').count()
        context.update({
            'total_users': User.objects.count(),
            'total_listings': 8,
            'approved_listings': 7,
            'pending_listings_count': 1,
            'pending_listings': [
                {
                    'title': 'Budget Room Near Tribhuvan University',
                    'location': 'Nayabazar, Kathmandu, Bagmati',
                    'description': (
                        "Budget-friendly room ideal for TU students. 5-minute walk "
                        "from campus. Common kitchen available. Safe and secure "
                        "building with 24-hour gate access. Ideal for focused study "
                        "with a quiet environment."
                    ),
                    'owner': 'Bijay Thapa',
                    'price': 'NPR 6,500/mo',
                    'room_type': 'Single Room',
                    'submitted': '1 month ago',
                    'documents': [
                        {'label': 'Citizenship Front', 'status': 'Pending'},
                        {'label': 'Citizenship Back', 'status': 'Pending'},
                        {'label': 'Lalpurja', 'status': 'Pending'},
                        {'label': 'Selfie', 'status': 'Pending'},
                    ],
                },
            ],
        })

    else:
        template = 'core/dashboard_tenant.html'

    return render(request, template, context)