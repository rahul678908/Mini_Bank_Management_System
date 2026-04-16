from rest_framework import serializers
from .models import CustomUser, BankAccount, Loan
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom fields
        data['email'] = self.user.email
        data['role'] = self.user.role
        data['customer_id'] = self.user.customer_id

        return data

class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = '__all__'


class BankAccountSerializer(serializers.ModelSerializer):
    loans = serializers.SerializerMethodField()

    class Meta:
        model = BankAccount
        fields = ['user', 'balance', 'loans']

    def get_loans(self, obj):
        loans = Loan.objects.filter(account=obj)
        return LoanSerializer(loans, many=True).data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'mobile_number', 'role', 'password']
        extra_kwargs = {'password': {'write_only': True}}