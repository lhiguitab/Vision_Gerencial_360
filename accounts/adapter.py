
from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # Evitar username autogenerado; usamos email como USERNAME_FIELD.
        return

    def save_user(self, request, user, form, commit=True):
        """Asegura que la cédula (PK) esté presente ANTES del primer guardado.

        Esto evita el error de login: "Save with update_fields did not affect any rows"
        causado por actualizar last_login cuando el PK cambia tras el primer save.
        """
        user = super().save_user(request, user, form, commit=False)
        cedula = form.cleaned_data.get('cedula')
        if cedula:
            user.cedula = cedula
        # Campos opcionales
        user.first_name = form.cleaned_data.get('first_name', user.first_name)
        user.last_name = form.cleaned_data.get('last_name', user.last_name)
        if commit:
            user.save()
        return user
