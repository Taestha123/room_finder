from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from functools import wraps

import os

from django.db import transaction
from django.db.models import F, Q
from django.urls import reverse
from accounts.models import User
from listings.models import (
    Listing, ListingImage, ListingDocument, ListingFacility,
    Advertisement, Favorite, Report,
)
from listings.nepal_data import PROVINCE_DISTRICTS
from .forms import ListingForm, FacilityForm

from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse

def home(request):
    listings = Listing.objects.filter(status='approved').select_related('owner').prefetch_related('images')

    query = request.GET.get('q', '').strip()
    province = request.GET.get('province', '')
    district = request.GET.get('district', '')
    room_types = request.GET.getlist('room_type')
    facility_filters = request.GET.getlist('facility')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    sort_by = request.GET.get('sort', 'latest')

    if query:
        listings = listings.filter(Q(title__icontains=query) | Q(location__icontains=query))
    if province:
        listings = listings.filter(province=province)
    if district:
        listings = listings.filter(district=district)
    if room_types:
        listings = listings.filter(room_type__in=room_types)

    if facility_filters:
        facility_field_map = {
            'car_parking': 'facility__car_parking',
            'bike_parking': 'facility__bike_parking',
            'wifi': 'facility__wifi',
            'drinking_water': 'facility__drinking_water',
            'water_24_7': 'facility__water_24_7',
            'attached_bathroom': 'facility__attached_bathroom',
            'kitchen': 'facility__kitchen',
            'pet_allowed': 'facility__pet_allowed',
        }
        for key in facility_filters:
            field = facility_field_map.get(key)
            if field:
                listings = listings.filter(**{field: True})
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
        'selected_room_types': room_types,
        'selected_facilities': facility_filters,
        'min_price': min_price,
        'max_price': max_price,
        'selected_sort': sort_by,
        'province_districts_json': PROVINCE_DISTRICTS,
    }
    return render(request, 'core/home.html', context)

def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.prefetch_related('images'),
        pk=pk,
        status='approved',
    )
    # Count a view once per visitor session, and never the owner's own visits.
    if not (request.user.is_authenticated and request.user == listing.owner):
        viewed = request.session.get('viewed_listings', [])
        if pk not in viewed:
            Listing.objects.filter(pk=pk).update(view_count=F('view_count') + 1)
            viewed.append(pk)
            request.session['viewed_listings'] = viewed

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
            recipient_list=[settings.CONTACT_RECEIVER_EMAIL],
        )
        submitted = True

    return render(request, 'core/contact.html', {'submitted': submitted})

# ----------------------------------------------------------------------
# Landlord dashboard
# ----------------------------------------------------------------------

LANDLORD_TABS = ('listings', 'add', 'documents')
MAX_IMAGES_PER_LISTING = 8
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}
DOC_EXTS = IMAGE_EXTS | {'.pdf'}


def landlord_required(view_func):
    """Like @login_required, but sends non-landlords back to their own dashboard."""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if request.user.role != 'landlord':
            return redirect('core:dashboard')
        return view_func(request, *args, **kwargs)
    return _wrapped


def _validate_uploads(files, allowed_exts, check_image=False):
    """Returns a list of human-readable problems (empty list = all good)."""
    problems = []
    for f in files:
        ext = os.path.splitext(f.name)[1].lower()
        if ext not in allowed_exts:
            problems.append(f'"{f.name}": unsupported file type.')
        elif f.size > MAX_UPLOAD_BYTES:
            problems.append(f'"{f.name}" is larger than 5 MB.')
        elif check_image and ext != '.pdf':
            from PIL import Image
            try:
                Image.open(f).verify()
            except Exception:
                problems.append(f'"{f.name}" is not a valid image.')
            finally:
                f.seek(0)
    return problems


def _save_images(listing, files):
    has_primary = listing.images.filter(is_primary=True).exists()
    for index, f in enumerate(files):
        ListingImage.objects.create(
            listing=listing,
            image=f,
            is_primary=(not has_primary and index == 0),
        )


def _landlord_context(user, active_tab='listings', listing_form=None,
                      facility_form=None, file_errors=None):
    listings = list(
        Listing.objects.filter(owner=user)
        .prefetch_related('images', 'documents')
        .order_by('-created_at')
    )
    for listing in listings:
        images = list(listing.images.all())
        listing.cover = images[0] if images else None
        docs = {}
        for doc in listing.documents.all():
            docs[doc.doc_type] = doc
        listing.doc_slots = [
            {'type': code, 'label': label, 'doc': docs.get(code)}
            for code, label in ListingDocument.DOC_TYPE_CHOICES
        ]

    stats = {
        'total': len(listings),
        'approved': sum(1 for l in listings if l.status == 'approved'),
        'pending': sum(1 for l in listings if l.status == 'pending'),
        'views': sum(l.view_count for l in listings),
    }
    return {
        'active_tab': active_tab,
        'my_listings': listings,
        'stats': stats,
        'listing_form': listing_form or ListingForm(initial={'province': 'Bagmati'}),
        'facility_form': facility_form or FacilityForm(),
        'file_errors': file_errors or [],
        'doc_types': ListingDocument.DOC_TYPE_CHOICES,
        'province_districts': PROVINCE_DISTRICTS,
        'max_images': MAX_IMAGES_PER_LISTING,
    }


