# Criação do Bucket S3
![Owncast-Bucket.drawio.svg](/Images/Owncast-Bucket.drawio.svg)

- [Opcional] Crie um Bucket S3 na mesma Region da sua estrutura de Redes (onde você tem seu VPC e suas Subnets) para servir seu site (se tiver um), isso poderá ser utilizado para a página HTML deste repositório para acesso aos vídeos gravados
  - Bucket name: Precisa ser um nome único globalmente, algum que tenha o significado de hospedagem do seu website estático
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access
  - Bucket versioning: Disable
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable
  - Demais configurações pode deixar o default
  - Após criar o bucket, vá para a aba Properties desse bucket
    - Edite a configuração para habilitar a opção S3 static website hosting
      - Hosting type: Host a static website
      - Index document: index.html

- Crie um Bucket S3 na mesma Region da sua estrutura de Redes (onde você tem seu VPC e suas Subnets) para armazenar os segmentos de vídeo que serão gravados
  - Bucket name: Precisa ser um nome único globalmente, algum que tenha o significado de armazenamento dos segmentos de vídeo
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access
  - Bucket versioning: Disable
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable
  - Demais configurações pode deixar o default
  - Após criar o bucket, vá para a aba Permissions desse bucket
    - Bucket policy: será configurado mais pra frente
    - Cross-origin resource sharing (CORS): use o template em [Code -> AWS_S3_Bucket -> CORS_policy.txt](Code/AWS_S3_Bucket/CORS_policy.txt)
      - #### Atenção: Altere o [YOUR_DOMAIN] pelo seu domínio caso você tenha um domínio configurado, se quiser abrir a página localmente então substitua o valor de AllowedOrigins para http://localhost

---
[⬅️ Anterior: Configuração de rede](01-Network.md) | [🏠 Índice](../README.md) | [Próximo: Criação das instâncias EC2 ➡️](03-EC2-instance-creation.md)