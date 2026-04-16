from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


# ---------------- USER MANAGER ----------------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, mobile_number, role, password=None):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            mobile_number=mobile_number,
            role=role
        )

        # AUTO CUSTOMER ID GENERATION (atomic-safe using select_for_update pattern)
        if role == "customer":
            from django.db import transaction
            with transaction.atomic():
                last_user = CustomUser.objects.select_for_update().filter(
                    role="customer"
                ).order_by("-id").first()
                if last_user and last_user.customer_id:
                    last_number = int(last_user.customer_id.replace("CUST", ""))
                    new_id = f"CUST{last_number + 1}"
                else:
                    new_id = "CUST1001"
            user.customer_id = new_id

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, mobile_number, password):
        user = self.create_user(email, mobile_number, "manager", password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


# ---------------- USER MODEL ----------------
class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
    ]

    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15)
    customer_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['mobile_number']


# ---------------- BANK ACCOUNT ----------------
class BankAccount(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)


# ---------------- LOAN ----------------
class Loan(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),    
        ('completed', 'Completed'),
    ]

    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')