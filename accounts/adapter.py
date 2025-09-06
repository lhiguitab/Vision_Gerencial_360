
from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def populate_username(self, request, user):
        # No hacemos nada aquí para evitar que se genere un username automático.
        # El username (nuestra cédula) ya se establece en el formulario.
        pass
