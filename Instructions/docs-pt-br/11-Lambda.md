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
    - Em [Code -> AWS_Lambda_Function -> Playlist](Code/AWS_Lambda_Function/Playlist) você encontrará o código-fonte da função Lambda dentro da pasta src (arquivo chamado lambda_function.py), um arquivo buildspec.yml que poderá ser utilizado em um fluxo de Build com o CodePipeline e um arquivo lambda_package.zip, pronto para upload no console da AWS
    - No console da AWS, ainda na guia Code, clique no botão Upload from e depois clique na opção .zip file
    - Clique no botão Upload e escolha o arquivo lambda_package.zip e depois clique no botão Save
    - O arquivo lambda_function.py será atualizado e várias pastas e arquivos aparecerão no Explorer do editor de código da função Lambda no console da AWS
    - Geralmente o deploy da função Lambda é feito automaticamente
  - Para testar, siga as seguintes instruções:
    - Vá na guia Test
    - No campo de texto de Event JSON, cole o seguinte conteúdo:
      ```
      {
        "requestContext": {
          "authorizer": {
            "claims": {
              "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
            }
          },
          "http": {
            "method": "GET"
          }
        },
        "rawPath": "/instance"
      }
      ```
    - Depois clique no botão Test
    - Se tudo deu certo, você verá a mensagem Executing function: succeeded com um fundo em cor verde, além disso se clicar em Details você verá o resultado da chamada, o resultado deveria ser algo assim:
      ```
      {
        "statusCode": 200,
        "headers": {
          "Access-Control-Allow-Origin": "https://example.com",
          "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
          "Access-Control-Allow-Credentials": "true",
          "Content-Type": "application/json"
        },
        "body": "{\"status\": \"stopped\"}"
      }
      ```
      - O atributo "status" com o valor "stopped" no body do response indica que a chamada conseguiu verificar o status das instâncias EC2
    - Vamos testar os demais endpoints:
      - PUT - /instance/turnon
        - Requisição:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "PUT"
            }
          },
          "rawPath": "/instance/turnon"
        }
        ```
        - Resposta esperada:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "{\"action\": \"starting\"}"
        }
        ```
        - Você pode verificar suas instâncias no serviço EC2, ambas as instâncias do Owncast e Proxy deverão estar ligadas agora
      - PUT - /instance/turnoff
        - Requisição:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "PUT"
            }
          },
          "rawPath": "/instance/turnoff"
        }
        ```
        - Resposta esperada:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "{\"action\": \"stopping\"}"
        }
        ```
        - Você pode verificar suas instâncias no serviço EC2, ambas as instâncias do Owncast e Proxy deverão estar parando agora
      - GET - /auth-cookies
        - Requisição:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "auth-cookies"
        }
        ```
        - Resposta esperada:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "multiValueHeaders": {
            "Set-Cookie": [
              "CloudFront-Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9ldmVydG9ub2d1cmEuY29tL2hscy8wLyoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NTY3Mjc2NDd9fX1dfQ__;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None",
              "CloudFront-Signature=Sj~HEy7Ljv5mf3J5x5n85mDXBFtC2cQKKuJj1n3jgbMcXbeNNaB~YUubHsSvvm9frCQCCycQxGkRJJanu0Ym3dV2VQyca7tC46yTElkfh9lhKQMZjkEgXF-ifTusunTZlEPl9DHW2C4x7MEB5QTd6CKjY~jgMH4H3yeBxi-VQcnIeuGv3qNDis-IOID0xhjeXhH7CSe5NP3I2XBI0Fq2-GvLbMfsidKJjkNp7-OyhTO1JsvU2RRGRGo5EUs31EuyYH30nC-CSsDZhWYz8MLQdoYtWXdtyh-x78Fex4eDd~V9-igWLMyBDHXyBSNYj0lESDRVSbzfotTky~OoIb-qyA__;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None",
              "CloudFront-Key-Pair-Id=K3KYD9LB8GV4A3;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None"
            ]
          },
          "body": ""
        }
        ```
        - Nesta rota é esperado que você receba os Cookies, que serão utilizados para acesso aos segmentos de vídeo via CloudFront, que serão utilizados pelo player de vídeo
      - GET - /list-videos
        - Requisição:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "/list-videos"
        }
        ```
        - Resposta esperada:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "[{\"videoId\": \"offline\", \"dateTime\": \"2025-09-01 10:37:52 - offline\"}, {\"videoId\": \"KOOuOXuNg\", \"dateTime\": \"2025-08-28 14:51:31 - KOOuOXuNg\"}]"
        }
        ```
        - Nesta rota é esperado que você receba uma lista de vídeos se você gravou alguns no momento de configuração da instância do Owncast (em que configuramos para uso do SJCAM SJ11)
      - GET - /playlist/{video-id}
        - Requisição:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "/playlist/offline.m3u8",
          "pathParameters": {
            "video_id": "offline.m3u8"
          }
        }
        ```
        - Resposta esperada:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/vnd.apple.mpegurl"
          },
          "body": "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:6.000,\nhttps://example.com/hls/0/stream-offline-0.ts\n#EXT-X-ENDLIST"
        }
        ```
        - Nesta rota é esperado que você receba uma lista dos segmentos de vídeo para o Id de vídeo que você usou na chamada (no pathParameters)
    - De certa forma está tudo funcionando, estes testes validam que a função Lambda consegue fazer as chamadas esperadas e que a role está com as policies corretas para acesso às instâncias EC2 e ao Bucket

---
[⬅️ Anterior: Configuração do Cognito](10-Cognito.md) | [🏠 Índice](../README.md) | [Próximo: Configuração do API Gateway ➡️](12-API-Gateway.md)