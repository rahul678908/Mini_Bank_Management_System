import logging
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import BankAccount, CustomUser, Loan
from .permissions import IsManager
from .serializers import BankAccountSerializer, CustomTokenSerializer, UserSerializer
from .tasks import apply_interest_task

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------
# LOGIN  (public — no auth required)
# ---------------------------------------------------------------
class CustomLoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = CustomTokenSerializer


# ---------------------------------------------------------------
# A. VIEW ACCOUNT  /api/account/<customer_id>/
# ---------------------------------------------------------------
class AccountDetailView(APIView):
    # FIX: explicit IsAuthenticated — unauthenticated requests now get 401
    permission_classes = [IsAuthenticated]

    def get(self, request, customer_id):
        user = request.user
        target_user = get_object_or_404(CustomUser, customer_id=customer_id)

        # Customer: only own account
        if user.role == 'customer' and user.customer_id != customer_id:
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        # Employee: cannot view other employees
        if user.role == 'employee' and target_user.role != 'customer':
            return Response(
                {"error": "Employees can only view customer accounts"},
                status=status.HTTP_403_FORBIDDEN,
            )

        account = get_object_or_404(BankAccount, user=target_user)
        serializer = BankAccountSerializer(account)

        return Response({
            "customer_id": target_user.customer_id,
            "name": target_user.email,
            "balance": account.balance,
            "loans": serializer.data['loans'],
        })


# ---------------------------------------------------------------
# B. PAY LOAN  /api/loan/pay/
# ---------------------------------------------------------------
class PayLoanView(APIView):
    # FIX: IsAuthenticated enforced
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # FIX: only customers can pay loans
        if user.role != 'customer':
            return Response(
                {"error": "Only customers can pay loans"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # FIX: validate amount exists and is a valid positive number
        raw_amount = request.data.get("amount")
        if raw_amount is None:
            return Response({"error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)

        account = get_object_or_404(BankAccount, user=user)
        loan = Loan.objects.filter(account=account, status='pending').first()

        if not loan:
            return Response({"error": "No active loan"}, status=status.HTTP_404_NOT_FOUND)

        pending = loan.total_amount - loan.amount_paid

        if amount > pending:
            return Response({"error": "Overpayment not allowed"}, status=status.HTTP_400_BAD_REQUEST)

        loan.amount_paid += amount

        if loan.amount_paid >= loan.total_amount:
            loan.status = 'completed'

        loan.save()

        return Response({
            "loan_id": loan.id,
            "pending_amount": loan.total_amount - loan.amount_paid,
        })


# ---------------------------------------------------------------
# C. APPLY INTEREST  /api/account/apply_interest/
# ---------------------------------------------------------------
class ApplyInterestView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request):
        # FIX: validate interest_percent exists and is valid
        raw_percent = request.data.get("interest_percent")
        if raw_percent is None:
            return Response(
                {"error": "interest_percent is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            percent = Decimal(str(raw_percent))
        except (InvalidOperation, ValueError):
            return Response({"error": "Invalid percentage"}, status=status.HTTP_400_BAD_REQUEST)

        if percent <= 0:
            return Response({"error": "Percentage must be positive"}, status=status.HTTP_400_BAD_REQUEST)

        # Async execution — result not immediately available
        apply_interest_task.delay(float(percent))

        return Response({
            "message": "Interest calculation started",
            "note": "Balances are being updated asynchronously. Check logs or account endpoints for results.",
        })


# ---------------------------------------------------------------
# D. CREATE USER  /api/user/create/
# ---------------------------------------------------------------
class CreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def post(self, request):
        serializer = UserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # FIX: manager cannot create another manager
        requested_role = serializer.validated_data.get('role')
        if requested_role == 'manager':
            return Response(
                {"error": "Creating manager accounts is not permitted"},
                status=status.HTTP_403_FORBIDDEN,
            )

        CustomUser.objects.create_user(
            email=serializer.validated_data['email'],
            mobile_number=serializer.validated_data['mobile_number'],
            role=requested_role,
            password=serializer.validated_data['password'],
        )

        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------
# E. APPLY LOAN  /api/loan/apply/
# ---------------------------------------------------------------
class ApplyLoanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role != 'customer':
            return Response(
                {"error": "Only customers can apply for loans"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # FIX: validate amount
        raw_amount = request.data.get("amount")
        if raw_amount is None:
            return Response({"error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            return Response({"error": "Invalid loan amount"}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Loan amount must be positive"}, status=status.HTTP_400_BAD_REQUEST)

        account, _ = BankAccount.objects.get_or_create(user=user)

        loan = Loan.objects.create(
            account=account,
            total_amount=amount,
            amount_paid=0,
            status='pending',
        )

        return Response({
            "message": "Loan applied successfully",
            "loan_id": loan.id,
        }, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------
# CUSTOMER LIST  /api/customers/
# ---------------------------------------------------------------
class CustomerListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role not in ['employee', 'manager']:
            return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)

        customers = CustomUser.objects.filter(role='customer')
        data = []
        for customer in customers:
            account, _ = BankAccount.objects.get_or_create(user=customer)
            data.append({
                "customer_id": customer.customer_id,
                "email": customer.email,
                "balance": account.balance,
            })

        return Response(data)


# ---------------------------------------------------------------
# EMPLOYEE LIST  /api/employees/
# ---------------------------------------------------------------
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        employees = CustomUser.objects.filter(role='employee')
        data = [
            {
                "email": emp.email,
                "mobile_number": emp.mobile_number,
                "role": emp.role,
            }
            for emp in employees
        ]
        return Response(data)


# ---------------------------------------------------------------
# ACCOUNT LIST  /api/accounts/
# ---------------------------------------------------------------
class AccountListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'customer':
            account = get_object_or_404(BankAccount, user=user)
            loans = Loan.objects.filter(account=account)
            return Response([{
                "customer_id": user.customer_id,
                "email": user.email,
                "balance": account.balance,
                "loans": [
                    {
                        "loan_id": loan.id,
                        "total_amount": loan.total_amount,
                        "amount_paid": loan.amount_paid,
                        "status": loan.status,
                    }
                    for loan in loans
                ],
            }])

        elif user.role in ['employee', 'manager']:
            customers = CustomUser.objects.filter(role='customer')
        else:
            return Response({"error": "Invalid role"}, status=status.HTTP_403_FORBIDDEN)

        data = []
        for customer in customers:
            account, _ = BankAccount.objects.get_or_create(user=customer)
            loans = Loan.objects.filter(account=account)
            data.append({
                "customer_id": customer.customer_id,
                "email": customer.email,
                "balance": account.balance,
                "loans": [
                    {
                        "loan_id": loan.id,
                        "total_amount": loan.total_amount,
                        "amount_paid": loan.amount_paid,
                        "status": loan.status,
                    }
                    for loan in loans
                ],
            })

        return Response(data)