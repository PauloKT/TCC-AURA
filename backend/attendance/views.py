from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
import secrets
from .models import SessaoChamada, Presenca
from .serializers import SessaoChamadaSerializer, SessaoTokenSerializer, PresencaSerializer
from courses.models import Aula
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

User = get_user_model()

class IsProfessor(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'professor'

class IsAluno(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role == 'aluno'

class SessaoChamadaViewSet(viewsets.ModelViewSet):
    queryset = SessaoChamada.objects.all()
    serializer_class = SessaoChamadaSerializer
    permission_classes = [IsProfessor]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            return SessaoChamada.objects.filter(aula__turma__materia__professor=user)
        return SessaoChamada.objects.none()

    def perform_create(self, serializer):
        # Get the aula from payload
        aula_id = self.request.data.get('aula')
        aula = get_object_or_404(Aula, id=aula_id)
        professor = self.request.user
        # Determine professor location and radius
        lat = professor.latitude if professor.latitude is not None else 0.0
        lng = professor.longitude if professor.longitude is not None else 0.0
        radius = professor.radius_meters if hasattr(professor, 'radius_meters') else 100
        # Save with professor location
        serializer.save(
            aula=aula,
            professor_latitude=lat,
            professor_longitude=lng,
            professor_radius_meters=radius,
        )

    @action(detail=True, methods=['get'], url_path='token')
    def token(self, request, pk=None):
        """
        GET /api/sessoes/{id}/token/
        Returns current token, expiration, seconds remaining, and professor location.
        """
        sessao = self.get_object()
        # If token expired or not active, refresh automatically
        if not sessao.is_token_valid():
            sessao.refresh_token()
        serializer = SessaoTokenSerializer(sessao)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='encerrar')
    def encerrar(self, request, pk=None):
        """
        POST /api/sessoes/{id}/encerrar/
        Ends the session.
        """
        sessao = self.get_object()
        if not sessao.ativa:
            return Response({'detail': 'Sessão já está encerrada.'}, status=status.BAD_REQUEST)
        sessao.ativa = False
        sessao.encerrada_em = timezone.now()
        sessao.save(update_fields=['ativa', 'encerrada_em'])
        return Response({'detail': 'Sessão encerrada com sucesso.'}, status=status.OK)

class PresencaCreateView(viewsets.GenericViewSet):
    """
    POST /api/presenca/registrar/
    Expects: sessao_id, token, latitude, longitude
    """
    serializer_class = PresencaSerializer
    permission_classes = [IsAluno]

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        presenca = serializer.save()
        return Response({
            'detail': 'Presença registrada com sucesso.',
            'presenca': PresencaSerializer(presenca).data
        }, status=status.CREATED)