from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from .models import Supplier

class SupplierBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                try:
                    Supplier.objects.get(user=user)
                    return user
                except Supplier.DoesNotExist:
                    return None
        except User.DoesNotExist:
            return None