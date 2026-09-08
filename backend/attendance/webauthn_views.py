"""
Views WebAuthn (3ª camada de segurança do AURA).

Implementa o protocolo WebAuthn (W3C / FIDO2) usando py_webauthn.

Fluxo de REGISTRO (uma vez por dispositivo):
  1. Backend  → POST /api/webauthn/register/begin/
               gera challenge e retorna o payload para navigator.credentials.create()
  2. Frontend → chama navigator.credentials.create()
  3. Backend  → POST /api/webauthn/register/complete/ com { challenge_b64, credential }
               valida a attestation e persiste a credencial

Fluxo de AUTENTICAÇÃO (a cada check-in):
  1. Backend  → POST /api/webauthn/authenticate/begin/
               gera challenge e retorna o payload para navigator.credentials.get()
  2. Frontend → chama navigator.credentials.get()
  3. Backend  → POST /api/webauthn/authenticate/complete/ com { challenge_b64, credential }
               valida a assertion e devolve um token curto de "verificado"

Importante: dados biométricos (impressão digital, Face ID) NUNCA saem do
dispositivo. Apenas a chave pública e os metadados do autenticador são persistidos.
"""
import base64
import logging

from cryptography.hazmat.primitives import serialization
from django.conf import settings as django_settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken

from webauthn import (
    create_webauthn_credentials,
    verify_create_webauthn_credentials,
    get_webauthn_credentials,
    verify_get_webauthn_credentials,
    types as webauthn_types,
)

from .models import WebAuthnCredential, WebAuthnChallenge

logger = logging.getLogger(__name__)


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64u_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s = s + '=' * padding
    return base64.urlsafe_b64decode(s)


def _get_rp() -> webauthn_types.RelyingParty:
    return webauthn_types.RelyingParty(
        id=django_settings.WEBAUTHN_RP_ID,
        name=django_settings.WEBAUTHN_RP_NAME,
        icon=None,
    )


def _get_user(aluno) -> webauthn_types.User:
    return webauthn_types.User(
        id=str(aluno.id).encode('utf-8'),
        display_name=aluno.get_full_name() or aluno.username,
        name=aluno.username,
        icon=None,
    )


