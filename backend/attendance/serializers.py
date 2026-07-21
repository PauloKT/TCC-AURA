from rest_framework import serializers
from .models import SessaoChamada, Presenca
from django.utils import timezone

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
                  'registrada_em', 'latitude', 'longitude', 'localizacao_capturada_em', 'valida']
        read_only_fields = ['id', 'aluno', 'aluno_username', 'sessao_aula_titulo',
                            'registrada_em', 'localizacao_capturada_em', 'valida']