from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from functools import wraps

from django.db.models import Q
from accounts.models import User
from listings.models import Listing, Advertisement, Favorite, Report

from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse

def home(request):
    listings = Listing.objects.filter(status='approved').select_related('owner').prefetch_related('images')

    query = request.GET.get('q', '').strip()
    province = request.GET.get('province', '')
    room_type = request.GET.get('room_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'latest')

    if query:
        listings = listings.filter(Q(title__icontains=query) | Q(location__icontains=query))
    if province:
        listings = listings.filter(province=province)
    if room_type:
        listings = listings.filter(room_type=room_type)
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)

    if sort_by == 'price_low':
        listings = listings.order_by('price')
    elif sort_by == 'price_high':
        listings = listings.order_by('-price')
    else:
        listings = listings.order_by('-created_at')
    favorited_ids = set()
    if request.user.is_authenticated and request.user.role == 'tenant':
        favorited_ids = set(
            Favorite.objects.filter(tenant=request.user).values_list('listing_id', flat=True)
        )

    context = {
        'listings': listings,
        'favorited_ids': favorited_ids,
        'province_choices': Listing.PROVINCE_CHOICES,
        'room_type_choices': Listing.ROOM_TYPE_CHOICES,
        'query': query,
        'selected_province': province,
        'selected_room_type': room_type,
        'min_price': min_price,
        'max_price': max_price,
        'selected_sort': sort_by,
    }
    return render(request, 'core/home.html', context)

def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.prefetch_related('images'),
        pk=pk,
        status='approved',
    )
    is_favorited = False
    phone_revealed = False
    if request.user.is_authenticated and request.user.role == 'tenant':
        is_favorited = Favorite.objects.filter(tenant=request.user, listing=listing).exists()
        phone_revealed = pk in request.session.get('revealed_phones', [])

    return render(request, 'core/listing_detail.html', {
        'listing': listing,
        'is_favorited': is_favorited,
        'phone_revealed': phone_revealed,
    })

@login_required
@require_POST
def toggle_favorite(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status='approved')
    favorite, created = Favorite.objects.get_or_create(tenant=request.user, listing=listing)

    if not created:
        favorite.delete()
        is_saved = False
    else:
        is_saved = True

    next_url = request.POST.get('next') or 'core:home'
    messages.success(request, 'Saved to favourites.' if is_saved else 'Removed from favourites.')
    return redirect(next_url)

def report_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status='approved')
    reason = request.POST.get('reason')
    details = request.POST.get('details', '').strip()

    if not reason:
        messages.error(request, 'Please select a reason for the report.')
    else:
        Report.objects.create(listing=listing, reporter=request.user, reason=reason, details=details)
        messages.success(request, 'Thank you — your report has been submitted and will be reviewed by our team.')

    return redirect('core:listing_detail', pk=pk)

@login_required
def reveal_phone(request, pk):
    listing = get_object_or_404(Listing, pk=pk, status='approved')

    if request.user.role != 'tenant':
        return JsonResponse({'error': 'Only tenants can reveal contact numbers.'}, status=403)

    revealed = request.session.get('revealed_phones', [])
    if pk not in revealed:
        revealed.append(pk)
        request.session['revealed_phones'] = revealed

    return JsonResponse({'phone': listing.owner.phone})

def about(request):
    return render(request, 'core/about.html')

def blog(request):
    return render(request, 'core/blog.html')

def contact(request):
    submitted = False
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        send_mail(
            subject=f"[Contact Form] {subject or 'General'} — from {full_name}",
            message=f"From: {full_name} ({email})\n\n{message}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['nehabasnet77.xdezo@gmail.com'],
        )
        submitted = True

    return render(request, 'core/contact.html', {'submitted': submitted})

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


def _admin_overview_stats():
    """Real counts, pulled straight from the database."""
    return {
        'total_listings': Listing.objects.count(),
        'approved_listings': Listing.objects.filter(status='approved').count(),
        'pending_listings_count': Listing.objects.filter(status='pending').count(),
        'total_users': User.objects.count(),
    }


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
        context['pending_listings'] = (
            Listing.objects.filter(status='pending')
            .select_related('owner')
            .prefetch_related('documents')
        )

    else:
            template = 'core/dashboard_tenant.html'

            favorites = (
                Favorite.objects.filter(tenant=user)
                .select_related('listing', 'listing__owner')
                .prefetch_related('listing__images')
            )
            saved_listings = [f.listing for f in favorites]
            saved_ids = [listing.id for listing in saved_listings]

            context['saved_count'] = len(saved_listings)
            context['saved_listings'] = saved_listings
            context['recommended_listings'] = (
                Listing.objects.filter(status='approved')
                .exclude(id__in=saved_ids)
                .select_related('owner')
                .prefetch_related('images')
                .order_by('-created_at')[:3]
            )

    return render(request, template, context)


