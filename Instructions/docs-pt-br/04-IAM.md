# Configuração de policies, roles e usuário do IAM
![Owncast-IAM.drawio.svg](/Images/Owncast-IAM.drawio.svg)

- No menu Policies, crie uma nova Policy, esta será a policy principal para o Owncast
  - Ao invés de selecionar com o editor Visual, mude para o editor JSON
  - Use o template do arquivo deste repositório em [Code -> AWS_IAM -> Owncast_Policy.txt](Code/AWS_IAM/Owncast_Policy.txt)
    - Altere a tag [OwncastSegmentsBucketName] pelo nome do bucket que você criou para os arquivos de segmento de vídeo
    - Altere a tag [YourRegion] pela mesma região que está sua VPC e Subnet
    - Altere a tag [YourAccount] pelo ID de identificação da sua conta AWS (você pode ver isso na parte superior direito do Console da AWS, use somente os números)
    - Altere a tag [ProxyInstanceId] pelo ID da instância EC2 referente ao Proxy da Subnet Pública (lembra que eu indiquei você anotar essa informação!)
    - Altere a tag [OwncastInstanceId] pelo ID da instância EC2 referente ao Owncast da Subnet Privada (lembra que eu indiquei você anotar essa informação!)
    - Altere o nome da secret CloudFrontPrivateKey caso você tenha criado com outro nome na Secrets Manager (lembra que eu indiquei você anotar essa informação!)
    - Altere o nome da secret AllowedEmails caso você tenha criado com outro nome na Secrets Manager (lembra que eu indiquei você anotar essa informação!)
    - Na próxima página, dê um nome para a sua policy (no meu caso ficou o nome OwncastPolicy)

- No menu Roles, crie uma nova Role, esta será a role principal para o Owncast atrelado à Policy do Owncast
  - Trusted entity type: AWS Service
  - Use case: Lambda
  - Permission policies selecione:
    - AWSLambdaBasicExecutionRole (AWS managed)
    - O nome da Policy do Owncast, no exemplo aqui se chama OwncastPolicy (Customer managed)
    - Lembre-se de deixar checada a caixa de seleção de ambas as policies acima citadas
  - Role details:
    - Role name: dê um nome para a role (no meu caso ficou o nome OwncastLambdaS3ReadAccessRole)
    - Demais campos pode deixar os valores default

- [Opcional] Crie uma policy para poder gerar um certificado digital via Let's Encrypt para a instância de Proxy
  - Esta policy é para o caso de você ter um domínio no Route 53 e quiser validar o domínio com certificado digital ao chamar o Proxy pelo domínio
  - Ao invés de selecionar com o editor Visual, mude para o editor JSON
  - Use o template do arquivo deste repositório em [Code -> AWS_IAM -> Route53Certificate_Policy.txt](Code/AWS_IAM/Route53Certificate_Policy.txt)
    - Altere a tag [YourHostedZoneId] pelo Id da sua Hosted Zone no Route 53
    - Na próxima página, dê um nome para a sua policy (no meu caso ficou o nome OwncastProxyRoute53CertificatePolicy)

- [Opcional] Crie uma Role para poder gerar um certificado digital via Let's Encrypt para a instância de Proxy utilizando a Policy opcional
  - Trusted entity type: AWS Service
  - Use case: EC2 (na lista de opções, mantenha a opção EC2 mesmo)
  - Permission policies selecione:
    - O nome da Policy do certificado digital, no exemplo aqui se chama OwncastProxyRoute53CertificatePolicy (Customer managed)
    - Lembre-se de deixar checada a caixa de seleção da policy acima citada
  - Role details:
    - Role name: dê um nome para a role (no meu caso ficou o nome OwncastProxyRoute53CertificateRole)
    - Demais campos pode deixar os valores default

- No menu Users, crie um novo usuário
  - User name: dê algum nome (no meu exemplo ficou Owncast)
  - Provide user access to the AWS Management Console - optional: deixe desmarcado
  - Após criar o usuário, clique neste usuário recém criado para ver os detalhes
  - Na aba Security Credentials, em Access keys clique no botão Create access key
    - Use case: Third-party service (será utilizado dentro das configurações da aplicação Owncast)
    - Confirmation (I understand the above recommendation and want to proceed to create an acces key): deixe marcado
    - O resto é opcional
    - Anote o Access key
    - Na coluna Secret access key, clique em Show e anote a Secret Key
    - Você pode opcionalmente fazer o download do arquivo .csv com a informação da Access Key e Secret Key, guarde este arquivo se for optar por fazer o download
    - #### Atenção: essa será a única oportunidade para anotar a Secret Key, não clique no botão Done antes de anotar essa informação

### Observações importantes: Tome nota do nome das Policies, Roles e do User (Acces Key e Secret Key) criadas

---
[⬅️ Anterior: Criação das instâncias EC2](03-EC2-instance-creation.md) | [🏠 Índice](../README.md) | [Próximo: Connfiguração das instâncias EC2 ➡️](05-Owncast-EC2-instance-configuration.md)