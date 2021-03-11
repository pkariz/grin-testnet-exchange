"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .api.views import (
    index_view,
    UserCreate,
    BalanceViewSet,
    CurrencyViewSet,
    DepositViewSet,
    WithdrawalViewSet,
)

router = routers.DefaultRouter()

router.register('balances', BalanceViewSet)
router.register('currencies', CurrencyViewSet)
router.register('deposits', DepositViewSet)
router.register('withdrawals', WithdrawalViewSet)

urlpatterns = [
    path('', index_view, name='index'),
    # register
    path('api/account/register/', UserCreate.as_view()),
    # login
    path('api/account/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/account/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # admin
    path('api/admin/', admin.site.urls),
    # router
    path('api/', include(router.urls)),
]


