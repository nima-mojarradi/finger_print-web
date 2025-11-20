import base64
from rest_framework import serializers
from .models import CustomUser, Company, Address, Fingerprint

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


class FingerprintSerializer(serializers.ModelSerializer):
    template_data = serializers.CharField(write_only=True)

    class Meta:
        model = Fingerprint
        fields = ['finger_name', 'template_data', 'created_at']
        read_only_fields = ['created_at']

    def create(self, validated_data):
        template_base64 = validated_data.pop('template_data')
        validated_data['template_data'] = base64.b64decode(template_base64) 
        return Fingerprint.objects.create(**validated_data)


class CustomUserSerializer(serializers.ModelSerializer):
    fingerprints = FingerprintSerializer(many=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['nationality_number', 'first_name', 'last_name', 'roles', 'company_id', 'password', 'fingerprints']

    def create(self, validated_data):
        fingerprints_data = validated_data.pop('fingerprints', [])
        password = validated_data.pop('password')
        user = CustomUser.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        for fp_data in fingerprints_data:
            fp_data['user'] = user
            FingerprintSerializer().create(fp_data)  
        return user

