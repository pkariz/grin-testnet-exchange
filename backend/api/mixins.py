from django_filters import rest_framework as additional_filters
from rest_framework import authentication, filters, permissions, viewsets
from rest_framework_guardian import filters as drf_guardian_filters
from rest_framework_simplejwt.authentication import JWTAuthentication
from .permissions import ObjectPermissions


class DefaultMixin(object):
    """
    Default settings for authentication, authorization and filtering. We support
    3 types of authentication:

    1. Session authentication
    2. Basic authentication sending username/password in every request
    3. JWT authentication
    """

    paginate_by = 50
    paginate_by_param = 'page_size'

    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
        JWTAuthentication,
    )

    filter_backends = (
        additional_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
        drf_guardian_filters.ObjectPermissionsFilter,
    )
    permission_classes = [
        permissions.IsAuthenticated,
        ObjectPermissions
    ]


class CustomModelViewSet(
    DefaultMixin,
    viewsets.ModelViewSet
):
    """Default viewset for models."""
    pass



class AllowAnyRetrieveAndListMixin():
    """It must be listed before the ModelViewSet."""

    def get_permissions(self):
        """
        Get and List actions don't require view permission.

        Returns:
            list: of permission instances which are required for a given request
        """
        permission_classes = [permissions.IsAuthenticated]
        if self.action in ['retrieve', 'list']:
            # need to remove ObjectPermissionsFilter because it filters
            # queryset results by <app>.view_<model> permission
            self.filter_backends = [
                filter_backend for filter_backend in self.filter_backends
                if filter_backend != drf_guardian_filters.ObjectPermissionsFilter
            ]
        else:
            permission_classes.append(ObjectPermissions)
        return [permission() for permission in permission_classes]
