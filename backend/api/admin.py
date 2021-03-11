from django.contrib import admin

from .models import Balance, Currency, Deposit, Withdrawal


class BalanceAdmin(admin.ModelAdmin):
    fields = ('currency__symbol', 'amount', 'locked_amount', 'user')
    search_fields = ('user__username', 'currency__symbol')


class CurrencyAdmin(admin.ModelAdmin):
    fields = ('name', 'symbol')


class DepositAdmin(admin.ModelAdmin):
    fields = ('currency__symbol', 'amount', 'status', 'confirmations', 'user')
    search_fields = ('user__username', 'currency__symbol', 'status')

class WithdrawalAdmin(admin.ModelAdmin):
    fields = ('currency__symbol', 'amount', 'status', 'confirmations', 'user')
    search_fields = ('user__username', 'currency__symbol', 'status')

admin.site.register(Balance, BalanceAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Deposit, DepositAdmin)
admin.site.register(Withdrawal, WithdrawalAdmin)
