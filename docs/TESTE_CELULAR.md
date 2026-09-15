# Testar chamada pelo celular

O professor e o aluno devem usar o mesmo endereço HTTPS. O SQLite continua no computador.

## Preparar o acesso

1. Ative o ambiente virtual e, no diretório `backend`, execute `python manage.py prepare_local` para fazer backup e aplicar migrations. Isso já foi executado na atualização de 10/09/2026.
2. Inicie o servidor local com `python manage.py runserver 127.0.0.1:8000`.
3. Se tiver `cloudflared` instalado, em outro terminal execute `cloudflared tunnel --url http://127.0.0.1:8000`.
4. Adicione o hostname HTTPS retornado pelo túnel a `ALLOWED_HOSTS` no `.env`, separado por vírgula dos hosts locais. Use apenas o hostname, sem `https://`. Reinicie o Django após alterar o `.env`.
5. Abra esse endereço HTTPS no computador e no celular. Mantenha o servidor e o túnel em execução. O túnel de teste torna o servidor acessível pela internet enquanto estiver ativo; encerre-o após o teste.

Abrir o professor em `localhost` gera QR Codes apontando para `localhost`, que não chegam ao computador quando abertos no celular. A localização no celular também exige um contexto seguro, normalmente HTTPS.

## Professor

1. Faça login como professor pelo endereço HTTPS.
2. Escolha a matéria e a turma.
3. Copie o link do campo de convite e compartilhe com o aluno.
4. Selecione ou crie uma aula.
5. Clique em **Iniciar Chamada** e mantenha o QR Code visível. O código muda a cada 30 segundos.
6. Ao terminar, clique em **Encerrar chamada**.

## Aluno

1. Abra o convite e faça login. Se necessário, depois do cadastro abra o convite novamente.
2. No painel, confirme **Entrar na turma**.
3. Com o painel visível, aguarde o aviso da chamada. A atualização ocorre a cada cinco segundos.
4. Use a câmera do celular para ler o QR do professor. Abra o link no mesmo navegador em que fez login.
5. Permita o acesso à localização. A presença é enviada automaticamente.
6. Aguarde **Presença confirmada com sucesso!** e volte para as turmas.

Se negar a localização ou houver falha de GPS, corrija a permissão e use **Tentar novamente**. Depois de uma leitura válida, há dois minutos para concluir o GPS. Após esse prazo, leia o QR atual novamente. A chamada deve continuar aberta.

## Localização do teste

O raio é medido a partir das coordenadas da instituição cadastrada, não da posição do computador. Se a sessão usa a AEMS e você está em casa, a rejeição por distância é esperada. Para testar em outro lugar, use uma instituição de teste com coordenadas reais desse local; não altere as coordenadas oficiais da AEMS para contornar a validação.

## Casos para conferir

- Aluno sem matrícula não recebe o aviso nem pode confirmar.
- Aluno matriculado recebe aviso com o painel aberto.
- GPS dentro do raio confirma; fora do raio não grava presença.
- QR já vencido pede nova leitura.
- QR que muda após uma leitura válida não interrompe o prazo de dois minutos para GPS.
- Chamada encerrada rejeita confirmação, mesmo com leitura anterior válida.
- Presença confirmada não aparece mais como pendente e não é duplicada.

Os avisos são exibidos no painel, não como push com o navegador fechado. A imagem do QR ainda usa `api.qrserver.com`, portanto é necessária conexão com a internet.
