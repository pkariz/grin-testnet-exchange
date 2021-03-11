from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import Balance, Currency, Deposit, Withdrawal


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())],
        min_length=5
    )
    password = serializers.CharField(min_length=8)

    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CurrencySerializer(serializers.ModelSerializer):

    class Meta:
        model = Currency
        fields = ('name', 'symbol')


class BalanceSerializer(serializers.ModelSerializer):
    currency = CurrencySerializer()

    class Meta:
        model = Balance
        fields = ('currency', 'amount', 'locked_amount', 'user')


class DepositSerializer(serializers.ModelSerializer):
    balance = BalanceSerializer()

    class Meta:
        model = Deposit
        fields = ('balance', 'amount', 'status', 'confirmations', 'created')


class WithdrawalSerializer(serializers.ModelSerializer):
    balance = BalanceSerializer()

    class Meta:
        model = Withdrawal
        fields = ('balance', 'amount', 'status', 'confirmations', 'created')
