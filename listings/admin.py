from django.contrib import admin
from .models import Listing, ListingImage, ListingDocument, Advertisement, ListingFacility, Favorite, Report

admin.site.register(Listing)
admin.site.register(ListingImage)
admin.site.register(ListingDocument)
admin.site.register(Advertisement)
admin.site.register(ListingFacility)
admin.site.register(Favorite)
admin.site.register(Report)