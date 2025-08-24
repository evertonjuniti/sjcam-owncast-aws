# Configuração do Cognito
![Owncast-Cognito.drawio.svg](/Images/Owncast-Cognito.drawio.svg)

- No Cognito na region que você escolheu (o mesmo da VPC e Subnets), vá ao menu User pools e crie um novo user pool
  - Application type: Single-page application (SPA)
  - Name your application: dê um nome para sua aplicação (no meu exemplo ficou Owncast SPA app)
  - Options for sign-in identifiers: Email e Username
  - Required attributes for sign-up: email (não haverá a opção de sign-up, mas esse campo é obrigatório o preenchimento)
  - Deixe os demais campos default e crie o user directory
  - Vá até o final da página e clique no botão Go to Overview
    - #### Em User pool information, tome nota do User pool ID
  - Vá para o menu App clientes deste user pool
    - #### Tome nota do valor da coluna Client ID
  - Vá para o menu Users deste user pool
    - Clique no botão Create user
    - Alias attributes used to sign in: deixe a opção Email marcada
    - Invitation message: Don't send an invitation
    - User name: escolha um nome de usuário
    - Email address: inclua o seu e-mail
    - Mark email address as verified: deixe marcado
    - Phone number - optional: é opcional, pode deixar vazio se quiser
    - Mark phone number as verified: é opcional também
    - Temporary password: Set a password
    - Password: escolha uma senha temporária, será necessário fazer o login uma primeira vez para trocar a senha, mas isso será visto na sessão de disponibilização da página de acesso aos vídeos
    - #### Repita este processo de criação de usuários para todos os usuários que deseje incluir
  - Vá para o menu Sign-up
    - Ao final da página em Self-service sign-up, clique no botão Edit
    - Em self-registration, Enable self-registration: deixe desmarcado e salve as alterações

---
[⬅️ Anterior: Criação das Secrets](09-Secrets.md) | [🏠 Índice](../README.md) | [Próximo: Configuração da função Lambda ➡️](11-Lambda.md)