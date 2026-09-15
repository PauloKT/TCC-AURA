from rest_framework import serializers
from django.utils import timezone
from django.core import signing
from courses.models import TurmaAluno
from .models import SessaoChamada, Presenca
from .geolocation import validate_coordinates


class SessaoChamadaSerializer(serializers.ModelSerializer):
    def validate_aula(self, aula):
        if aula.turma.materia.professor_id != self.context['request'].user.id:
            raise serializers.ValidationError('Selecione uma aula sua.')
        if self.instance and aula.pk != self.instance.aula_id:
            raise serializers.ValidationError('A aula de uma sessão não pode ser alterada.')
        return aula

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
                  'valida']
        read_only_fields = ['id', 'aluno', 'aluno_username', 'sessao_aula_titulo',
                            'registrada_em', 'localizacao_capturada_em',
                            'valida']


class PresencaCreateSerializer(serializers.Serializer):
    """
        Valida o registro de presença por QR Code e geolocalização:
            - sessao_id e token batem
            - sessão está ativa e não expirada
            - token (URL) corresponde ao token atual da sessão
            - localização determina presença ou falta ao salvar
    """
    sessao_id = serializers.IntegerField()
    token = serializers.CharField(required=False)
    comprovante = serializers.CharField(required=False, max_length=1000)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def validate(self, attrs):
        try:
            validate_coordinates(attrs['latitude'], attrs['longitude'])
        except ValueError as exc:
            raise serializers.ValidationError({'detail': str(exc)}) from exc

        sessao = SessaoChamada.objects.filter(id=attrs['sessao_id']).first()
        if not sessao:
            raise serializers.ValidationError({'sessao_id': 'Sessão não encontrada.'})

        if not TurmaAluno.objects.filter(
            turma_id=sessao.aula.turma_id, aluno=self.context['request'].user,
        ).exists():
            raise serializers.ValidationError({'detail': 'Você não está matriculado nesta turma.'})

        if not sessao.ativa:
            raise serializers.ValidationError({'detail': 'A sessão de chamada já foi encerrada.'})

        if attrs.get('comprovante'):
            try:
                leitura = signing.loads(attrs['comprovante'], salt='attendance.scan', max_age=120)
            except signing.BadSignature:
                raise serializers.ValidationError({'detail': 'Tempo para confirmar esgotado. Leia o QR Code novamente.'})
            if leitura != {'sessao': sessao.pk, 'aluno': self.context['request'].user.pk}:
                raise serializers.ValidationError({'detail': 'Comprovante de leitura inválido.'})
        elif not sessao.is_token_valid() or sessao.token_atual != attrs.get('token'):
            raise serializers.ValidationError({'detail': 'QR Code inválido ou expirado. Leia o QR Code atual.'})

        if sessao.professor_latitude is None or sessao.professor_longitude is None:
            raise serializers.ValidationError({'detail': 'A sessão não possui localização institucional válida.'})

        attrs['sessao'] = sessao
        return attrs

    def create(self, validated_data):
        aluno = self.context['request'].user
        sessao = validated_data['sessao']

        presenca, _ = Presenca.objects.get_or_create(
            sessao=sessao,
            aluno=aluno,
            defaults={
                'latitude': validated_data['latitude'],
                'longitude': validated_data['longitude'],
            },
        )
        return presenca
