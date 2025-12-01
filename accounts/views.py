import json
from logging import INFO
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.utils.timezone import localtime, timezone
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import CompanySerializer
from .models import CustomUser, Company, Fingerprint, FINGER_NAMES
from .forms import LoginForm, CustomUserForm, UserEditForm, CompanyForm
from .serializers import UserUpdateSerializer
from attendance.models import AttendanceEvent
from .utils import decode_base64
from datetime import timedelta


class LoginView(View):

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('profile')
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            nationality_number = form.cleaned_data.get("nationality_number")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=nationality_number, password=password)

            if user:
                login(request, user)
                messages.success(request, f"ورود موفقیت‌آمیز، خوش آمدید {user.first_name}")
                return redirect('profile')
            else:
                form.add_error(None, "کد ملی یا رمز عبور اشتباه است.")

        return render(request, 'login.html', {'form': form})


class LogoutView(View):
    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        logout(request)
        return redirect('login')  

# ---------------------- PROFILE ----------------------

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "base_profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        events = AttendanceEvent.objects.filter(user=user)        
        daily_attendance = {}
        for event in events:
            day = event.timestamp.date()
            if day not in daily_attendance:
                daily_attendance[day] = {'check_in': None, 'check_out': None}
            if event.event_type == 'in':
                if not daily_attendance[day]['check_in'] or event.timestamp < daily_attendance[day]['check_in']:
                    daily_attendance[day]['check_in'] = localtime(event.timestamp)
            elif event.event_type == 'out':
                if not daily_attendance[day]['check_out'] or event.timestamp > daily_attendance[day]['check_out']:
                    daily_attendance[day]['check_out'] = localtime(event.timestamp)

        sorted_days = sorted(daily_attendance.keys(), reverse=True)

        recent_attendance = []
        for day in sorted_days[:10]:
            recent_attendance.append({
                'date': day,
                'check_in': daily_attendance[day]['check_in'],
                'check_out': daily_attendance[day]['check_out']
            })
        context['recent_attendance'] = recent_attendance

        last_7_days = sorted_days[:7][::-1]
        if last_7_days:
            labels = [day.strftime("%Y-%m-%d") for day in last_7_days]
            data = []
            for day in last_7_days:
                check_in = daily_attendance[day]['check_in']
                check_out = daily_attendance[day]['check_out']
                hours = round((check_out - check_in).total_seconds()/3600, 2) if check_in and check_out else 0
                data.append(hours)
        else:
            labels = []
            data = []

        chart_data = {
            "labels": labels,
            "datasets": [{
                "label": "ساعات حضور",
                "data": data,
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "borderColor": "rgba(54, 162, 235, 1)",
                "borderWidth": 1
            }]
        }

        context['chart_data'] = json.dumps(chart_data)
        context['user'] = user
        return context

# ---------------------- USER MANAGEMENT ----------------------

class UserCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = "create_user.html"
    success_url = reverse_lazy('user-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fingers'] = [name for name, _ in FINGER_NAMES]
        return context

    def form_valid(self, form):
        user_request = self.request.user
        if user_request.roles == 'normal_admin':
            form.instance.roles = 'user'
            form.instance.company = user_request.company
        elif user_request.roles == 'super_admin':
            requested_role = form.cleaned_data.get('roles')
            company = form.cleaned_data.get('company')
            form.instance.roles = requested_role
            if not company:
                form.add_error('company', 'سوپر ادمین باید شرکت را انتخاب کند.')
                return self.form_invalid(form)
        else:
            form.add_error(None, 'شما اجازه ایجاد کاربر ندارید.')
            return self.form_invalid(form)

        random_password = get_random_string(length=12)
        form.instance.set_password(random_password)
        form.instance.is_active = True
        response = super().form_valid(form)

        messages.success(
            self.request,
            f"کاربر «{form.instance.first_name} {form.instance.last_name}» با موفقیت ایجاد شد."
        )
        messages.add_message(
            self.request,
            INFO,
            random_password,
            extra_tags='show_password'
        )

        # ریدایرکت به صفحه ثبت اثرانگشت
        return redirect('enroll_fingerprint', nationality_number=form.instance.nationality_number)

    def form_invalid(self, form):
        messages.error(self.request, "لطفاً خطاهای فرم را برطرف کنید.")
        return super().form_invalid(form)

class UserListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.roles == 'normal_admin':
            users = CustomUser.objects.filter(company=request.user.company)
        else:
            users = CustomUser.objects.all()
        return render(request, 'users.html', {"users": users})

