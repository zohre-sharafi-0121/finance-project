from django.urls import path
from core import views

urlpatterns = [
    path("upload/", views.FileUploadView.as_view()),
    path("verify/", views.VerificationAPIView.as_view()),

    path("transfer/", views.TransferFundsView.as_view()),
    path("beneficiaries/", views.BeneficiariesList.as_view()),
    path("wallet/<str:wallet_id>/", views.WalletDetail.as_view()),

    # Savings Endpoints
    path("savings-goals/create/", views.CreateSavingsGoalView.as_view()),
    path("savings-goals/deposit/", views.DepositToSavingsGoalView.as_view()),
    path("savings-goals/withdraw/", views.WithdrawFromSavingsGoalView.as_view()),
    path("savings-goals/", views.SavingsGoalListAPIView.as_view()),
    path("savings-goals/<uuid:uuid>/", views.SavingsGoalDetailAPIView.as_view()),
    
    # Dashboard overview
    path("overview/", views.OverviewAPIVIew.as_view()),

    # Transactions endpoints
    path("transactions/", views.TransactionListAPIView.as_view()),
    path("transactions/<uuid:reference>/", views.TransactionDetailAPIView.as_view()),

    path("beneficiaries/", views.BeneficiariesListAPIView.as_view(), name="beneficiaries-list"),
    path("beneficiaries/add/", views.BeneficiaryCreateAPIView.as_view(), name="beneficiary-detail"),
    path("beneficiaries/<int:pk>/", views.BeneficiaryDetailAPIView.as_view(), name="beneficiary-add"),


    path("notifications/", views.NotificationListAPIView.as_view(), name="notifications-list"),
    path("notifications/<int:pk>/read/", views.NotificationMarkReadAPIView.as_view(), name="notification-read"),
    path("notifications/read-all/", views.NotificationMarkAllReadAPIView.as_view(), name="notifications-read-all"),
]