@landlord_required
@require_POST
def landlord_add_listing(request):
    form = ListingForm(request.POST)
    facility_form = FacilityForm(request.POST)
    images = request.FILES.getlist('images')
    docs = {
        code: request.FILES.get(f'doc_{code}')
        for code, _ in ListingDocument.DOC_TYPE_CHOICES
        if request.FILES.get(f'doc_{code}')
    }

    file_errors = []
    if not images:
        file_errors.append('Add at least one photo of the room.')
    elif len(images) > MAX_IMAGES_PER_LISTING:
        file_errors.append(f'You can upload up to {MAX_IMAGES_PER_LISTING} photos.')
    file_errors += _validate_uploads(images, IMAGE_EXTS, check_image=True)
    file_errors += _validate_uploads(docs.values(), DOC_EXTS, check_image=True)

    if form.is_valid() and facility_form.is_valid() and not file_errors:
        with transaction.atomic():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.status = 'pending'
            listing.save()
            facility = facility_form.save(commit=False)
            facility.listing = listing
            facility.save()
            _save_images(listing, images)
            for code, f in docs.items():
                ListingDocument.objects.create(listing=listing, doc_type=code, file=f)
        messages.success(
            request,
            f'"{listing.title}" was submitted and is pending approval.',
        )
        return redirect(f"{reverse('core:dashboard')}?tab=listings")

    context = {'user': request.user}
    context.update(_landlord_context(
        request.user, 'add', form, facility_form, file_errors,
    ))
    return render(request, 'core/dashboard_landlord.html', context)


@landlord_required
def landlord_edit_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    listing_title = listing.title
    facility, _ = ListingFacility.objects.get_or_create(listing=listing)
    existing_images = list(listing.images.all())
    file_errors = []

    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        facility_form = FacilityForm(request.POST, instance=facility)
        new_images = request.FILES.getlist('images')
        remove_ids = {int(i) for i in request.POST.getlist('remove_images') if i.isdigit()}

        remaining = [img for img in existing_images if img.id not in remove_ids]
        if len(remaining) + len(new_images) < 1:
            file_errors.append('A listing needs at least one photo.')
        if len(remaining) + len(new_images) > MAX_IMAGES_PER_LISTING:
            file_errors.append(f'A listing can have up to {MAX_IMAGES_PER_LISTING} photos.')
        file_errors += _validate_uploads(new_images, IMAGE_EXTS, check_image=True)

        if form.is_valid() and facility_form.is_valid() and not file_errors:
            with transaction.atomic():
                listing = form.save(commit=False)
                # A rejected listing goes back into the review queue once fixed.
                if listing.status == 'rejected':
                    listing.status = 'pending'
                    listing.rejection_reason = ''
                listing.save()
                facility_form.save()
                for img in existing_images:
                    if img.id in remove_ids:
                        img.image.delete(save=False)
                        img.delete()
                _save_images(listing, new_images)
            messages.success(request, f'"{listing.title}" was updated.')
            return redirect(f"{reverse('core:dashboard')}?tab=listings")
    else:
        form = ListingForm(instance=listing)
        facility_form = FacilityForm(instance=facility)

    return render(request, 'core/landlord_listing_edit.html', {
        'user': request.user,
        'listing': listing,
        'listing_title': listing_title,
        'listing_form': form,
        'facility_form': facility_form,
        'images': existing_images,
        'file_errors': file_errors,
        'province_districts': PROVINCE_DISTRICTS,
        'max_images': MAX_IMAGES_PER_LISTING,
    })


@landlord_required
@require_POST
def landlord_upload_document(request, pk):
    listing = get_object_or_404(Listing, pk=pk, owner=request.user)
    doc_type = request.POST.get('doc_type')
    upload = request.FILES.get('file')
    back = f"{reverse('core:dashboard')}?tab=documents"

    if doc_type not in dict(ListingDocument.DOC_TYPE_CHOICES):
        messages.error(request, 'Unknown document type.')
        return redirect(back)
    if not upload:
        messages.error(request, 'Choose a file to upload.')
        return redirect(back)
    problems = _validate_uploads([upload], DOC_EXTS, check_image=True)
    if problems:
        messages.error(request, problems[0])
        return redirect(back)

    doc = listing.documents.filter(doc_type=doc_type).first()
    if doc and doc.status == 'approved':
        messages.error(request, 'That document is already approved and cannot be replaced.')
        return redirect(back)

    if doc:
        if doc.file:
            doc.file.delete(save=False)
        doc.file = upload
        doc.status = 'pending'
        doc.save()
    else:
        ListingDocument.objects.create(listing=listing, doc_type=doc_type, file=upload)
    messages.success(request, f'{dict(ListingDocument.DOC_TYPE_CHOICES)[doc_type]} uploaded for "{listing.title}".')
    return redirect(back)


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
        tab = request.GET.get('tab', 'listings')
        context.update(_landlord_context(user, tab if tab in LANDLORD_TABS else 'listings'))

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