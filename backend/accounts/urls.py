from django.urls import path
from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    AlunoMinhaFrequenciaView,
    AlunoTurmasView,
    AlunoEntrarTurmaView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('aluno/minha-frequencia/', AlunoMinhaFrequenciaView.as_view(), name='aluno-minha-frequencia'),
    path('aluno/turmas/', AlunoTurmasView.as_view(), name='aluno-turmas'),
    path('aluno/entrar-turma/', AlunoEntrarTurmaView.as_view(), name='aluno-entrar-turma'),
]
