from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0006_listing_available_from_listing_bills_electricity_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='listingdocument',
            name='file',
            field=models.FileField(blank=True, upload_to='documents/'),
        ),
    ]