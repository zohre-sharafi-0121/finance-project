from rest_framework import serializers
from .models import User, KYC
from django.utils import timezone

class UserRegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ("id", "email", "password")
        extra_kwargs = {
            'password': {'write_only': True}
        }

    
    def create(self, validated_data):
        email = validated_data['email']
        local_part = email.split("@")[0]
        user = User.objects.create_user(
            username=local_part,
            email=email,
            password=validated_data['password']
        )

        return user
    

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "email", "username"]


class KYCSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYC
        fields = "__all__"


class KYCCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = KYC
        fields = ["full_name", "date_of_birth", "id_type", "id_image"]
        read_only_fields = []

    def validate_date_of_birth(self, value):
        if value >= timezone.now().date():
            raise serializers.ValidationError("Date of birth must be in the past")
        return value
    
    def validate_full_name(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Full name looks too short")
        return value
    
    def create(self, validated_data):
        user = self.context["request"].user

        if hasattr(user, "kyc_profile"):
            raise serializers.ValidationError("You already submitted KYC, please contact support if you need changes")
        
        return KYC.objects.create(user=user, **validated_data)