from django import forms
from .models import CustomUser, Company, FINGER_NAMES, Address


class LoginForm(forms.Form):
    nationality_number = forms.CharField(
        label="کد ملی",
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'کد ملی',
            'autocomplete': 'off'
        })
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور',
            'autocomplete': 'off'
        })
    )
    remember_me = forms.BooleanField(
        label="مرا به خاطر بسپار",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class CustomUserForm(forms.ModelForm):
    selected_finger = forms.ChoiceField(
        choices=FINGER_NAMES,
        label="انگشت برای ثبت اثرانگشت",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'nationality_number', 'roles', 'company', 'selected_finger', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
            'nationality_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی (۱۰ رقمی)', 'dir': 'ltr'}),
            'roles': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise forms.ValidationError("وارد کردن ایمیل الزامی است.")
        return email

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        self.fields['profile_picture'].required = False
        if user and user.roles == 'normal_admin':
            self.fields['company'].queryset = Company.objects.filter(id=user.company.id, is_active=True)
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'roles', 'company']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'nationality_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی', 'dir': 'ltr'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل (اجباری)'}),
            'roles': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) 
        super().__init__(*args, **kwargs)
        
        if user and user.roles == 'normal_admin':
            self.fields['company'].queryset = Company.objects.filter(id=user.company.id, is_active=True)
        else:
            self.fields['company'].queryset = Company.objects.filter(is_active=True)



class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['title', 'address']



class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['title', 'address']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام مکان (مثلاً دفتر مرکزی)'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'آدرس کامل'}),
        }

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if Address.objects.filter(address__iexact=address).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("این آدرس قبلاً ثبت شده است.")
        return address