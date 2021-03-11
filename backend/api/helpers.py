from guardian.shortcuts import assign_perm


def assign_default_model_permissions(user):
    default_model_perms = [
        'api.view_balance',
        'api.view_deposit',
        'api.add_deposit',
        'api.view_withdrawal',
        'api.add_withdrawal',
    ]
    for perm in default_model_perms:
        assign_perm(perm, user)
