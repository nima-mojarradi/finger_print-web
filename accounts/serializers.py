import base64
from rest_framework import serializers
from .models import CustomUser, Company, Address, Fingerprint
from django.contrib.auth import get_user_model
from .utils import decode_base64
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'title', 'address']


class CompanySerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(), source='address', write_only=True
    )

    class Meta:
        model = Company
        fields = ['id', 'title', 'address', 'address_id']


CustomUser = get_user_model()

class FingerprintSerializer(serializers.Serializer):
    finger_name = serializers.CharField()
    template_data = serializers.CharField()  # Base64

class CreateUserSerializer(serializers.ModelSerializer):
    fingerprints = FingerprintSerializer(many=True, required=False)
    roles = serializers.ChoiceField(choices=[('user','User'), ('normal_admin','Normal Admin'), ('super_admin','Super Admin')], default='user')
    company_id = serializers.IntegerField(required=False)

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'nationality_number', 'roles', 'company_id', 'fingerprints']

    def validate(self, attrs):
        nationality_number = attrs.get('nationality_number')
        if CustomUser.objects.filter(nationality_number=nationality_number).exists():
            raise serializers.ValidationError("User with this nationality number already exists.")
        return attrs

    def create(self, validated_data):
        fingerprints_data = validated_data.pop('fingerprints', [])
        company_id = validated_data.pop('company_id', None)
        requested_role = validated_data.pop('roles', 'user')
        user_request = self.context['request'].user

        # تعیین نقش و شرکت
        if user_request.roles == 'normal_admin':
            role = 'user'
            company = user_request.company
        elif user_request.roles == 'super_admin':
            role = requested_role
            if not company_id:
                raise serializers.ValidationError({"company_id": "Super admin must provide company_id"})
            company = Company.objects.get(id=company_id)
        else:
            raise serializers.ValidationError("Invalid role")

        # رمز عبور تصادفی
        from django.utils.crypto import get_random_string
        random_password = get_random_string(length=10)

        # ساخت کاربر
        user = CustomUser.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            nationality_number=validated_data['nationality_number'],
            roles=role,
            company=company,
            password=random_password
        )

        # اضافه کردن اثر انگشت‌ها
        for fp in fingerprints_data:
            template_data_base64 = fp.get('template_data')
            binary_data = decode_base64(template_data_base64)
            if binary_data is None:
                raise serializers.ValidationError(f"Invalid Base64 data for finger {fp.get('finger_name')}")
            Fingerprint.objects.create(
                user=user,
                finger_name=fp.get('finger_name'),
                template_data=binary_data
            )

        user._generated_password = random_password
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'roles', 'company']
        read_only_fields = ['nationality_number']




class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ["id", "title", "address"]
