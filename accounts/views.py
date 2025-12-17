import json
from logging import INFO
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, View
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.utils.timezone import localtime, now
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from .serializers import CompanySerializer
from .models import CustomUser, Company, Fingerprint, FINGER_NAMES
from .forms import LoginForm, CustomUserForm, UserEditForm, CompanyForm
from .serializers import UserUpdateSerializer
from attendance.models import AttendanceEvent
from .utils import decode_base64
from django.urls import reverse
from datetime import timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.utils.timezone import now, localtime
from django.http import JsonResponse

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
                messages.success(request, f"ورود موفقیت‌آمیز، خوش آمدید {user.first_name}!")
                return redirect('profile')
            
            else:
                form.add_error(None, "کد ملی یا رمز عبور اشتباه است.")

        return render(request, 'login.html', {'form': form})


class LogoutView(View):
    def get(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        logout(request)
        return redirect('login')



class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "base_profile.html"  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        events = AttendanceEvent.objects.filter(user=user).order_by('timestamp')

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
        current_time = localtime(now())

        for day in sorted_days[:10]:
            check_in = daily_attendance[day]['check_in']
            check_out = daily_attendance[day]['check_out']

            if check_in and check_out:
                hours = round((check_out - check_in).total_seconds() / 3600, 2)
                status = "کامل"
            elif check_in:
                hours = round((current_time - check_in).total_seconds() / 3600, 2)
                status = "در حال کار"
            else:
                hours = 0
                status = "غایب"

            recent_attendance.append({
                'date': day,
                'check_in': check_in,
                'check_out': check_out,
                'hours': hours,
                'status': status
            })

        context['recent_attendance'] = recent_attendance

        last_7_days = sorted_days[:7][::-1]
        labels = [day.strftime("%Y-%m-%d") for day in last_7_days]
        data = []
        for day in last_7_days:
            check_in = daily_attendance[day]['check_in']
            check_out = daily_attendance[day]['check_out']
            hours = round((check_out - check_in).total_seconds() / 3600, 2) if check_in and check_out else 0
            data.append(hours)

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

        # اول کاربر رو ذخیره کن
        user = form.save()  # اینجا کاربر ذخیره می‌شه

        # پیام‌ها رو اضافه کن
        messages.success(self.request, f"کاربر «{user.first_name} {user.last_name}» با موفقیت ایجاد شد.")
        messages.add_message(self.request, messages.INFO, random_password, extra_tags='temp_password')
        messages.add_message(self.request, messages.INFO, form.cleaned_data['selected_finger'], extra_tags='selected_finger')

        # حالا ریدایرکت کن
        return redirect('show_temp_password', nationality_number=user.nationality_number)

    def form_invalid(self, form):
        messages.error(self.request, "لطفاً خطاهای فرم را برطرف کنید.")
        return super().form_invalid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  
        return kwargs

class UserListView(LoginRequiredMixin, View):
    template_name = 'users.html'
    paginate_by = 15  

    def get_queryset(self, request):
        queryset = CustomUser.objects.filter(is_active=True).select_related('company')

        if request.user.roles == 'normal_admin':
            queryset = queryset.filter(company=request.user.company)
        elif request.user.roles != 'super_admin':
            messages.error(request, "شما دسترسی به این صفحه ندارید.")
            return CustomUser.objects.none()

        q = request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(nationality_number__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                Q(company__title__icontains=q)
            )

        queryset = queryset.order_by('first_name', 'last_name')
        return queryset, q

    def get(self, request):
        queryset, search_query = self.get_queryset(request)

        paginator = Paginator(queryset, self.paginate_by)
        page = request.GET.get('page')

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)

        context = {
            'users': users,
            'search_query': search_query,
            'paginator': paginator,
            'page_obj': users,
        }
        return render(request, self.template_name, context)

class UserEditView(UpdateView):
    model = CustomUser
    form_class = UserEditForm
    template_name = "edit_user.html"
    slug_field = "nationality_number"
    slug_url_kwarg = "nationality_number"

    def get_success_url(self):
        return reverse_lazy("user-list")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # کاربر جاری رو بده
        return kwargs

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated", "data": serializer.data}, status=200)
        return Response(serializer.errors, status=400)


