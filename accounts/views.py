#accounts
from .utils import decode_base64
import json
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView, View
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.contrib.auth import authenticate, login 
from django.contrib import messages
from attendance.models import AttendanceEvent
from django.utils.timezone import localtime
from .forms import LoginForm
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
    template_name = "profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # دریافت تمام رویدادهای حضور کاربر
        events = AttendanceEvent.objects.filter(user=user)
        
        # سازماندهی حضور روزانه
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

        # آخرین 10 حضور
        recent_attendance = []
        for day in sorted_days[:10]:
            recent_attendance.append({
                'date': day,
                'check_in': daily_attendance[day]['check_in'],
                'check_out': daily_attendance[day]['check_out']
            })
        context['recent_attendance'] = recent_attendance

        # آماده سازی داده برای Chart.js (آخرین 7 روز)
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
    
# class LogoutView(View):
#     authentication_classes = [TokenAuthentication]
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         request.user.auth_token.delete()
#         return redirect('')
    
# class CreateUser(APIView):
#     permission_classes = [IsAuthenticated, (IsNormalAdmin | IsSuperAdmin)]

#     def post(self, request):
#         if not request.data:
#             return Response({"debug_error": "Request Data is EMPTY in View"}, status=400)
#         if request.data.get("first_name") is None:
#             return Response({"debug_error": "First Name is NONE"}, status=400)
#         first_name = request.data.get("first_name")
#         last_name = request.data.get("last_name")
#         nationality_number = request.data.get("nationality_number")
#         requested_role = request.data.get("roles", "user")
#         fingerprints = request.data.get("fingerprints", [])

#         if not all([first_name, last_name, nationality_number]):
#             return Response({"error": "first_name, last_name, nationality_number required"}, status=400)
#         if CustomUser.objects.filter(nationality_number=nationality_number).exists():
#             return Response({"error": "User already exists"}, status=400)

#         if request.user.roles == 'normal_admin':
#             role = 'user'
#             company = request.user.company
#         elif request.user.roles == 'super_admin':
#             role = requested_role
#             company_id = request.data.get("company_id")
#             if not company_id:
#                 return Response({"error": "Super admin must provide company_id"}, status=400)
#             company = get_object_or_404(Company, id=company_id)
#         else:
#             return Response({"error": "Invalid role"}, status=403)

#         random_password = get_random_string(length=10)
#         user = CustomUser.objects.create_user(
#             nationality_number=nationality_number,
#             password=random_password,
#             first_name=first_name,
#             last_name=last_name,
#             company=company,
#             roles=role,
#         )

#         for fp in fingerprints:
#             finger_name = fp.get('finger_name')
#             template_data_base64 = fp.get('template_data')
#             binary_data = decode_base64(template_data_base64)
#             if binary_data is None:
#                 return Response({"error": f"Invalid Base64 data for finger {finger_name}"}, status=400)

#             Fingerprint.objects.create(
#                 user=user,
#                 finger_name=finger_name,
#                 template_data=binary_data
#             )

#         return Response({
#             "message": "User created",
#             "nationality_number": user.nationality_number,
#             "password": random_password,
#             "company": str(user.company)
#         }, status=201)

class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = "profile.html"

    def get(self,request,):
        context = super().get_context_data()
        user = self.request.user
        context.update({
            "nationality_number": user.nationality_number,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.roles,
            "company": user.company,
        })
        return render(request, 'profile.html', context=context)

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



# class UserListView(APIView):
#     permission_classes = [IsAuthenticated, (IsNormalAdmin | IsSuperAdmin)]

#     def get(self, request):
#         if request.user.roles == 'normal_admin':
#             users = CustomUser.objects.filter(company=request.user.company)
#         elif request.user.roles == 'super_admin':
#             company_id = request.query_params.get("company_id")
#             if company_id:
#                 users = CustomUser.objects.filter(company_id=company_id)
#             else:
#                 users = CustomUser.objects.all()
#         data = [{
#             "nationality_number": u.nationality_number,
#             "first_name": u.first_name,
#             "last_name": u.last_name,
#             "roles": u.roles,
#             "company": str(u.company) if u.company else None
#         } for u in users]
#         return Response(data, status=200)


# class UserDetailView(APIView):
#     permission_classes = [IsAuthenticated, (IsNormalAdmin | IsSuperAdmin)]

#     def get(self, request, nationality_number):
#         user = get_object_or_404(CustomUser, nationality_number=nationality_number)
#         if request.user.roles == 'normal_admin' and user.company != request.user.company:
#             return Response({"error": "No permission"}, status=403)
#         return Response({
#             "nationality_number": user.nationality_number,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "roles": user.roles,
#             "company": str(user.company) if user.company else None
#         })
#     def delete(self, request, nationality_number):
#         user = get_object_or_404(CustomUser, nationality_number=nationality_number)
#         if request.user.roles == 'normal_admin' and user.company != request.user.company:
#             return Response({"error": "No permission"}, status=403)
#         user.delete()
#         return Response({"message": "User deleted"}, status=204)


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
    