@admin_required
def admin_listings(request):
    context = _admin_overview_stats()
    context.update({
        'user': request.user,
        'active_page': 'listings',
        'listings': Listing.objects.all().select_related('owner'),
    })
    return render(request, 'core/admin_listings.html', context)


@admin_required
def admin_listing_detail(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related('owner').prefetch_related('documents'),
        id=listing_id,
    )
    context = _admin_overview_stats()
    context.update({
        'user': request.user,
        'active_page': 'listings',
        'listing': listing,
    })
    return render(request, 'core/admin_listing_detail.html', context)


@admin_required
@require_POST
def admin_approve_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    listing.status = 'approved'
    listing.rejection_reason = ''
    listing.save(update_fields=['status', 'rejection_reason'])
    messages.success(request, f'"{listing.title}" has been approved.')
    return redirect(request.POST.get('next') or 'core:dashboard')


@admin_required
@require_POST
def admin_reject_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    listing.status = 'rejected'
    listing.rejection_reason = request.POST.get('reason', '').strip()
    listing.save(update_fields=['status', 'rejection_reason'])
    messages.success(request, f'"{listing.title}" has been rejected.')
    return redirect(request.POST.get('next') or 'core:dashboard')


@admin_required
@require_POST
def admin_remove_listing(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)
    title = listing.title
    listing.delete()
    messages.success(request, f'"{title}" has been removed.')
    return redirect('core:admin_listings')


@admin_required
def admin_users(request):
    """Real data — every registered user, newest first."""
    context = _admin_overview_stats()
    context.update({
        'user': request.user,
        'active_page': 'users',
        'users_list': User.objects.all().order_by('-date_joined'),
    })
    return render(request, 'core/admin_users.html', context)


@admin_required
@require_POST
def admin_toggle_user_status(request, user_id):
    """Flips a user's is_active flag — this is the real Suspend/Restore action."""
    target = get_object_or_404(User, id=user_id)

    if target.id == request.user.id:
        messages.error(request, "You can't suspend your own account.")
    else:
        target.is_active = not target.is_active
        target.save(update_fields=['is_active'])
        action = 'restored' if target.is_active else 'suspended'
        messages.success(request, f"{target.get_full_name()} has been {action}.")

    return redirect('core:admin_users')


@admin_required
def admin_analytics(request):
    context = _admin_overview_stats()

    # Real per-province counts of approved listings.
    province_counts = []
    for code, label in Listing.PROVINCE_CHOICES:
        count = Listing.objects.filter(province=code, status='approved').count()
        province_counts.append((label, count))
    province_counts.sort(key=lambda pair: pair[1], reverse=True)
    max_count = max((c for _, c in province_counts), default=0) or 1
    provinces = [
        {'name': name, 'count': count, 'pct': round(count / max_count * 100)}
        for name, count in province_counts
    ]

    # Real total ad revenue. Impressions/phone reveals have no tracking
    # system behind them yet, so they stay as clearly-labelled placeholders
    # until real analytics events are wired up.
    total_ad_revenue = sum(ad.est_revenue for ad in Advertisement.objects.all())
    metrics = [
        {'label': 'TOTAL AD REVENUE (EST.)', 'value': f'NPR {total_ad_revenue:,}',
         'delta': 'from active ad placements', 'positive': True},
        {'label': 'AD IMPRESSIONS', 'value': '48,320',
         'delta': 'no tracking wired up yet', 'positive': True},
        {'label': 'PHONE REVEALS', 'value': '1,247',
         'delta': 'no tracking wired up yet', 'positive': False},
    ]

    context.update({
        'user': request.user,
        'active_page': 'analytics',
        'metrics': metrics,
        'provinces': provinces,
    })
    return render(request, 'core/admin_analytics.html', context)


@admin_required
def admin_advertisements(request):
    context = _admin_overview_stats()
    context.update({
        'user': request.user,
        'active_page': 'ads',
        'ads': Advertisement.objects.all(),
    })
    return render(request, 'core/admin_advertisements.html', context)


@admin_required
def admin_ad_configure(request, ad_id):
    ad = get_object_or_404(Advertisement, id=ad_id)

    if request.method == 'POST':
        ad.title = request.POST.get('title', ad.title).strip()
        ad.size = request.POST.get('size', ad.size).strip()
        ad.est_revenue = int(request.POST.get('est_revenue') or ad.est_revenue)
        ad.is_active = request.POST.get('is_active') == 'on'
        ad.save()
        messages.success(request, f'"{ad.title}" has been updated.')
        return redirect('core:admin_advertisements')

    context = _admin_overview_stats()
    context.update({'user': request.user, 'active_page': 'ads', 'ad': ad})
    return render(request, 'core/admin_ad_configure.html', context)


@admin_required
def admin_ad_report(request, ad_id):
    ad = get_object_or_404(Advertisement, id=ad_id)
    context = _admin_overview_stats()
    context.update({'user': request.user, 'active_page': 'ads', 'ad': ad})
    return render(request, 'core/admin_ad_report.html', context)