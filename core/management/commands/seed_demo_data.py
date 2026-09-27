from django.core.management.base import BaseCommand

from accounts.models import User
from core.models import Advertisement
from listings.models import Listing, ListingDocument


class Command(BaseCommand):
    help = 'Creates demo landlord/tenant users, listings and ad placements for local testing.'

    def handle(self, *args, **options):
        if Advertisement.objects.exists() or Listing.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Demo data already exists — skipping. Delete existing Advertisement/Listing '
                'rows first if you want to reseed.'
            ))
            return

        demo_landlords = [
            ('Rajesh Sharma', 'rajesh@demo.com', '9841000010'),
            ('Sunita Maharjan', 'sunita@demo.com', '9841000011'),
            ('Bijay Thapa', 'bijay@demo.com', '9841000012'),
            ('Anil Gurung', 'anil@demo.com', '9841000013'),
            ('Priya Shrestha', 'priya@demo.com', '9841000014'),
            ('Mohan Adhikari', 'mohan@demo.com', '9841000015'),
            ('Kamala Poudel', 'kamala@demo.com', '9841000016'),
        ]
        owners = {}
        for full_name, email, phone in demo_landlords:
            first, _, last = full_name.partition(' ')
            user, _ = User.objects.get_or_create(email=email, defaults={
                'first_name': first, 'last_name': last, 'phone': phone,
                'role': 'landlord', 'is_active': True, 'email_verified': True,
            })
            user.set_password('DemoPass123')
            user.save()
            owners[full_name] = user

        listings_data = [
            ('Modern 2BHK Flat in Lazimpat', 'Rajesh Sharma', 'flat', 'Kathmandu', 'Bagmati', 28000, 'approved'),
            ('Furnished Single Room near Patan Durbar', 'Sunita Maharjan', 'single', 'Lalitpur', 'Bagmati', 9000, 'approved'),
            ('Budget Room Near Tribhuvan University', 'Bijay Thapa', 'single', 'Kathmandu', 'Bagmati', 6500, 'pending'),
            ('Luxury 3BHK Apartment in Pulchowk', 'Anil Gurung', 'apartment', 'Lalitpur', 'Bagmati', 45000, 'approved'),
            ('Hostel Accommodation in Thamel', 'Priya Shrestha', 'hostel', 'Kathmandu', 'Bagmati', 7000, 'approved'),
            ('Family House in Pokhara Lakeside', 'Mohan Adhikari', 'house', 'Pokhara', 'Gandaki', 32000, 'approved'),
            ('2-Room Set in Butwal City Center', 'Kamala Poudel', 'rooms', 'Butwal', 'Lumbini', 11000, 'approved'),
        ]
        for title, owner_name, room_type, location, province, price, status in listings_data:
            listing = Listing.objects.create(
                owner=owners[owner_name], title=title, room_type=room_type,
                location=location, province=province, price=price, status=status,
                description=(
                    "Budget-friendly room ideal for TU students. 5-minute walk from "
                    "campus. Common kitchen available. Safe and secure building with "
                    "24-hour gate access. Ideal for focused study with a quiet environment."
                ) if status == 'pending' else 'A well-kept, verified listing on RoomFinder Nepal.',
            )
            if status == 'pending':
                for doc_type in ['citizenship_front', 'citizenship_back', 'lalpurja', 'selfie']:
                    ListingDocument.objects.create(listing=listing, doc_type=doc_type, status='pending')

        ads_data = [
            ('Homepage Top Banner', 'display_banner', '728x90', 18200),
            ('Between Listing Cards', 'banner', '336x280', 24100),
            ('Room Detail \u2014 Below Images', 'banner', '728x90', 12600),
            ('Phone Reveal (Rewarded)', 'rewarded', 'Full Screen', 69600),
        ]
        for title, ad_type, size, revenue in ads_data:
            Advertisement.objects.create(
                title=title, ad_type=ad_type, size=size, est_revenue=revenue, is_active=True,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(demo_landlords)} landlords, {len(listings_data)} listings, '
            f'{len(ads_data)} ad placements.'
        ))