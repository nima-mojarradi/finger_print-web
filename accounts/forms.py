from django import forms
from .models import CustomUser, Company, FINGER_NAMES


class LoginForm(forms.Form):
    nationality_number = forms.CharField(
        label="کد ملی",
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی'})
    )
    password = forms.CharField(
        label="رمز عبور",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'})
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
        fields = ['first_name', 'last_name', 'nationality_number', 'roles', 'company', 'selected_finger']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام خانوادگی'}),
            'nationality_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'کد ملی (۱۰ رقمی)', 'dir': 'ltr'}),
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

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'roles', 'company']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
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
