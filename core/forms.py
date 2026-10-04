from django import forms

from listings.models import Listing, ListingFacility
from listings.nepal_data import PROVINCE_DISTRICTS


class ListingForm(forms.ModelForm):
    # Options are filled in by JS from the selected province; the server
    # re-validates the choice in clean_district().
    district = forms.CharField(
        widget=forms.Select(choices=[('', 'Select district')]),
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'room_type', 'price', 'security_deposit', 'available_from',
            'province', 'district', 'location', 'ward_number', 'exact_address',
            'bills_water', 'bills_electricity', 'bills_internet',
            'description', 'house_rules',
        ]
        labels = {
            'title': 'Listing title',
            'room_type': 'Room type',
            'price': 'Monthly rent (NPR)',
            'security_deposit': 'Security deposit (NPR)',
            'available_from': 'Available from',
            'location': 'Area / City',
            'ward_number': 'Ward no.',
            'exact_address': 'Exact address / landmark',
            'bills_water': 'Water',
            'bills_electricity': 'Electricity',
            'bills_internet': 'Internet',
            'house_rules': 'House rules',
        }
        help_texts = {'location': ''}
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Modern 2BHK Flat in Lazimpat'}),
            'price': forms.NumberInput(attrs={'min': 1, 'placeholder': '15000'}),
            'security_deposit': forms.NumberInput(attrs={'min': 0, 'placeholder': '0'}),
            'available_from': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'location': forms.TextInput(attrs={'placeholder': 'e.g. Lazimpat, Kathmandu'}),
            'ward_number': forms.TextInput(attrs={'placeholder': '4'}),
            'exact_address': forms.TextInput(attrs={'placeholder': 'Shown only to verified tenants'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the room, the neighbourhood and who it suits.'}),
            'house_rules': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g. No smoking, quiet after 10 PM.'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = True
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'ld-input'
        self.fields['district'].widget.attrs['data-selected'] = self['district'].value() or ''

    def clean_price(self):
        price = self.cleaned_data['price']
        if price < 1:
            raise forms.ValidationError('Enter a rent greater than 0.')
        return price

    def clean_district(self):
        district = self.cleaned_data['district']
        province = self.cleaned_data.get('province')
        if province and district not in PROVINCE_DISTRICTS.get(province, []):
            raise forms.ValidationError('Pick a district that belongs to the selected province.')
        return district


class FacilityForm(forms.ModelForm):
    class Meta:
        model = ListingFacility
        exclude = ['listing']
        labels = {
            'furnished_status': 'Furnishing',
            'car_parking': 'Car parking',
            'bike_parking': 'Bike parking',
            'wifi': 'Wi-Fi',
            'drinking_water': 'Drinking water',
            'water_24_7': '24/7 water',
            'attached_bathroom': 'Attached bathroom',
            'kitchen': 'Kitchen',
            'balcony': 'Balcony',
            'cctv': 'CCTV',
            'security_guard': 'Security guard',
            'pet_allowed': 'Pets allowed',
            'laundry': 'Laundry',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['furnished_status'].widget.attrs['class'] = 'ld-input'

    def checkbox_fields(self):
        return [f for f in self if f.name != 'furnished_status']