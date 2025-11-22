from .utils import decode_base64
from django.views.generic.edit import CreateView
import json
from django.contrib.auth import logout
from .models import CustomUser, Company, Fingerprint
from .permissions import IsNormalAdmin, IsSuperAdmin, IsUser
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, View
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from .forms import UserEditForm
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login 
from django.contrib import messages
from attendance.models import AttendanceEvent
from django.utils.timezone import localtime
from .forms import LoginForm, CustomUserForm
from .serializers import UserUpdateSerializer
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


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
                messages.error(request, "کد ملی یا رمز عبور اشتباه است.")
        
        return render(request, 'login.html', {'form': form})
    

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
    
class LogoutView(View):
    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        logout(request)
        return redirect('login')  
    
class UserCreateView(LoginRequiredMixin, CreateView):
    model = CustomUser
    form_class = CustomUserForm
    template_name = "create_user.html"
    success_url = reverse_lazy('user-create')

    def form_valid(self, form):
        user_request = self.request.user
        requested_role = form.cleaned_data.get('roles')
        company = form.cleaned_data.get('company')

        if user_request.roles == 'normal_admin':
            form.instance.roles = 'user'
            form.instance.company = user_request.company
        elif user_request.roles == 'super_admin':
            form.instance.roles = requested_role
            if not company:
                form.add_error('company', 'سوپر ادمین باید شرکت را انتخاب کند.')
                return self.form_invalid(form)
        else:
            form.add_error(None, 'شما اجازه ایجاد کاربر ندارید.')
            return self.form_invalid(form)

        random_password = get_random_string(length=12)
        form.instance.set_password(random_password)

        messages.success(
            self.request,
            f"کاربر {form.instance.first_name} {form.instance.last_name} با موفقیت ایجاد شد."
        )

        messages.add_message(
            self.request, 
            messages.INFO, 
            random_password, 
            extra_tags='show_password'
        )

        return super().form_valid(form)

# class AddFingerprintView(APIView):
#     permission_classes = [IsAuthenticated, (IsNormalAdmin | IsSuperAdmin)]

#     def post(self, request, nationality_number):
#         user = get_object_or_404(CustomUser, nationality_number=nationality_number)

#         if request.user.roles == 'normal_admin' and user.company != request.user.company:
#             return Response({"error": "No permission"}, status=403)

#         finger_name = request.data.get("finger_name")
#         template_data = request.data.get("template_data")

#         if not finger_name or not template_data:
#             return Response({"error": "finger_name and template_data required"}, status=400)

#         binary_data = decode_base64(template_data)
#         if binary_data is None:
#             return Response({"error": "Invalid Base64 fingerprint data"}, status=400)

#         fingerprint = Fingerprint.objects.create(
#             user=user,
#             finger_name=finger_name,
#             template_data=binary_data
#         )

#         return Response({"message": "Fingerprint added", "finger_id": fingerprint.id}, status=201)



class UserListView(View):
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
    permission_classes = [IsAuthenticated, (IsNormalAdmin | IsSuperAdmin)]

    def put(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)

        if request.user.roles == 'normal_admin' and user.company != request.user.company:
            return Response({"error": "No permission"}, status=403)

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated", "data": serializer.data}, status=200)

        return Response(serializer.errors, status=400)
    def delete(self, request, nationality_number):
        user = get_object_or_404(CustomUser, nationality_number=nationality_number)
        if request.user.roles == 'normal_admin' and user.company != request.user.company:
            return Response({"error": "No permission"}, status=403)
        user.delete()
        return Response({"message": "User deleted"}, status=204)


# class ChangePasswordView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         old_password = request.data.get("old_password")
#         new_password = request.data.get("new_password")

#         if not old_password or not new_password:
#             return Response({"error": "old_password and new_password are required"}, status=400)

#         user = request.user

#         if not user.check_password(old_password):
#             return Response({"error": "Old password is incorrect"}, status=400)
        
#         if old_password == new_password :
#             return Response({'error':"New password and old password shouldn't be the same."}, status=400)

#         user.set_password(new_password)
#         user.save()

#         return Response({"message": "Password changed successfully"}, status=200)


# class CompanyListCreateView(APIView):
#     permission_classes = [IsAuthenticated, IsSuperAdmin]

#     def get(self, request):
#         companies = Company.objects.all()
#         data = [{"id": c.id, "title": c.title, "address": str(c.address)} for c in companies]
#         return Response(data, status=200)

#     def post(self, request):
#         title = request.data.get("title")
#         address_id = request.data.get("address_id")
#         if not all([title, address_id]):
#             return Response({"error": "title and address_id required"}, status=400)
#         address = get_object_or_404(Address, id=address_id)
#         company = Company.objects.create(title=title, address=address)
#         return Response({"message": "Company created", "id": company.id}, status=201)


# class CompanyDetailView(APIView):
#     permission_classes = [IsAuthenticated, IsSuperAdmin]

#     def get_object(self, pk):
#         return get_object_or_404(Company, pk=pk)

#     def get(self, request, pk):
#         company = self.get_object(pk)
#         return Response({"id": company.id, "title": company.title, "address": str(company.address)})

#     def put(self, request, pk):
#         company = self.get_object(pk)
#         title = request.data.get("title")
#         address_id = request.data.get("address_id")
#         if title:
#             company.title = title
#         if address_id:
#             address = get_object_or_404(Address, id=address_id)
#             company.address = address
#         company.save()
#         return Response({"message": "Company updated"})

#     def delete(self, request, pk):
#         company = self.get_object(pk)
#         company.delete()
#         return Response({"message": "Company deleted"}, status=204)
    

