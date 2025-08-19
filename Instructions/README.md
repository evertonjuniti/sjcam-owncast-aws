# Instruções de instalação e configuração | Installation and configuration instructions
## Ordem de configuração dos recursos | Resource configuration order
> [pt-br] Para facilitar o passo-a-passo, haverá uma certa ordem de configuração dos recursos no ambiente da AWS, talvez certas configurações não façam muito sentido num primeiro momento, mas tentarei explicar de forma mais detalhada possível por questões didáticas e para melhor aproveitamento das informações aqui contidas. Fica avisado que a referência das informações é a versão do Console da AWS do terceiro trimestre de 2025, a depender da época que você estiver visualizando este guia pode ser que algumas diferenças surjam

>[en-us] To make the step-by-step process easier, there will be a specific order for configuring resources in the AWS environment. Some configurations may not make much sense at first, but I'll try to explain them in as much detail as possible for educational purposes and to better understand the information contained herein. Please note that the information references the AWS Console version from Q3 2025; depending on when you're viewing this guide, some differences may arise.

<a name="summary"></a>

### Resumo dos passos de configuração | Summary of configuration steps

- [Configuração de rede | Network configuration](#network-configuration)
- [Criação do Bucket S3 | Creating S3 an Bucket](#bucket-creation)
- [Criação das Secrets | Creation of Secrets](#secrets-creation)
- [Criação das instâncias EC2 | Creating EC2 instances](#instance-creation)

<a name="network-configuration"></a>

#### Configuração de rede | Network configuration
![Owncast-Network.drawio.svg](/Images/Owncast-Network.drawio.svg)

>[pt-br]
- Escolhi a região sa-east-1 para minha estrutura, você pode escolher o que preferir
- Estou usando VPC default da minha conta
  - VPC CIDR Block: 172.31.0.0/16
- Crie 2 subnets, uma que representa a subnet pública e outra a subnet privada
  - Public Subnet CIDR Block: 172.31.101.0/28 (somente 8 IPs)
  - Private Subnet CIDR Block: 172.31.100.0/28 (somente 8 IPs)
  - Somente 8 IPs é proposital, para evitar a criação de muitas instâncias EC2
- Crie 1 Endpoint, necessário para integração com o bucket S3 sem sair da VPC
  - No menu Endpoints, criei um do tipo "AWS Services", serviço "com.amazonaws.sa-east-1.s3" (dada a minha region) do tipo "Gateway" atrelado à minha VPC default
- Crie 1 Route Table para a subnet pública
  - Rotas:
    - Destination: 0.0.0.0./0 | Target: [Internet Gateway]
    - Destination: 172.31.0.0/16 | Target: local
  - Observação: É necessário haver um Internet Gateway atrelado à sua VPC
  - Faça a associação desta Route Table à Subnet Pública criada
- Crie 1 Route Table para a subnet privada
  - Rotas:
    - Destination: [Alias do S3] | Target: [VPC Endpoint S3]
    - Destination: 172.31.0.0/16 | Target: local
  - Observação: o Alias do S3 pode ser obtido no menu "Managed prefix lists"
  - Faça a associação desta Route Table à Subnet Pública criada
- Crie um NACL (Network Access Control List) para a subnet pública
  - Regras de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
    - HTTPS (porta 443), Source: 0.0.0.0/0
    - Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Custom TCP (range de portas 1024-65535), Source: 172.31.100.0/28
  - Regras de saída
    - HTTP* (porta 8080), Destination: 172.31.100.0/28
    - Custom TCP (porta 1935), Destination: 172.31.100.0/28
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - HTTPS (porta 443), Destination: 0.0.0.0/0
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Custom TCP (range e portas 1024-65535), Destination: 0.0.0.0/0
  - Associe este NACL à Subnet Pública criada
- Crie um NACL (Network Access Control List) para a subnet privada
  - Regras de entrada
    - Custom TCP (porta 1935), Source: 172.31.101.0/28
    - HTTP* (porta 8080), Source: 172.31.101.0/28
    - Custom TCP (range de portas 1024-65535), Source: 0.0.0.0/0
  - Regras de saída
    - Custom TCP (range de portas 1024-65535), Destination: 172.31.101.0/28
    - Custom TCP (range de portas 1024-65535), Destination: 0.0.0.0/0
    - HTTPS (porta 443), Destination: 0.0.0.0/0
  - Faça a associação desta Route Table à Subnet Privada criada
- Crie um Security Group (será usado na instância de Proxy)
  - Regras de entrada
    - HTTPS (porta 443), Source: 0.0.0.0/0
    - Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Custom TCP (range de portas 1024-65535), Source: 172.31.100.0/28
  - Regras de saída
    - Custom TCP (porta 1935), Destination: 172.31.100.0/28
    - Custom TCP (porta 8080), Destination: 172.31.100.0/28
- Crie um Security Group (será usado na instância do Owncast)
  - Regras de entrada
    - Custom TCP (porta 1935), Source: 172.31.101.0/28
    - Custom TCP (range de portas 1024-65535), Source: [Alias do S3]
    - Custom TCP (porta 8080), Source: 172.31.101.0/28
  - Regras de saída
    - Custom TCP (range de portas 1024-65535), Destination: 172.31.101.0/28
    - HTTPS (porta 443), Destination: [Alias do S3]
- Crie um Security Group (será usado para manutenção das instâncias)
  - Regras de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
  - Regras de saída
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - HTTPS (porta 443), Destination: 0.0.0.0/0

##### Observação importante: para fazer a manutenção e instalação de software na instância EC2 na Subnet Privada serão necessários passos adicionais, cuja recomendação é fazer somente em momento de manutenção, depois desfaça os itens abaixo descritos
- Inclua na Route Table associado à Subnet Privada:
  - Uma rota Destination: 0.0.0.0/0, Target: Internet Gateway
- Inclua na NACL associada à Subnet Privada:
  - Regra de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
  - Regra de saída
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
- Associe à instância EC2 da Subnet Privada:
  - O Security Group de manutenção de instâncias
  - Um IP público do tipo Elastic IP

Esses passos acima farão com que seja possível a conexão com a internet para fazer a atualização de segurança da instância e eventuais instalações.

Depois de fazer as instalações, desfaça todos esses itens acima citados para manter uma maior segurança do acesso à instância na Subnet Privada.

>[en-us]
- I chose the sa-east-1 region for my structure, you can choose whatever you prefer
- I'm using my account's default VPC
  - VPC CIDR Block: 172.31.0.0/16
- Create 2 subnets, one representing the public subnet and the other the private subnet
  - Public Subnet CIDR Block: 172.31.101.0/28 (only 8 IPs)
  - Private Subnet CIDR Block: 172.31.100.0/28 (only 8 IPs)
  - Only 8 IPs is intentional, to avoid creating too many EC2 instances
- Create 1 Endpoint, necessary for integration with the S3 bucket without leaving the VPC
  - In the Endpoints menu, I created one of the "AWS Services" type, service "com.amazonaws.sa-east-1.s3" (given my region) of the "Gateway" type linked to my default VPC
- Create a route table for the public subnet
  - Routes:
    - Destination: 0.0.0.0./0 | Target: [Internet Gateway]
    - Destination: 172.31.0.0/16 | Target: local
  - Note: An Internet Gateway must be attached to your VPC
  - Associate this route table with the public subnet you created
- Create a route table for the private subnet
  - Routes:
    - Destination: [S3 Alias] | Target: [S3 VPC Endpoint]
    - Destination: 172.31.0.0/16 | Target: local
  - Note: The S3 Alias can be found in the "Managed prefix lists" menu
  - Associate this route table with the private subnet you created
- Create a NACL (Network Access Control List) for the public subnet
  - Inbound Rules
    - SSH (port 22), Source: 0.0.0.0/0
    - HTTPS (port 443), Source: 0.0.0.0/0
    - Custom TCP (port 1935), Source: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Source: 172.31.100.0/28
  - Outbound Rules
    - HTTP* (port 8080), Destination: 172.31.100.0/28
    - Custom TCP (port 1935), Destination: 172.31.100.0/28
    - HTTP (port 80), Destination: 0.0.0.0/0
    - HTTPS (port 443), Destination: 0.0.0.0/0
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Custom TCP (range and ports 1024-65535), Destination: 0.0.0.0/0
  - Associate this NACL with the created Public Subnet
- Create a NACL (Network Access Control List) for the private subnet
  - Inbound Rules
    - Custom TCP (port 1935), Source: 172.31.101.0/28
    - HTTP* (port 8080), Source: 172.31.101.0/28
    - Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
  - Outbound Rules
    - Custom TCP (port range 1024-65535), Destination: 172.31.101.0/28
    - Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
    - HTTPS (port 443), Destination: 0.0.0.0/0
  - Associate this Route Table with the created Private Subnet
- Create a Security Group (will be used on the Proxy instance)
  - Inbound Rules
    - HTTPS (port 443), Source: 0.0.0.0/0
    - Custom TCP (port 1935), Source: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Source: 172.31.100.0/28
  - Outbound Rules
    - Custom TCP (port 1935), Destination: 172.31.100.0/28
    - Custom TCP (port 8080), Destination: 172.31.100.0/28
- Create a Security Group (will be used on the Owncast instance)
  - Inbound Rules
    - Custom TCP (port 1935), Source: 172.31.101.0/28
    - Custom TCP (port range 1024-65535), Source: [S3 Alias]
    - Custom TCP (port 8080), Source: 172.31.101.0/28
  - Outbound Rules
    - Custom TCP (port range 1024-65535), Destination: 172.31.101.0/28
    - HTTPS (port 443), Destination: [S3 Alias]
- Create a Security Group (will be used for instance maintenance)
  - Inbound Rules
    - SSH (port 22), Source: 0.0.0.0/0
  - Outbound Rules
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - HTTP (port 80), Destination: 0.0.0.0/0
    - HTTPS (port 443), Destination: 0.0.0.0/0

##### Important note: to perform maintenance and software installation on the EC2 instance in the Private Subnet, additional steps will be required. We recommend that you only do these during maintenance, then undo the items described below
- Include the following in the Route Table associated with the Private Subnet:
  - A route Destination: 0.0.0.0/0, Target: Internet Gateway
- Include the following in the NACL associated with the Private Subnet:
  - Inbound Rule
    - SSH (port 22), Source: 0.0.0.0/0
  - Outbound Rule
    - HTTP (port 80), Destination: 0.0.0.0/0
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
- Associate it with the EC2 instance in the Private Subnet:
  - The instance maintenance security group
  - An Elastic IP public IP

These steps above will enable an internet connection for instance security updates and any installations.

After completing the installations, undo all of the above items to maintain greater security when accessing the instance in the Private Subnet.

[Retornar ao resumo | Return to summary](#summary)

<a name="bucket-creation"></a>

#### Criação do Bucket S3 | Creating an S3 Bucket
![Owncast-Bucket.drawio.svg](/Images/Owncast-Bucket.drawio.svg)

>[pt-br]

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
      - ##### Atenção: Altere o [YOUR_DOMAIN] pelo seu domínio caso você tenha um domínio configurado, se quiser abrir a página localmente então substitua o valor de AllowedOrigins para http://localhost

>[en-us]

- [Optional] Create an S3 bucket in the same region as your network structure (where you have your VPC and subnets) to serve your website (if you have one). This can be used for the HTML page of this repository to access recorded videos
  - Bucket name: Must be a globally unique name, one that reflects the hosting of your static website.
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access
  - Bucket versioning: Disabled
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable
  - Other settings can be left at default
  - After creating the bucket, go to the Properties tab for that bucket
    - Edit the configuration to enable the S3 static website hosting option
      - Hosting type: Host a static website
      - Index document: index.html

- Create an S3 Bucket in the same Region as your Networking structure (where you have your VPC and Subnets) to store the video segments that will be recorded.
  - Bucket name: Must be a globally unique name, one that is meaningful for storing the video segments.
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access.
  - Bucket versioning: Disabled.
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable.
  - Other settings can be left at default.
  - After creating the bucket, go to the Permissions tab for that bucket.
    - Bucket policy: Will be configured later.
    - Cross-origin resource sharing (CORS): Use the template in [Code -> AWS_S3_Bucket -> CORS_policy.txt](Code/AWS_S3_Bucket/CORS_policy.txt)
      - ##### Attention: Change [YOUR_DOMAIN] to your domain if you have one. a configured domain, if you want to open the page locally then replace the value of AllowedOrigins to http://localhost

[Retornar ao resumo | Return to summary](#summary)

<a name="secrets-creation"></a>

#### Criação das Secrets | Creation of Secrets
![Owncast-SecretsManager.drawio.svg](/Images/Owncast-SecretsManager.drawio.svg)

>[pt-br]

Há um pré-requisito para uma das secrets, que envolve a geração do par de chaves privada e pública do tipo RSA.

Em [Code -> Keygen](Code/Keygen) há um código-fonte feito em linguagem GO para geração deste par de chaves, convenientemente eu deixei o go_keygen.exe já gerado (feito o build à partir do código-fonte), você só precisa executar e o par será gerado na pasta em que for chamado o executável. Você não precisa confiar no executável, se preferir você mesmo pode fazer o build do código-fonte, você só vai precisar da versão mais recente do GO que pode ser obtido [nesta página](https://go.dev/doc/install).

Você pode estar se perguntando porque gerar o par de chaves através de um código-fonte ao invés de usar um comando bash via openssl, a resposta é simples: na minha máquina eu não consegui gerar uma chave privada cujo cabeçalho ficasse "BEGIN RSA PRIVATE KEY", que acreditem é necessário ter esse cabeçalho para a solução deste repositório funcionar.

De qualquer maneira, vou deixar os comandoss para fazer via openssl, caso em sua máquina dê o resultado final (precisa ter o cabeçalho BEGIN RSA PRIVATE KEY, qualquer coisa diferente disso não funcionará).

```
bash
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

- Crie duas secrets na Secrets Manager na mesma Region da sua estrutura de Redes (onde você tem seu VPC e suas Subnets)
  - Secret 1 - para armazenar os e-mails que terão permissão de acesso à página dos vídeos
    - Secret type: Other type of secret
    - Key/value pairs
      - Key: 0, Value: seu endereço de e-mail
      - [opcional] Key: 1, Value: outro endereço de e-mail que você deseje. Vá adicionando mais caso deseje
    - Encryption key: aws/secretsmanager
    - Na próxima página, em Secret name dê um nome para a secret, no exemplo aqui se chama AllowedEmails
    - Ná próxima página pode manter os valores default, já que não precisa rotacionar essas secrets
  - Secret 2 - para armazenar a chave privada que será utilizada para gerar os cookies dos vídeos
    - Secret type: Other type of secret
    - Plaintext: cole a chave RSA privada gerada integralmente aqui
    - Encryption key: aws/secretsmanager
    - Na próxima página, em Secret name dê um nome para a secret, no exemplo aqui se chama CloudFrontPrivateKey (sim, o nome é ruim, mas é o que eu havia criado na época)
    - Ná próxima página pode manter os valores default, já que não precisa rotacionar essas secrets

>[en-us]

There is a prerequisite for one of the secrets, which involves generating an RSA private and public key pair.

In [Code -> Keygen](Code/Keygen), there is source code written in GO for generating this key pair. Conveniently, I've already generated go_keygen.exe (built from the source code). You just need to run it, and the key pair will be generated in the folder where the executable is called. You don't need to trust the executable; if you prefer, you can build it yourself from the source code. You'll just need the latest version of GO, which can be obtained [from this page](https://go.dev/doc/install).

You may be wondering why I should generate the key pair from source code instead of using a bash command via OpenSSL. The answer is simple: on my machine, I couldn't generate a private key with the header "BEGIN RSA PRIVATE KEY," which, believe me, is required for the solution in this repository to work.

Anyway, I'll leave the commands to be done via openssl, in case your machine gives the final result (it needs to have the BEGIN RSA PRIVATE KEY header, anything different from that won't work).

```
bash
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

- Create two secrets in Secrets Manager in the same Region as your Network structure (where you have your VPC and Subnets)
  - Secret 1 - to store the emails that will be allowed to access the video page
    - Secret type: Other type of secret
    - Key/value pairs
      - Key: 0, Value: Your email address
      - [optional] Key: 1, Value: Another email address of your choice. Add more if desired
    - Encryption key: aws/secretsmanager
    - On the next page, under Secret name, give the secret a name. In the example here, it's called AllowedEmails
    - On the next page, you can keep the default values, since you don't need to rotate these secrets
  - Secret 2 - to store the private key that will be used to generate the video cookies
    - Secret type: Other type of secret
    - Plaintext: Paste the fully generated private RSA key here
    - Encryption key: aws/secretsmanager
    - On the next page, under Secret name, give the secret a name. In the example here, it's called CloudFrontPrivateKey (yes, the name is bad, but it's what I created at the time)
    - On the next page, you can keep the default values, since you don't need to rotate these secrets

[Retornar ao resumo | Return to summary](#summary)

<a name="instance-creation"></a>

#### Criação das instâncias EC2 | Creating EC2 instances
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

>[pt-br]

- Instância EC2 para o servidor de Proxy (utilizando HAProxy)
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.micro
  - Key pair: pode selecionar alguma que já tenha, se não tiver crie um novo par
  - Network settings:
    - VPC: VPC default (seguindo o exemplo deste guia)
    - Subnet: a Subnet Pública que você criou
    - Security Group: escolha o Security Group que você criou para uso do Proxy
  - Demais configurações pode manter o default
  - Na guia de Elastic IP, crie um e associe a esta instância
- Instância EC2 para o servidor do Owncast
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.small
  - Key pair: pode selecionar alguma que já tenha (por exemplo a que atribuiu à instância EC2 de Proxy), ou crie um novo par
  - Network settings:
    - VPC: VPC default (seguindo o exemplo deste guia)
    - Subnet: a Subnet Privada que você criou
    - Security Group: escolha o Security Group que você criou para uso do Owncast
  - Demais configurações pode manter o default

##### Observações importantes: Tome nota do Instance ID de ambas as instâncias EC2 e do endereço IP elástico

>[en-us]

- EC2 instance for the Proxy server (using HAProxy)
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.micro
  - Key pair: You can select one you already have; if you don't have one, create a new pair
  - Network settings:
    - VPC: Default VPC (following the example in this guide)
    - Subnet: The Public Subnet you created
    - Security Group: Choose the Security Group you created for Proxy use
  - Other settings can remain at the default
  - In the Elastic IP tab, create one and associate it with this instance
- EC2 instance for the Owncast server
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.small
  - Key pair: You can select one you already have (for example, the one you assigned to the Proxy EC2 instance), or create a new pair
  - Network settings:
    - VPC: Default VPC (following the example in this guide)
    - Subnet: The Private Subnet you created
    - Security Group: Choose the Security Group you created. You created it for Owncast use
  - You can keep the other settings at the default

##### Important Notes: Take note of the Instance ID of both EC2 instances and the Elastic IP address

[Retornar ao resumo | Return to summary](#summary)