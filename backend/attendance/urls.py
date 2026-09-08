from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SessaoChamadaViewSet, PresencaCreateView
from .webauthn_views import (
    WebAuthnRegisterBeginView,
    WebAuthnRegisterCompleteView,
    WebAuthnAuthenticateBeginView,
    WebAuthnAuthenticateCompleteView,
)

router = DefaultRouter()
router.register(r'sessoes', SessaoChamadaViewSet, basename='sessao')

urlpatterns = [
    path('', include(router.urls)),
    path('presenca/registrar/', PresencaCreateView.as_view({'post': 'create'}), name='presenca-registrar'),
    # WebAuthn (3ª camada de segurança)
    path('webauthn/register/begin/', WebAuthnRegisterBeginView.as_view(), name='webauthn-register-begin'),
    path('webauthn/register/complete/', WebAuthnRegisterCompleteView.as_view(), name='webauthn-register-complete'),
    path('webauthn/authenticate/begin/', WebAuthnAuthenticateBeginView.as_view(), name='webauthn-authenticate-begin'),
    path('webauthn/authenticate/complete/', WebAuthnAuthenticateCompleteView.as_view(), name='webauthn-authenticate-complete'),
]