class UserDeleteView(LoginRequiredMixin, View):
    def post(self, request, nationality_number):
        if request.user.roles not in ["super_admin", "normal_admin"]:
            messages.error(request, "شما اجازه حذف کاربر ندارید.")
            return redirect('user-list')
        
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        
        if request.user.roles == "normal_admin" and user.company != request.user.company:
            messages.error(request, "شما فقط می‌توانید کاربران شرکت خود را حذف کنید.")
            return redirect('user-list')
        
        user.is_active = False
        user.deleted_at = now() 
        user.save()

        messages.success(request, f"کاربر «{user.first_name} {user.last_name}» با موفقیت غیرفعال شد.")
        return redirect('user-list')

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
        nationality_number = self.kwargs['nationality_number']
        finger_name = self.kwargs['finger_name']

        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        context['user'] = user
        context['selected_finger'] = finger_name
        context['finger_display'] = dict(FINGER_NAMES).get(finger_name, finger_name)
        return context

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
        now = now()
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


class ShowTempPasswordView(LoginRequiredMixin, TemplateView):
    template_name = "show_temp_password.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nationality_number = self.kwargs['nationality_number']
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)

        temp_password = "در دسترس نیست"
        selected_finger = None
        for message in messages.get_messages(self.request):
            if message.extra_tags == 'temp_password':
                temp_password = message.message
            if message.extra_tags == 'selected_finger':
                selected_finger = message.message

        context['user'] = user
        context['temp_password'] = temp_password
        context['selected_finger'] = selected_finger
        context['next_url'] = reverse('enroll_fingerprint', args=[nationality_number, selected_finger]) if selected_finger else reverse('user-list')

        return context



class ChangePasswordView(LoginRequiredMixin, View):
    template_name = "change_password.html"

    def get(self, request):
        form = PasswordChangeForm(request.user)
        response = render(request, self.template_name, {"form": form})
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            messages.success(request, "رمز عبور با موفقیت تغییر کرد.")
            return redirect("profile")

        messages.error(request, "لطفاً خطاهای فرم را بررسی کنید.")
        return render(request, self.template_name, {"form": form})
    

class CompanyListView(LoginRequiredMixin, View):
    def get(self, request):
        if request.user.roles != "super_admin":
            messages.error(request, "فقط سوپر ادمین می‌تواند شرکت‌ها را مدیریت کند.")
            return redirect('profile')

        companies = Company.objects.filter(is_active=True)  # فقط فعال‌ها
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
    def post(self, request, pk):
        if request.user.roles != "super_admin":
            return JsonResponse({"error": "فقط سوپر ادمین می‌تواند حذف کند."}, status=403)

        company = get_object_or_404(Company, pk=pk, is_active=True)

        company.is_active = False
        company.deleted_at = now()
        company.save()

        CustomUser.objects.filter(company=company).update(
            is_active=False,
            deleted_at=now()
        )

        return JsonResponse({
            "success": True,
            "message": f"شرکت «{company.title}» و کاربران آن با موفقیت غیرفعال شدند."
        })



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



class ArchivedUserListView(LoginRequiredMixin, View):
    template_name = 'archived_users.html'

    def get(self, request):
        if request.user.roles not in ['super_admin', 'normal_admin']:
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('user-list')

        users = CustomUser.objects.filter(is_active=False).select_related('company')
        if request.user.roles == 'normal_admin':
            users = users.filter(company=request.user.company)

        return render(request, self.template_name, {'users': users})
    

class ReactivateUserView(LoginRequiredMixin, View):
    def post(self, request, nationality_number):
        if request.user.roles not in ['super_admin', 'normal_admin']:
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('user-list')

        user = get_object_or_404(CustomUser, nationality_number=nationality_number, is_active=False)
        if request.user.roles == 'normal_admin' and user.company != request.user.company:
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('user-list')

        user.is_active = True
        user.deleted_at = None
        user.save()

        messages.success(request, "کاربر با موفقیت بازیابی شد.")
        return redirect('user-list')
    

class ArchivedCompanyListView(LoginRequiredMixin, View):
    template_name = 'archived_companies.html'

    def get(self, request):
        if request.user.roles != 'super_admin':
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('company-list')

        companies = Company.objects.filter(is_active=False)
        return render(request, self.template_name, {'companies': companies})
    

class ReactivateCompanyView(LoginRequiredMixin, View):
    def post(self, request, company_id):
        if request.user.roles != 'super_admin':
            messages.error(request, "دسترسی غیرمجاز")
            return redirect('company-list')

        company = get_object_or_404(Company, id=company_id, is_active=False)
        company.is_active = True
        company.deleted_at = None
        company.save()

        messages.success(request, "شرکت با موفقیت بازیابی شد.")
        return redirect('company-list')