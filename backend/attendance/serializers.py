from rest_framework import serializers
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from .models import SessaoChamada, Presenca
from .geolocation import is_within_radius, validate_coordinates


class SessaoChamadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessaoChamada
        fields = ['id', 'aula', 'token_atual', 'token_expira_em', 'ativa', 'iniciada_em', 'encerrada_em',
                  'professor_latitude', 'professor_longitude', 'professor_radius_meters']
        read_only_fields = ['id', 'token_atual', 'token_expira_em', 'ativa', 'iniciada_em', 'encerrada_em',
                            'professor_latitude', 'professor_longitude', 'professor_radius_meters']


class SessaoTokenSerializer(serializers.ModelSerializer):
    segundos_restantes = serializers.SerializerMethodField()
    class Meta:
        model = SessaoChamada
        fields = ['token_atual', 'token_expira_em', 'segundos_restantes',
                  'professor_latitude', 'professor_longitude', 'professor_radius_meters']

    def get_segundos_restantes(self, obj):
        delta = obj.token_expira_em - timezone.now()
        return max(int(delta.total_seconds()), 0)


class PresencaSerializer(serializers.ModelSerializer):
    aluno_username = serializers.CharField(source='aluno.username', read_only=True)
    sessao_aula_titulo = serializers.CharField(source='sessao.aula.titulo', read_only=True)
    class Meta:
        model = Presenca
        fields = ['id', 'sessao', 'aluno', 'aluno_username', 'sessao_aula_titulo',
                  'registrada_em', 'latitude', 'longitude', 'localizacao_capturada_em',
                  'webauthn_verified', 'valida']
        read_only_fields = ['id', 'aluno', 'aluno_username', 'sessao_aula_titulo',
                            'registrada_em', 'localizacao_capturada_em',
                            'webauthn_verified', 'valida']


class PresencaCreateSerializer(serializers.Serializer):
    """
    Valida o registro de presença:
      - sessao_id e token batem
      - sessão está ativa e não expirada
      - token (URL) corresponde ao token atual da sessão
      - webauthn_token (opcional, mas recomendado) comprova a 3ª camada
    """
    sessao_id = serializers.IntegerField()
    token = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    webauthn_token = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        try:
            validate_coordinates(attrs['latitude'], attrs['longitude'])
        except ValueError as exc:
            raise serializers.ValidationError({'detail': str(exc)}) from exc

        sessao = SessaoChamada.objects.filter(id=attrs['sessao_id']).first()
        if not sessao:
            raise serializers.ValidationError({'sessao_id': 'Sessão não encontrada.'})

        if not sessao.ativa:
            raise serializers.ValidationError({'detail': 'A sessão de chamada já foi encerrada.'})

        if not sessao.is_token_valid():
            raise serializers.ValidationError({'detail': 'O QR Code expirou. Solicite um novo ao professor.'})

        if sessao.token_atual != attrs['token']:
            raise serializers.ValidationError({'detail': 'Token inválido. Pode ter expirado; escaneie o QR Code novamente.'})

        if sessao.professor_latitude is None or sessao.professor_longitude is None:
            raise serializers.ValidationError({'detail': 'A sessão não possui localização institucional válida.'})

        if not is_within_radius(
            sessao.professor_latitude,
            sessao.professor_longitude,
            attrs['latitude'],
            attrs['longitude'],
            sessao.professor_radius_meters,
        ):
            raise serializers.ValidationError({
                'detail': 'Você está fora do raio permitido para registrar presença.'
            })

        # Verifica webauthn_token (se enviado)
        webauthn_ok = False
        if attrs.get('webauthn_token'):
            try:
                token = AccessToken(attrs['webauthn_token'])
                if (token.get('user_id') == self.context['request'].user.id
                        and token.get('webauthn_verified') is True):
                    webauthn_ok = True
            except InvalidToken:
                webauthn_ok = False

        attrs['sessao'] = sessao
        attrs['webauthn_ok'] = webauthn_ok
        return attrs

    def create(self, validated_data):
        aluno = self.context['request'].user
        sessao = validated_data['sessao']

        # Já existe presença? Retorna a existente (idempotência)
        existente = Presenca.objects.filter(sessao=sessao, aluno=aluno).first()
        if existente:
            return existente

        presenca = Presenca(
            sessao=sessao,
            aluno=aluno,
            latitude=validated_data['latitude'],
            longitude=validated_data['longitude'],
            webauthn_verified=validated_data['webauthn_ok'],
        )
        presenca.save()  # save() do model recalcula .valida com base em GPS
        return presenca
