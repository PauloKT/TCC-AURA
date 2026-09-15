# Interface AURA

## Análise e direção

O projeto utiliza cinco páginas HTML, APIs DRF com JWT, CSS e JavaScript sem build. As páginas eram servidas como arquivos estáticos apenas em DEBUG. Os modelos já oferecem CRUD e o registro de presença preserva o primeiro resultado de GPS por chamada. A frequência conta sessões de chamada, incluindo sessões abertas. Esse cálculo permanece intacto.

Paleta: azul acadêmico #183b56, verde petróleo #176b60, névoa #f3f6f8, branco #ffffff, texto #203346, alerta #915c13. Tipografia: Segoe UI Variable/Segoe UI para títulos e corpo, sem download de fontes. Layout alinhado à esquerda, menu compacto e área de trabalho ampla.

```
Menu | Barra de contexto e perfil
     | Título e ação principal
     | Resumo compacto
     | Agenda / turmas e atividade
```

Revisão do conceito: evitar cards idênticos em toda a página. Usar faixas de indicadores, listas de aulas e painéis com funções distintas. Reservar a composição mais marcante para a autenticação e o foco de projeção para o QR Code.

## Integração

Templates Django compartilham base, navegação e perfil. Os endereços .html existentes são preservados. Os arquivos JS e CSS são carregados por static. Em produção é necessário servir STATIC_ROOT pelo servidor web, como em qualquer implantação Django.

As rotas /api/interface/perfil/ e /api/interface/painel/ são somente leitura, autenticadas e limitadas ao professor responsável ou ao aluno matriculado. Os relatórios reutilizam frequency_result, sem nova regra de frequência. Não existem recuperação de senha ou validação Wi-Fi implementadas; a interface não promete essas funções.
