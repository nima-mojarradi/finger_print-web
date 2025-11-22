from django import forms
from .models import CustomUser


class LoginForm(forms.Form):
    # این فیلدها مستقیماً با متغیرهای ویوی لاگین شما مطابقت دارند
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
    # توجه: رمز عبور در هنگام ذخیره باید در ویو set شود
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'nationality_number', 'roles', 'company']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality_number': forms.TextInput(attrs={'class': 'form-control'}),
            'roles': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
        }



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
