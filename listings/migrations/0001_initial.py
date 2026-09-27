import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Listing',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('room_type', models.CharField(choices=[('single', 'Single Room'), ('shared', 'Shared Room'), ('flat', 'Flat'), ('apartment', 'Apartment'), ('house', 'House'), ('hostel', 'Hostel'), ('rooms', 'Multiple Rooms')], default='single', max_length=20)),
                ('location', models.CharField(help_text='e.g. Kathmandu, Lalitpur', max_length=200)),
                ('province', models.CharField(choices=[('Koshi', 'Koshi'), ('Madhesh', 'Madhesh'), ('Bagmati', 'Bagmati'), ('Gandaki', 'Gandaki'), ('Lumbini', 'Lumbini'), ('Karnali', 'Karnali'), ('Sudurpashchim', 'Sudurpashchim')], default='Bagmati', max_length=20)),
                ('price', models.PositiveIntegerField(help_text='Monthly rent in NPR')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('rejection_reason', models.CharField(blank=True, max_length=255)),
                ('view_count', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='listings', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ListingDocument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('doc_type', models.CharField(choices=[('citizenship_front', 'Citizenship Front'), ('citizenship_back', 'Citizenship Back'), ('lalpurja', 'Lalpurja'), ('selfie', 'Selfie')], max_length=30)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=10)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='listings.listing')),
            ],
        ),
    ]