class _AlunoOnlyView(APIView):
    permission_classes = [IsAuthenticated]

    def _ensure_aluno(self, request):
        if request.user.role != 'aluno':
            return Response(
                {'detail': 'Apenas alunos podem usar WebAuthn.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None


class WebAuthnRegisterBeginView(_AlunoOnlyView):
    """POST /api/webauthn/register/begin/"""

    def post(self, request):
        deny = self._ensure_aluno(request)
        if deny:
            return deny

        aluno = request.user
        existing_keys = [
            _b64u_decode(c.credential_id)
            for c in WebAuthnCredential.objects.filter(aluno=aluno)
        ]

        try:
            options, challenge_b64 = create_webauthn_credentials(
                rp=_get_rp(),
                user=_get_user(aluno),
                existing_keys=existing_keys,
                user_verification=webauthn_types.UserVerification.Required,
            )
        except Exception as e:
            logger.exception('Erro ao criar challenge WebAuthn (register)')
            return Response(
                {'detail': f'Falha ao iniciar registro: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        WebAuthnChallenge.objects.create(
            aluno=aluno,
            challenge=challenge_b64,
            tipo=WebAuthnChallenge.TIPO_REGISTRO,
        )

        return Response({
            'challenge_b64': challenge_b64,
            'options': options,
        })


class WebAuthnRegisterCompleteView(_AlunoOnlyView):
    """POST /api/webauthn/register/complete/

    Body: { "challenge_b64": "...", "credential": { id, rawId, response: { clientDataJSON, attestationObject }, type } }
    """

    def post(self, request):
        deny = self._ensure_aluno(request)
        if deny:
            return deny

        challenge_b64 = request.data.get('challenge_b64')
        credential = request.data.get('credential')
        nickname = request.data.get('nickname', '')[:80]

        if not challenge_b64 or not credential:
            return Response(
                {'detail': 'Campos "challenge_b64" e "credential" são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        challenge_record = WebAuthnChallenge.objects.select_related('aluno').filter(
            challenge=challenge_b64, consumido=False
        ).first()
        if (
            not challenge_record
            or challenge_record.aluno_id != request.user.id
            or challenge_record.is_expired()
        ):
            return Response(
                {'detail': 'Challenge inválido ou expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            verification = verify_create_webauthn_credentials(
                rp=_get_rp(),
                challenge_b64=challenge_b64,
                client_data_b64=credential['response']['clientDataJSON'],
                attestation_b64=credential['response']['attestationObject'],
                fido_metadata=None,
                user_verification_required=True,
            )
        except Exception as e:
            logger.warning('WebAuthn register verify falhou: %s', e)
            return Response(
                {'detail': f'Falha na verificação: {e}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # O credential_id vem do payload do cliente (já em base64url)
        cred_id_b64 = credential['id']
        # A chave pública vem como objeto cryptography; serializa para SPKI-DER
        try:
            pubkey_der = verification.public_key.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        except Exception:
            # Fallback: usa PEM
            pubkey_der = verification.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        pubkey_b64 = base64.b64encode(pubkey_der).decode('ascii')

        WebAuthnCredential.objects.update_or_create(
            credential_id=cred_id_b64,
            defaults={
                'aluno': request.user,
                'public_key': pubkey_b64,
                'public_key_alg': verification.public_key_alg,
                'sign_count': verification.sign_count,
                'nickname': nickname,
            },
        )

        challenge_record.consumido = True
        challenge_record.save(update_fields=['consumido'])

        return Response(
            {'detail': 'Credencial registrada com sucesso.', 'credential_id': cred_id_b64},
            status=status.HTTP_201_CREATED,
        )


class WebAuthnAuthenticateBeginView(_AlunoOnlyView):
    """POST /api/webauthn/authenticate/begin/"""

    def post(self, request):
        deny = self._ensure_aluno(request)
        if deny:
            return deny

        aluno = request.user
        creds = list(WebAuthnCredential.objects.filter(aluno=aluno))
        if not creds:
            return Response(
                {'detail': 'Nenhuma credencial WebAuthn cadastrada. Registre primeiro.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing_keys = [_b64u_decode(c.credential_id) for c in creds]

        try:
            options, challenge_b64 = get_webauthn_credentials(
                rp=_get_rp(),
                existing_keys=existing_keys,
                user_verification=webauthn_types.UserVerification.Required,
            )
        except Exception as e:
            logger.exception('Erro ao iniciar autenticação WebAuthn')
            return Response(
                {'detail': f'Falha ao iniciar autenticação: {e}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        WebAuthnChallenge.objects.create(
            aluno=aluno,
            challenge=challenge_b64,
            tipo=WebAuthnChallenge.TIPO_AUTENTICACAO,
        )

        return Response({
            'challenge_b64': challenge_b64,
            'options': options,
        })


class WebAuthnAuthenticateCompleteView(_AlunoOnlyView):
    """POST /api/webauthn/authenticate/complete/

    Sucesso: devolve um JWT curto (5 min) com a flag webauthn_verified=True,
    que o aluno envia no endpoint /api/presenca/registrar/.
    """

    def post(self, request):
        deny = self._ensure_aluno(request)
        if deny:
            return deny

        challenge_b64 = request.data.get('challenge_b64')
        credential = request.data.get('credential')

        if not challenge_b64 or not credential:
            return Response(
                {'detail': 'Campos "challenge_b64" e "credential" são obrigatórios.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        challenge_record = WebAuthnChallenge.objects.select_related('aluno').filter(
            challenge=challenge_b64, consumido=False
        ).first()
        if (
            not challenge_record
            or challenge_record.aluno_id != request.user.id
            or challenge_record.is_expired()
        ):
            return Response(
                {'detail': 'Challenge inválido ou expirado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stored = WebAuthnCredential.objects.get(credential_id=credential['id'])
        except WebAuthnCredential.DoesNotExist:
            return Response(
                {'detail': 'Credencial desconhecida.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Carrega a chave pública do armazenamento (DER ou PEM)
        pubkey_raw = stored.public_key.encode('ascii')
        try:
            pubkey_obj = serialization.load_der_public_key(pubkey_raw)
        except Exception:
            try:
                pubkey_obj = serialization.load_pem_public_key(pubkey_raw)
            except Exception as e:
                return Response(
                    {'detail': f'Chave pública inválida: {e}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        try:
            verification = verify_get_webauthn_credentials(
                rp=_get_rp(),
                challenge_b64=challenge_b64,
                client_data_b64=credential['response']['clientDataJSON'],
                authenticator_b64=credential['response']['authenticatorData'],
                signature_b64=credential['response']['signature'],
                sign_count=stored.sign_count,
                pubkey_alg=stored.public_key_alg,
                pubkey=pubkey_obj,
                user_verification_required=True,
            )
        except Exception as e:
            logger.warning('WebAuthn auth verify falhou: %s', e)
            return Response(
                {'detail': f'Falha na verificação: {e}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.utils import timezone
        stored.sign_count = verification.sign_count
        stored.ultimo_uso_em = timezone.now()
        stored.save(update_fields=['sign_count', 'ultimo_uso_em'])

        challenge_record.consumido = True
        challenge_record.save(update_fields=['consumido'])

        # Token curto de 5 min para usar no registro de presença
        token = AccessToken()
        token['user_id'] = request.user.id
        token['role'] = request.user.role
        token['webauthn_verified'] = True
        token.set_exp(from_now=True, lifetime=300)

        return Response({
            'detail': 'Verificação biométrica confirmada.',
            'webauthn_token': str(token),
        })
