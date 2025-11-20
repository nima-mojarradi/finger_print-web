from rest_framework import serializers
from accounts.models import Fingerprint
from .models import AttendanceEvent


class FingerprintSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Fingerprint
        fields = ['id', 'user', 'user_full_name']

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"



class AttendanceEventSerializer(serializers.ModelSerializer):
    user_full_name = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceEvent
        fields = [
            'id',
            'user',
            'user_full_name',
            'event_type',
            'verified_by',
            'device_id',
            'timestamp',
            'formatted_time',
        ]

    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_formatted_time(self, obj):
        return obj.timestamp.strftime("%Y-%m-%d %H:%M:%S")