class UserEditView(UpdateView):
    model = CustomUser
    form_class = UserEditForm
    template_name = "edit_user.html"
    slug_field = "nationality_number"
    slug_url_kwarg = "nationality_number"

    def get_success_url(self):
        return reverse_lazy("user-list")

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated", "data": serializer.data}, status=200)
        return Response(serializer.errors, status=400)

    def delete(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        user.delete()
        return Response({"message": "User deleted"}, status=204)

# ---------------------- FINGERPRINT MANAGEMENT ----------------------

class AddFingerprintAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        finger_name = request.data.get("finger_name")
        template_data = request.data.get("template_data")
        if not finger_name or not template_data:
            return Response({"error": "finger_name and template_data required"}, status=400)
        binary_data = decode_base64(template_data)
        if binary_data is None:
            return Response({"error": "Invalid Base64 fingerprint data"}, status=400)

        fingerprint = Fingerprint.objects.create(
            user=user,
            finger_name=finger_name,
            template_data=binary_data
        )
        return Response({"message": "Fingerprint added", "finger_id": fingerprint.id}, status=201)

class EnrollFingerprintView(LoginRequiredMixin, TemplateView):
    template_name = "enroll_fingerprint.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nationality_number = self.kwargs.get('nationality_number')
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        context['user'] = user
        context['fingers'] = [name for name, _ in FINGER_NAMES]
        return context

# ---------------------- ATTENDANCE ----------------------

class FingerprintAttendanceView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        fingerprint_id = request.data.get("finger_id")
        device_id = request.data.get("device_id")
        if not fingerprint_id:
            return Response({"error": "finger_id is required"}, status=400)
        try:
            fingerprint = Fingerprint.objects.get(id=fingerprint_id)
        except Fingerprint.DoesNotExist:
            return Response({"error": "Fingerprint not recognized"}, status=404)
        user = fingerprint.user
        last_event = AttendanceEvent.objects.filter(user=user).order_by('-timestamp').first()
        now = timezone.now()
        if last_event and last_event.event_type == "in":
            time_diff = now - last_event.timestamp
            event_type = "out" if time_diff <= timedelta(hours=24) else "out"
        else:
            event_type = "in"
        event = AttendanceEvent.objects.create(
            user=user,
            event_type=event_type,
            verified_by="fingerprint",
            device_id=device_id,
            timestamp=now
        )
        return Response({
            "message": f"{event_type.capitalize()} recorded successfully",
            "user": f"{user.first_name} {user.last_name}",
            "timestamp": event.timestamp,
            "event_type": event.event_type,
        }, status=201)


class ChangePasswordView(LoginRequiredMixin, View):
    template_name = "change_password.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        old_password = request.POST.get("old_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")

        user = request.user

        if not all([old_password, new_password1, new_password2]):
            messages.error(request, "همه فیلدها الزامی هستند.")
            return render(request, self.template_name)

        if not user.check_password(old_password):
            messages.error(request, "رمز عبور فعلی اشتباه است.")
            return render(request, self.template_name)

        if new_password1 != new_password2:
            messages.error(request, "رمز جدید و تکرار آن یکسان نیستند.")
            return render(request, self.template_name)

        if old_password == new_password1:
            messages.error(request, "رمز جدید نمی‌تواند مشابه رمز قبلی باشد.")
            return render(request, self.template_name)

        if len(new_password1) < 8:
            messages.error(request, "رمز عبور جدید باید حداقل ۸ کاراکتر باشد.")
            return render(request, self.template_name)

        user.set_password(new_password1)
        user.save()

        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        messages.success(request, "رمز عبور با موفقیت تغییر کرد.")
        return redirect("profile") 
    

class CompanyListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.roles != "super_admin":
            messages.error(request, "فقط سوپر ادمین می‌تواند شرکت‌ها را مدیریت کند.")
            return redirect('profile')

        companies = Company.objects.all()
        return render(request, 'company_list.html', {"companies": companies})



class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = "company_create.html"
    success_url = reverse_lazy('company-list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.roles != "super_admin":
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('profile')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "شرکت با موفقیت ایجاد شد.")
        return super().form_valid(form)


class CompanyEditView(LoginRequiredMixin, UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = "company_edit.html"
    slug_field = "id"
    slug_url_kwarg = "company_id"

    def dispatch(self, request, *args, **kwargs):
        if request.user.roles != "super_admin":
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('profile')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        messages.success(self.request, "شرکت با موفقیت ویرایش شد.")
        return reverse_lazy("company-list")


class CompanyDeleteView(LoginRequiredMixin, View):
    def post(self, request, company_id):
        if request.user.roles != "super_admin":
            messages.error(request, "فقط سوپر ادمین می‌تواند حذف کند.")
            return redirect('company-list')

        company = get_object_or_404(Company, id=company_id)
        company.delete()

        messages.success(request, "شرکت با موفقیت حذف شد.")
        return redirect('company-list')



class CompanyDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        return Response({
            "id": company.id,
            "title": company.title,
            "address": company.address
        })

    def put(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Company updated", "data": serializer.data})
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        company = get_object_or_404(Company, pk=pk)
        company.delete()
        return Response({"message": "Company deleted"}, status=204)
