from rest_framework import serializers
from core import models as core_models
from userauths import models as userauths_models

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(max_length=1000)

    class Meta:
        fields = ['file']

class BeneficiarySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="beneficiary_user.email", read_only=True)
    wallet_id = serializers.CharField(source="beneficiary_user.wallet.wallet_id", read_only=True)

    class Meta:
        model = core_models.Beneficiary
        fields = ["id", "name", "email", "wallet_id", "created_at"]

    def get_name(self, obj):
        kyc = getattr(obj.beneficiary_user, "kyc_profile", None)
        return (
            getattr(kyc, "full_name", None)
            or obj.beneficiary_user.username
            or obj.beneficiary_user.email
            or "Unknown"
        )
    
class WalletSerializer(serializers.Serializer):
    class Meta:
        model = core_models.Wallet
        fields = "__all__"

class MiniUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = userauths_models.User
        fields = ["id", "username", "email"]

class TransactionSerializer(serializers.ModelSerializer):
    wallet_id = serializers.CharField(source="wallet.wallet_id", read_only=True)
    sender = MiniUserSerializer(read_only=True)
    receiver = MiniUserSerializer(read_only=True)

    class Meta:
        model = core_models.Transaction
        fields = (
            "transaction_type",
            "status",
            "amount",
            "reference",
            "external_reference",
            "wallet_id",
            "sender",
            "receiver",
            "timestamp",
        )