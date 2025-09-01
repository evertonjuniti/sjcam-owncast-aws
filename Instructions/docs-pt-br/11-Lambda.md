# Configuração da função Lambda
![Owncast-Lambda.drawio.svg](/Images/Owncast-Lambda.drawio.svg)

### Observação importante: aqui estou assumindo que nesta parte opcional você tem um domínio próprio no Route 53, isso é importante pois a função Lambda gera Cookies e também há checagem de CORS

- Crie uma nova função Lambda na mesma Region da sua estrutura de Redes (onde você tem seu VPC e suas Subnets)
  - Escolha a opção Author from scratch
  - Function name: escolha um nome para sua função Lambda (no meu exemplo ficou owncastPlaylistGenerator, sim, o nome é horrível)
  - Runtime: escolha a opção Python (na época que eu criei estava na versão 3.13)
  - Architecture: pode ser x86_64
  - Na guia Permissions, expanda Change default execution role
    - Execution role: Use an existing role
    - Existing role: use a role que você havia criado para o Owncast (a do use case Lambda) (no meu exemplo o nome era OwncastLambdaS3ReadAccessRole)
  - Demais opções pode deixar os valores default, ao final clique no botão Create function
  - Pode ignorar a tela do Getting started caso tenha aparecido

- Antes de olharmos o código, vá na guia Configuration
  - No menu General configuration, clique no botão Edit
    - Memory: altere de 128 para 512
    - Timeout: altere de 0 min 3 sec para 0 min 10 sec (ou seja, o timeout será de 10 segundos)
    - Demais opções pode deixar como está, clique no botão Save
  - No menu Environment variables, clique no botão Edit
    - Pode clicar no botão Add environment variable 11 vezes, iremos criar 11 variáveis de ambiente. Abaixo o nome de cada variável (por favor, não mude) e a indicação do que deveria ter de valor para cada variável
      - ALLOWED_EMAILS_SECRET: [o nome que você deu para a Secret 1]
      - BUCKET_NAME: [o nome do seu Bucket S3 que criou para o armazenamento dos segmentos de vídeo]
      - CF_KEY_PAIR_ID: [o ID da Public Key que você criou no CloudFront]
      - COOKIE_DOMAIN: [o nome do seu domínio com um ponto inicial, por exemplo: .example.com]
      - EC2_INSTANCE_ID: [o ID da sua instância do Owncast]
      - EC2_INSTANCE_PROXY_ID: [o ID da sua instância de Proxy]
      - EXPIRES_IN: [tempo em segundos que você deseja que o Cookie expire, 3600 significa 1 hora por exemplo]
      - FOLDER_PREFIX: hls/0/
      - ORIGIN_DOMAIN: [o nome do seu domínio com http ou https (depende se você criou um certificado digital), por exemplo: https://example.com]
      - REGION: [a region em que seu Bucket S3 foi criado]
      - SECRETS_NAME: [o nome que você deu para a Secret 2]
    - Ao final clique no botão Save

- Agora vá na guia Code
  - Você verá como se fosse um editor de código, lá haverá uma aba chamada lambda_function.py
    - Em [Code -> AWS_Lambda_Function](Code/AWS_Lambda_Function) você encontrará o código-fonte da função Lambda dentro da pasta src (arquivo chamado lambda_function.py), um arquivo buildspec.yml que poderá ser utilizado em um fluxo de Build com o CodePipeline e um arquivo lambda_package.zip, pronto para upload no console da AWS
    - No console da AWS, ainda na guia Code, clique no botão Upload from e depois clique na opção .zip file
    - Clique no botão Upload e escolha o arquivo lambda_package.zip e depois clique no botão Save
    - O arquivo lambda_function.py será atualizado e várias pastas e arquivos aparecerão no Explorer do editor de código da função Lambda no console da AWS
    - Geralmente o deploy da função Lambda é feito automaticamente
  - Para testar aqui é um pouco trabalhoso mas é possível se você fizer com cuidado:
    - No código-fonte do editor, vá na definição da função chamada validate_authorization
    - Antes do try, coloque a instrução:
      ```
      return None
      ```
    - Depois clique no botão Deploy
    - #### Atenção: depois que terminar o teste, lembre de remover este código
    - Agora vá na guia Test
    - No campo de texto de Event JSON, cole o seguinte conteúdo:
      ```
      {
        "requestContext": {
          "http": {
            "method": "GET"
          }
        },
        "rawPath": "/instance"
      }
      ```
    - Depois clique no botão Test
    - Se tudo deu certo, você verá a mensagem Executing function: succeeded com um fundo em cor verde, além disso se clicar em Details você verá o resultado da chamada
    - De certa forma está tudo funcionando, você poderia verificar o código-fonte para testar os demais métodos e rotas disponíveis se preferir, como por exemplo o /list-videos que muda apenas a rota, o resto do JSON é igual
    - #### Vamos desfazer a alteração que fizemos para o teste
    - No código-fonte do editor, vá na definição da função chamada validate_authorization
    - Antes do try, remova a instrução:
      ```
      return None
      ```
    - Depois clique no botão Deploy

---
[⬅️ Anterior: Configuração do Cognito](10-Cognito.md) | [🏠 Índice](../README.md) | [Próximo: Configuração do API Gateway ➡️](12-API-Gateway.md)