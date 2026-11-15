
from django import forms

from listings.models import Listing, ListingFacility
from listings.nepal_data import PROVINCE_DISTRICTS


class ListingForm(forms.ModelForm):
    district = forms.CharField(
        widget=forms.Select(choices=[('', 'Select district')]),
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'room_type', 'price', 'security_deposit', 'available_from',
            'province', 'district', 'city_vdc', 'location', 'ward_number', 'exact_address',
            'latitude', 'longitude',
            'bills_water', 'bills_electricity', 'bills_internet',
            'description', 'house_rules',
        ]
        labels = {
            'title': 'Property title',
            'room_type': 'Property type',
            'price': 'Monthly rent (NPR)',
            'security_deposit': 'Security deposit (NPR)',
            'available_from': 'Available from',
            'city_vdc': 'City / VDC',
            'location': 'Area / Tole',
            'ward_number': 'Ward no.',
            'exact_address': 'Exact address / landmark',
            'bills_water': 'Water',
            'bills_electricity': 'Electricity',
            'bills_internet': 'Internet',
            'description': 'Description (min. 100 characters)',
            'house_rules': 'House rules',
        }
        help_texts = {'location': ''}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Modern 2BHK Flat in Lazimpat'}),
            'price': forms.NumberInput(attrs={'min': 1, 'placeholder': '15000'}),
            'security_deposit': forms.NumberInput(attrs={'min': 0, 'placeholder': '0'}),
            'available_from': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'city_vdc': forms.TextInput(attrs={'placeholder': 'e.g. Pokhara Metropolitan City'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Lakeside, Baidam'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
            'ward_number': forms.TextInput(attrs={'placeholder': '4'}),
            'exact_address': forms.TextInput(attrs={'placeholder': 'Shown only to verified tenants'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your property in detail...'}),
            'house_rules': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. No smoking, quiet after 10 PM.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True
        self.fields['city_vdc'].required = True

        self.fields['room_type'].choices = [('', 'Select type...')] + list(Listing.ROOM_TYPE_CHOICES)

        if not self.instance.pk and not self.is_bound:
            self.initial['room_type'] = ''

        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'ld-input'

        province_value = (
            self.data.get(self.add_prefix('province'))
            if self.is_bound else self.initial.get('province', self.instance.province or 'Bagmati')
        )

        district_choices = PROVINCE_DISTRICTS.get(province_value, [])

        self.fields['district'].choices = [('', 'Select...')] + [
            (district, district) for district in district_choices
        ]

        self.fields['district'].widget.attrs['data-selected'] = self['district'].value() or ''

    def clean_description(self):
        description = self.cleaned_data['description'].strip()

        if not self.instance.pk and len(description) < 100:
            raise forms.ValidationError(
                f'Please write at least 100 characters (you have {len(description)}).'
            )

        return description

    def clean_price(self):
        price = self.cleaned_data['price']

        if price < 1:
            raise forms.ValidationError('Enter a rent greater than 0.')

        return price

    def clean_district(self):
        district = self.cleaned_data['district']
        province = self.cleaned_data.get('province')

        if province and district not in PROVINCE_DISTRICTS.get(province, []):
            raise forms.ValidationError(
                'Pick a district that belongs to the selected province.'
            )

        return district


class FacilityForm(forms.ModelForm):
    class Meta:
        model = ListingFacility
        exclude = ['listing']

        labels = {
            'furnished_status': 'Furnishing',
            'car_parking': '🚗 Car Parking',
            'bike_parking': '🏍️ Bike Parking',
            'wifi': '📶 WiFi',
            'drinking_water': '💧 Drinking Water',
            'water_24_7': '🚰 24/7 Water',
            'attached_bathroom': '🚿 Attached Bathroom',
            'kitchen': '🍳 Kitchen',
            'balcony': '🏗️ Balcony',
            'cctv': '📹 CCTV',
            'security_guard': '💂 Security Guard',
            'pet_allowed': '🐾 Pet Allowed',
            'laundry': '👕 Laundry',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['furnished_status'].widget.attrs['class'] = 'ld-input'

    def checkbox_fields(self):
        return [f for f in self if f.name != 'furnished_status']
