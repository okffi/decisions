from django.contrib.auth import backends as auth_backends
from django.contrib.auth.models import User


class EmailModelBackend(auth_backends.ModelBackend):
    def authenticate(self, email=None, password=None, **kwargs):
        try:
            user = User._default_manager.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user (#20760).
            User().set_password(password)
