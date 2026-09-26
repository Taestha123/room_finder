from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from accounts.models import User


def home(request):
    return render(request, 'core/home.html')


def admin_required(view_func):
    """
    Like @login_required, but also bounces non-admins back to their
    own dashboard instead of showing them the admin panel.
    """
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != 'admin':
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------------------------------------------------------------------
# MOCK DATA matching the Figma admin panel design.
# Once listings.models has a real Listing model, delete everything in this
# section and replace it with real querysets, e.g.:
#   total_listings      = Listing.objects.count()
#   approved_listings   = Listing.objects.filter(status='approved').count()
#   pending_qs          = Listing.objects.filter(status='pending')
#   pending_listings_count = pending_qs.count()
# ---------------------------------------------------------------------------

def _admin_overview_stats():
    return {
        'total_listings': 8,
        'approved_listings': 7,
        'pending_listings_count': 1,
        'total_users': User.objects.count(),
    }


MOCK_PENDING_LISTINGS = [
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
]

MOCK_ALL_LISTINGS = [
    {'title': 'Modern 2BHK Flat in Lazimpat', 'room_type': 'Flat',
     'owner': 'Rajesh Sharma', 'location': 'Kathmandu', 'rent': 'NPR 28,000', 'status': 'approved'},
    {'title': 'Furnished Single Room near Patan Durbar', 'room_type': 'Single Room',
     'owner': 'Sunita Maharjan', 'location': 'Lalitpur', 'rent': 'NPR 9,000', 'status': 'approved'},
    {'title': 'Budget Room Near Tribhuvan University', 'room_type': 'Single Room',
     'owner': 'Bijay Thapa', 'location': 'Kathmandu', 'rent': 'NPR 6,500', 'status': 'pending'},
    {'title': 'Luxury 3BHK Apartment in Pulchowk', 'room_type': 'Apartment',
     'owner': 'Anil Gurung', 'location': 'Lalitpur', 'rent': 'NPR 45,000', 'status': 'approved'},
    {'title': 'Hostel Accommodation in Thamel', 'room_type': 'Hostel',
     'owner': 'Priya Shrestha', 'location': 'Kathmandu', 'rent': 'NPR 7,000', 'status': 'approved'},
    {'title': 'Family House in Pokhara Lakeside', 'room_type': 'House',
     'owner': 'Mohan Adhikari', 'location': 'Kaski', 'rent': 'NPR 32,000', 'status': 'approved'},
    {'title': '2-Room Set in Butwal City Center', 'room_type': '2 Rooms',
     'owner': 'Kamala Poudel', 'location': 'Rupandehi', 'rent': 'NPR 11,000', 'status': 'approved'},
]
# ---------------------------------------------------------------------------


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
        context.update(_admin_overview_stats())
        context['active_page'] = 'pending'
        context['pending_listings'] = MOCK_PENDING_LISTINGS

    else:
        template = 'core/dashboard_tenant.html'

    return render(request, template, context)


@admin_required
def admin_listings(request):
    context = _admin_overview_stats()
    context.update({
        'user': request.user,
        'active_page': 'listings',
        'listings': MOCK_ALL_LISTINGS,
    })
    return render(request, 'core/admin_listings.html', context)