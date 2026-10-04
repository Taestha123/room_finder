from django.conf import settings
from django.db import models


class Listing(models.Model):
    ROOM_TYPE_CHOICES = (
        ('single', 'Single Room'),
        ('shared', 'Shared Room'),
        ('flat', 'Flat'),
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('hostel', 'Hostel'),
        ('rooms', 'Multiple Rooms'),
    )

    PROVINCE_CHOICES = (
        ('Koshi', 'Koshi'),
        ('Madhesh', 'Madhesh'),
        ('Bagmati', 'Bagmati'),
        ('Gandaki', 'Gandaki'),
        ('Lumbini', 'Lumbini'),
        ('Karnali', 'Karnali'),
        ('Sudurpashchim', 'Sudurpashchim'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='single')
    location = models.CharField(max_length=200, help_text='e.g. Kathmandu, Lalitpur')
    province = models.CharField(max_length=20, choices=PROVINCE_CHOICES, default='Bagmati')
    price = models.PositiveIntegerField(help_text='Monthly rent in NPR')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    rejection_reason = models.CharField(max_length=255, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ListingDocument(models.Model):
    DOC_TYPE_CHOICES = (
        ('citizenship_front', 'Citizenship Front'),
        ('citizenship_back', 'Citizenship Back'),
        ('lalpurja', 'Lalpurja'),
        ('selfie', 'Selfie'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    doc_type = models.CharField(max_length=30, choices=DOC_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='documents',
    )

    def __str__(self):
        return f'{self.get_doc_type_display()} ({self.listing_id})'


class Advertisement(models.Model):
    AD_TYPE_CHOICES = (
        ('display_banner', 'Display / Banner'),
        ('banner', 'Banner Ad'),
        ('rewarded', 'Rewarded Ad'),
    )

    title = models.CharField(max_length=120)
    ad_type = models.CharField(max_length=20, choices=AD_TYPE_CHOICES, default='banner')
    size = models.CharField(max_length=40, help_text='e.g. 728x90, 336x280, Full Screen')
    est_revenue = models.PositiveIntegerField(default=0, help_text='Estimated monthly revenue in NPR')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title

class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='listings/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', 'uploaded_at']

    def __str__(self):
        return f'Image for {self.listing.title}'

class Favorite(models.Model):
    tenant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favorites',
        limit_choices_to={'role': 'tenant'},
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='favorited_by',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('tenant', 'listing')

    def __str__(self):
        return f'{self.tenant.email} saved {self.listing.title}'

class Report(models.Model):
    REASON_CHOICES = (
        ('fake', 'Fake or misleading listing'),
        ('scam', 'Suspected scam / deposit fraud'),
        ('duplicate', 'Duplicate listing'),
        ('inappropriate', 'Inappropriate content'),
        ('other', 'Other'),
    )
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('reviewed', 'Reviewed'),
        ('dismissed', 'Dismissed'),
    )

    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Report on {self.listing.title} by {self.reporter.email}'