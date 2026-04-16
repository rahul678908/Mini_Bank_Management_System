from django.urls import path
from .views import *

urlpatterns = [
    path('account/apply_interest/', ApplyInterestView.as_view()),
    path('account/<str:customer_id>/', AccountDetailView.as_view()),
    path('loan/pay/', PayLoanView.as_view()),
    path('user/create/', CreateUserView.as_view()),
    path('login/', CustomLoginView.as_view()),
    path('loan/apply/', ApplyLoanView.as_view()),
    path('customers/', CustomerListView.as_view()),
    path('employees/', EmployeeListView.as_view()),
    path('accounts/', AccountListView.as_view()),
]