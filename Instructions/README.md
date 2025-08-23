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
- [Configuração de policies, roles e usuário do IAM | Configuring IAM policies, roles, and users](iam-configuration)
- [Configuração do Cognito | Cognito configuration](cognito-configuration)
- [Configuração do Route 53 | Route 53 configuration](route53-configuration)
- [Criação de certificado digital | Digital certificate creation](certificate-manager-creation)
- [Configuração das instâncias EC2 | Configuring EC2 instances](#instance-configuration)

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
    - Rule number 100, HTTPS (porta 443), Source: 0.0.0.0/0
    - Rule number 101, Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Rule number 102, Custom TCP (range de portas 1024-65535), Source: 172.31.100.0/28
  - Regras de saída
    - Rule number 100, HTTP* (porta 8080), Destination: 172.31.100.0/28
    - Rule number 101, Custom TCP (porta 1935), Destination: 172.31.100.0/28
    - Rule number 102, Custom TCP (range de portas 1024-65535), Destination: 0.0.0.0/0
  - Associe este NACL à Subnet Pública criada
- Crie um NACL (Network Access Control List) para a subnet privada
  - Regras de entrada
    - Rule number 100, Custom TCP (porta 1935), Source: 172.31.101.0/28
    - Rule number 101, HTTP* (porta 8080), Source: 172.31.101.0/28
    - Rule number 102, Custom TCP (range de portas 1024-65535), Source: 0.0.0.0/0
  - Regras de saída
    - Rule number 100, Custom TCP (range de portas 1024-65535), Destination: 172.31.101.0/28
    - Rule number 101, HTTPS (porta 443), Destination: 0.0.0.0/0
  - Faça a associação desta Route Table à Subnet Privada criada
- Crie um Security Group (será usado na instância de Proxy)
  - Regras de entrada
    - HTTPS (porta 443), Source: 0.0.0.0/0
    - Custom TCP (porta 1935), Source: 0.0.0.0/0
  - Regras de saída
    - Custom TCP (porta 1935), Destination: 172.31.100.0/28
    - Custom TCP (porta 8080), Destination: 172.31.100.0/28
- Crie um Security Group (será usado na instância do Owncast)
  - Regras de entrada
    - Custom TCP (porta 1935), Source: 172.31.101.0/28
    - Custom TCP (porta 8080), Source: 172.31.101.0/28
  - Regras de saída
    - HTTPS (porta 443), Destination: [Alias do S3]
- Crie um Security Group (será usado para manutenção das instâncias)
  - Regras de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
  - Regras de saída
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - HTTPS (porta 443), Destination: 0.0.0.0/0

##### Observação importante: para fazer a manutenção e instalação de software na instância EC2 na Subnet Pública e Privada serão necessários passos adicionais, cuja recomendação é fazer somente em momento de manutenção, depois desfaça os itens abaixo descritos
- Inclua na Route Table associado à Subnet Privada:
  - Uma rota Destination: 0.0.0.0/0, Target: Internet Gateway
- Inclua na NACL associada à Subnet Pública e Privada:
  - Regra de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
    - Custom TCP (range de porta 1024-65535), Source: 0.0.0.0/0
  - Regra de saída
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Custom TCP (range de porta 1024-65535), Destination: 0.0.0.0/0
- Inclua na NACL associada à Subnet Pública:
  - Regra de saída
    - HTTPS (porta 443), Destination: 0.0.0.0/0
- Associe à instância EC2 da Subnet Pública e Privada:
  - O Security Group de manutenção de instâncias
  - Um IP público do tipo Elastic IP (aqui é uma instância por vez)

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
    - Rule number 100, HTTPS (port 443), Source: 0.0.0.0/0
    - Rule number 101, Custom TCP (port 1935), Source: 0.0.0.0/0
    - Rule number 102, Custom TCP (port range 1024-65535), Source: 172.31.100.0/28
  - Outbound Rules
    - Rule number 100, HTTP* (port 8080), Destination: 172.31.100.0/28
    - Rule number 101, Custom TCP (port 1935), Destination: 172.31.100.0/28
    - Rule number 102, Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
  - Associate this NACL with the created Public Subnet
- Create a NACL (Network Access Control List) for the private subnet
  - Inbound Rules
    - Rule number 100, Custom TCP (port 1935), Source: 172.31.101.0/28
    - Rule number 101, HTTP* (port 8080), Source: 172.31.101.0/28
    - Rule number 102, Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
  - Outbound Rules
    - Rule number 100, Custom TCP (port range 1024-65535), Destination: 172.31.101.0/28
    - Rule number 101, HTTPS (port 443), Destination: 0.0.0.0/0
  - Associate this Route Table with the created Private Subnet
- Create a Security Group (will be used on the Proxy instance)
  - Inbound Rules
    - HTTPS (port 443), Source: 0.0.0.0/0
    - Custom TCP (port 1935), Source: 0.0.0.0/0
  - Outbound Rules
    - Custom TCP (port 1935), Destination: 172.31.100.0/28
    - Custom TCP (port 8080), Destination: 172.31.100.0/28
- Create a Security Group (will be used on the Owncast instance)
  - Inbound Rules
    - Custom TCP (port 1935), Source: 172.31.101.0/28
    - Custom TCP (port 8080), Source: 172.31.101.0/28
  - Outbound Rules
    - HTTPS (port 443), Destination: [S3 Alias]
- Create a Security Group (will be used for instance maintenance)
  - Inbound Rules
    - SSH (port 22), Source: 0.0.0.0/0
  - Outbound Rules
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - HTTP (port 80), Destination: 0.0.0.0/0
    - HTTPS (port 443), Destination: 0.0.0.0/0

##### Important note: to perform maintenance and software installation on the EC2 instance in the Public and Private Subnet, additional steps will be required. We recommend that you only do these during maintenance, then undo the items described below
- Include the following in the Route Table associated with the Private Subnet:
  - A route Destination: 0.0.0.0/0, Target: Internet Gateway
- Include the following in the NACL associated with the Public and Private Subnet:
  - Inbound Rule
    - SSH (port 22), Source: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
  - Outbound Rule
    - HTTP (port 80), Destination: 0.0.0.0/0
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
- Include the following in the NACL associated with the Public Subnet:
  - Outbound Rule
    - HTTPS (port 443), Destination: 0.0.0.0/0
- Associate it with the EC2 instance in the Public and Private Subnet:
  - The instance maintenance security group
  - An Elastic IP public IP (here is one instance at a time)

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

##### Observações importantes: Tome nota do nome de ambas essas secrets que você acabou de criar

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

##### Important Notes: Take note of the name of both these secrets you just created

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
    - ##### se for criar um, guarde o arquivo .pem em um local na sua máquina, você vai precisar disso para acessar a instância depois
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
    - ##### se for criar um, guarde o arquivo .pem em um local na sua máquina, você vai precisar disso para acessar a instância depois
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
    - ##### if you are going to create one, save the .pem file somewhere on your machine, you will need it to access the instance later
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
    - ##### if you are going to create one, save the .pem file somewhere on your machine, you will need it to access the instance later
  - Network settings:
    - VPC: Default VPC (following the example in this guide)
    - Subnet: The Private Subnet you created
    - Security Group: Choose the Security Group you created. You created it for Owncast use
  - You can keep the other settings at the default

##### Important Notes: Take note of the Instance ID of both EC2 instances and the Elastic IP address

[Retornar ao resumo | Return to summary](#summary)

<a name="iam-configuration"></a>

#### Configuração de policies, roles e usuário do IAM | Configuring IAM policies, roles, and users
![Owncast-IAM.drawio.svg](/Images/Owncast-IAM.drawio.svg)

>[pt-br]

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
    - ##### Atenção: essa será a única oportunidade para anotar a Secret Key, não clique no botão Done antes de anotar essa informação

##### Observações importantes: Tome nota do nome das Policies, Roles e do User (Acces Key e Secret Key) criadas

>[en-us]

- In the Policies menu, create a new Policy, this will be the main policy for Owncast
  - Instead of selecting with the Visual editor, switch to the JSON editor.
  - Use the template file from this repository in [Code -> AWS_IAM -> Owncast_Policy.txt](Code/AWS_IAM/Owncast_Policy.txt)
    - Change the [OwncastSegmentsBucketName] tag to the name of the bucket you created for the video segment files.
    - Change the [YourRegion] tag to the same region as your VPC and Subnet.
    - Change the [YourAccount] tag to your AWS account ID (you can see this in the upper right corner of the AWS Console; use only numbers).
    - Change the [ProxyInstanceId] tag to the ID of the EC2 instance for the Public Subnet Proxy (remember I told you to write this down!)
    - Change the [OwncastInstanceId] tag to the ID of the EC2 instance for the Private Subnet Owncast (Remember, I told you to write this down!)
    - Change the name of the CloudFrontPrivateKey secret if you created it with a different name in Secrets Manager (remember, I told you to write this down!)
    - Change the name of the AllowedEmails secret if you created it with a different name in Secrets Manager (remember, I told you to write this down!)
    - On the next page, give your policy a name (in my case it was OwncastPolicy)

- In the Roles menu, create a new role. This will be the primary role for Owncast, linked to the Owncast Policy.
  - Trusted entity type: AWS Service
  - Use case: Lambda
  - Permission policies: select:
    - AWSLambdaBasicExecutionRole (AWS managed)
    - The name of the Owncast Policy. In this example, it's called OwncastPolicy (Customer managed)
    - Remember to check the boxes for both policies mentioned above
  - Role details:
    - Role name: Give the role a name (in my case, it was OwncastLambdaS3ReadAccessRole)
    - You can leave the other fields at their default values

- [Optional] Create a policy to generate a digital certificate via Let's Encrypt for the Proxy instance
  - This policy is for if you have a domain in Route 53 and want to validate the domain with a digital certificate when calling the Proxy through the domain
  - Instead of selecting with the Visual editor, switch to the JSON editor
  - Use the template file from this repository in [Code -> AWS_IAM -> Route53Certificate_Policy.txt](Code/AWS_IAM/Route53Certificate_Policy.txt)
    - Change the [YourHostedZoneId] tag to the ID of your Hosted Zone in Route 53
    - On the next page, give your policy a name (in my case, it was OwncastProxyRoute53CertificatePolicy)

- [Optional] Create a Role to generate a digital certificate via Let's Encrypt for the Proxy instance using the optional Policy
  - Trusted entity type: AWS Service
  - Use case: EC2 (in the list of options, keep the EC2 option)
  - Permission policies: select:
    - The name of the digital certificate policy. In this example, it's called OwncastProxyRoute53CertificatePolicy (Customer managed)
    - Remember to check the box for the policy mentioned above
  - Role details:
    - Role name: Give the role a name (in my case, it was called OwncastProxyRoute53CertificateRole)
    - You can leave the other fields at their default values

- In the Users menu, create a new user
  - User name: Give it a name (in my example, it was Owncast)
  - Provide user access to the AWS Management Console - optional: leave unchecked
  - After creating the user, click on the newly created user to view the details
  - In the Security Credentials tab, under Access keys, click the Create access key button
    - Use case: Third-party service (will be used within the Owncast application settings)
    - Confirmation (I understand the above recommendation and want to proceed to create an access key): leave checked
    - The rest is optional
    - Write down the Access key
    - In the Secret access key column, click Show and write down the Secret Key
    - You can optionally download the .csv file with the Access Key and Secret Key information. Save this file if you choose to download it
    - ##### Attention: This will be the only opportunity to write down the Secret Key. Do not click the Done button before writing down this information

##### Important notes: Take note of the name of the Policies created

[Retornar ao resumo | Return to summary](#summary)

<a name="cognito-configuration"></a>

#### Configuração do Cognito | Cognito configuration
![Owncast-Cognito.drawio.svg](/Images/Owncast-Cognito.drawio.svg)

>[pt-br]

- No Cognito na region que você escolheu (o mesmo da VPC e Subnets), vá ao menu User pools e crie um novo user pool
  - Application type: Single-page application (SPA)
  - Name your application: dê um nome para sua aplicação (no meu exemplo ficou Owncast SPA app)
  - Options for sign-in identifiers: Email e Username
  - Required attributes for sign-up: email (não haverá a opção de sign-up, mas esse campo é obrigatório o preenchimento)
  - Deixe os demais campos default e crie o user directory
  - Vá até o final da página e clique no botão Go to Overview
    - ##### Em User pool information, tome nota do User pool ID
  - Vá para o menu App clientes deste user pool
    - ##### Tome nota do valor da coluna Client ID
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
    - ##### Repita este processo de criação de usuários para todos os usuários que deseje incluir
  - Vá para o menu Sign-up
    - Ao final da página em Self-service sign-up, clique no botão Edit
    - Em self-registration, Enable self-registration: deixe desmarcado e salve as alterações

>[en-us]

- In Cognito, in the region you chose (the same as the VPC and Subnets), go to the User Pools menu and create a new user pool
  - Application type: Single-page application (SPA)
  - Name your application: Give your application a name (in my example, it was Owncast SPA app)
  - Options for sign-in identifiers: Email and Username
  - Required attributes for sign-up: Email (there won't be a sign-up option, but this field is required)
  - Leave the remaining fields default and create the user directory
  - Scroll to the bottom of the page and click the Go to Overview button
    - ##### Under User pool information, take note the User pool ID
  - Go to the App clients menu for this user pool
    - ##### Take note the value in the Client ID column
  - Go to the Users menu for this user pool
    - Click the Create user button
    - Alias attributes used to sign in: Leave the Email option checked
    - Invitation message: Don't send an invitation
    - User name: Choose a username
    - Email address: Include your email address
    - Mark email address as verified: Leave checked
    - Phone number - optional: Optional; you can leave it blank if you wish
    - Mark phone number as verified: Also optional
    - Temporary password: Set a password
    - Password: Choose a temporary password. You will need to log in a first time to change the password, but this will be displayed in the video access page.
    - ##### Repeat this user creation process for all users you wish to include
  - Go to the Sign-up menu
    - At the bottom of the page, under Self-service sign-up, click the Edit button.
    - Under Self-registration, Enable self-registration: Leave it unchecked and save the changes.

[Retornar ao resumo | Return to summary](#summary)

<a name="route53-configuration"></a>

#### Configuração do Route 53 | Route 53 configuration
![Owncast-Route_53.drawio.svg](/Images/Owncast-Route_53.drawio.svg)

>[pt-br]
   
- [Opcional] Registre um domínio, esse é um requisito opcional caso você queira acessar os recursos por um domínio seu
  - Vá no menu Registered domains no Route 53 e clique no botão Register domains
    - Check availability for a domain: especifique um nome de domínio desejado e clique no botão Search
      - Pode ser que o domínio exato não esteja disponível, mas na lista de Suggested available domains há opções de domínio possíveis para seleção
      - Observe que a depender do domínio o custo anual pode variar
      - Clique em Select na coluna Actions para o domínio selecionado e depois clique no botão Proceed to checkout
    - Observe que você pode optar pela renovação automática ou não
    - Você precisará informar dados cadastrais de registro de contato como pessoa responsável pelo domínio, você pode mudar os demais tipos de contato se quiser ou manter as opções padrão já selecionadas
    - Por fim em Terms and conditions, leia as condições e marque a caixa de seleção e depois clique no botão Submit para comprar o domínio

- [Opcional] Crie uma hosted zone, esse é um requisito opcional caso você queira usar seu domínio para registrar como você roteia tráfego para seu domínio aos serviços que criaremos com este manual
  - Vá no menu Hosted zones no Route 53 e clique no botão Create hosted zone
    - Domain name: indique o nome do domínio que você possui (pode ser o que você comprou caso tenha optado por registrar um domínio)
    - Type: Public hosted zone (para permitir chamadas/tráfego da internet)

>[en-us]

- [Optional] Register a domain. This is an optional requirement if you want to access resources through your own domain
  - Go to the Registered domains menu in Route 53 and click the Register domains button
    - Check availability for a domain: specify a desired domain name and click the Search button
      - The exact domain may not be available, but the Suggested available domains list contains possible domain options for selection
      - Note that the annual cost may vary depending on the domain
      - Click Select in the Actions column for the selected domain and then click the Proceed to checkout button
  - Note that you can choose automatic renewal or not
  - You will need to provide contact information as the person responsible for the domain. You can change the other contact types if you wish or keep the default options already selected
  - Finally, in the Terms and Conditions section, read the terms and conditions, select the checkbox, and then click the Submit button to purchase the domain

- [Optional] Create a hosted zone. This is an optional requirement if you want to use your domain to register how you route traffic for your domain to the services we'll create in this guide
  - Go to the Hosted Zones menu in Route 53 and click the Create Hosted Zone button
    - Domain Name: Enter the name of your domain (this can be the one you purchased if you chose to register a domain)
    - Type: Public hosted zone (to allow calls/internet traffic)

[Retornar ao resumo | Return to summary](#summary)

<a name="certificate-manager-creation"></a>

#### Criação de certificado digital | Digital certificate creation
![Owncast-Certificate_Manager.drawio.svg](/Images/Owncast-Certificate_Manager.drawio.svg)

>[pt-br]

- [Opcional] Caso queira usar o certificado digital em conjunto com o seu domínio de registro
  - ##### Atenção: aqui você precisa estar na region us-east-1 (N. Virginia) para uso com o CloudFront
  - Vá no meu List certificates no AWS Certificate Manager e clique no botão Request
  - Certificate type: Request a public certificate
  - Fully qualified domain name: Adicione o seu domínio e também um wildcard do seu domínio (isso vai te ajudar depois), vou indicar um exemplo:
    - evertonogura.com (esse é o meu domínio, aqui substitua pelo seu)
    - *.evertonogura.com (esse é o wildcard para sub-domínio, aqui substitua pelo seu)
    - ##### Observação: para adicionar mais de um domínio, após adicionar o primeiro domínio, clique no botão Add another name to this certificate para adionar demais domínios ou sub-domínios
  - Allow export: Disable export
    - ##### Cuidado: não clique em Enable export se você não vai exportar o certificado para usar fora da AWS, se você selecionar essa opção vai te gerar um custo de $ 164.00 USD
  - Validation method: DNS validation - recommended
  - Key algorithm: RSA 2048 (mas pode selecionar outro se quiser)
  - É necessário aguardar a AWS fazer a validação do nome de domínio para verificar se você é o dono, se você registrou o domínio no Route 53 e se você criou a Hosted zone, clique no botão Create records in Route 53 para que o AWS Certificate Manager adicione os registros de domínios e sub-domínios para você na sua Hosted zone e aí a validação ocorrerá com sucesso

>[en-us]

- [Optional] If you want to use the digital certificate in conjunction with your registered domain,
  - ##### Note: You must be in the us-east-1 (N. Virginia) region for use with CloudFront
  - Go to my List certificates in AWS Certificate Manager and click the Request button
  - Certificate type: Request a public certificate
  - Fully qualified domain name: Add your domain and a wildcard for your domain (this will help you later). Here's an example:
    - evertonogura.com (this is my domain, replace it with yours here)
    - *.evertonogura.com (this is the wildcard for a subdomain, replace it with yours here)
    - ##### Note: To add more than one domain, after adding the first domain, click the Add another name to this certificate button to add additional domains or subdomains
  - Allow export: Disable export
    - ##### Caution: Do not click Enable export if you will not export the certificate for use outside of AWS. Selecting this option will incur a cost of $164.00 USD
  - Validation method: DNS validation - recommended
  - Key algorithm: RSA 2048 (but you can select another if you wish)
  - You must wait for AWS to validate the domain name to verify that you are the owner. If you registered the domain with Route 53 and created the Hosted zone, click the Create records in Route 53 button so that AWS Certificate Manager adds the domain and subdomain records for you to your Hosted zone, and then the validation will be successful

[Retornar ao resumo | Return to summary](#summary)

<a name="instance-configuration"></a>

#### Connfiguração das instâncias EC2 | Configuring EC2 instances
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

Owncast_1.png:

![Owncast_1.png](/Images/Owncast_1.png)

Owncast_2.png:

![Owncast_2.png](/Images/Owncast_2.png)

Owncast_3.png:

![Owncast_3.png](/Images/Owncast_3.png)

Owncast_4.png:

![Owncast_4.png](/Images/Owncast_4.png)

Owncast_5.png:

![Owncast_5.png](/Images/Owncast_5.png)

Owncast_6.png:

![Owncast_6.png](/Images/Owncast_6.png)

Owncast_7.png:

![Owncast_7.png](/Images/Owncast_7.png)

Owncast_8.png:

![Owncast_8.png](/Images/Owncast_8.png)

Owncast_9.png:

![Owncast_9.png](/Images/Owncast_9.png)

Owncast_10.png:

![Owncast_10.png](/Images/Owncast_10.png)

Owncast_11.png:

![Owncast_11.png](/Images/Owncast_11.png)

Owncast_12.png:

![Owncast_12.png](/Images/Owncast_12.png)

Owncast_13.png:

![Owncast_13.png](/Images/Owncast_13.png)

Owncast_14.png:

![Owncast_14.png](/Images/Owncast_14.png)

Owncast_15.png:

![Owncast_15.png](/Images/Owncast_15.png)

Owncast_16.png:

![Owncast_16.png](/Images/Owncast_16.png)

Owncast_17.png:

![Owncast_17.png](/Images/Owncast_17.png)

Owncast_18.png:

![Owncast_18.png](/Images/Owncast_18.png)

Owncast_19.png:

![Owncast_19.png](/Images/Owncast_19.png)

Owncast_20.png:

![Owncast_20.png](/Images/Owncast_20.png)

Owncast_21.png:

![Owncast_21.png](/Images/Owncast_21.png)

Owncast_22.png:

![Owncast_22.png](/Images/Owncast_22.png)

Owncast_23.png:

![Owncast_23.png](/Images/Owncast_23.png)

Owncast_24.png:

![Owncast_24.png](/Images/Owncast_24.png)

Owncast_25.png:

![Owncast_25.png](/Images/Owncast_25.png)

Owncast_26.png:

![Owncast_26.png](/Images/Owncast_26.png)

Owncast_27.png:

![Owncast_27.png](/Images/Owncast_27.png)

>[pt-br]

Nesta etapa iremos configurar a instância EC2 referente ao Proxy para instalação e configuração do HAProxy e a instância EC2 referente ao Owncast para instalação e configuração do Owncast.

Vamos começar pela instância do Owncast na Subnet Privada, assim já conseguiremos fazer um primeiro teste com a SJCAM SJ11.

##### Atenção: faremos ajustes no Route Table, NACL, Security Group (todos via serviço VPC) apenas para possibilitar os testes, eu vou indicar o que fazer e como desfazer ao final

- [Desfazer depois] Vá em Route tables no VPC, selecione a Route table referente à Subnet Privada
  - Na aba Routes, clique no botão Edit routes
  - Clique no botão Add route
  - Na coluna Destination, selecione a opção 0.0.0.0/0
  - Na coluna Target, selecione a opção Internet Gateway
  - No campo logo abaixo, clique para selecionar o Internet Gateway específico que existe para a sua VPC e depois clique no botão Save changes
  - ##### Esta configuração de rota é necessária para que seja possível conectividade com a internet à partir da Subnet Privada
- [Desfazer depois] Vá em Network ACLs ainda no VPC, selecione o NACL associado à Subnet Privada
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (porta 8080), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 105 (este é um exemplo, tem que ser um número após a última rule que você já tinha), SSH (porta 22), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 106 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (range de porta 1024-65535), Source: 0.0.0.0/0
    - Clique no botão Save changes
  - Vá na aba Outbound rules e clique no botão Edit outbound rules
    - Clique no botão Add new rule
      - Rule number 102 (este é um exemplo, tem que ser um número após a última rule que você já tinha), HTTP (porta 80), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (range de porta 1024-65535), Destination: 0.0.0.0/0
    - Clique no botão Save changes
  - ##### Esta configuração de firewall à nível de subnet é necessária para que seja possível conectividade com a internet à partir da Subnet Privada, entrada RTMP e para o Web Server, saída para internet
- [Desfazer depois] Vá em Security Groups ainda no VPC, selecione o Security Group de Manutenção
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Clique no botão Add new rule
      - Custom TCP (porta 1935), Source: Anywhere-IPv4 - 0.0.0.0/0
    - Clique no botão Add new rule
      - Custom TCP (porta 8080), Source: Anywhere-IPv4 - 0.0.0.0/0
    - Clique no botão Save rules
  - Outbound já tem regras de saída para HTTP, HTTPS e UDP, então não é necessário fazer nada
  - ##### Esta configuração de firewall à nível de instância é necessária para que seja possível conectividade com a internet à partir da Subnet Privada, entrada RTMP e para o Web Server, saída para internet
- Vá no menu Instances no EC2, selecione a instância referente ao Owncast, clique no botão Actions, depois clique na opção Security e depois clique em Change security groups
  - Clique na barra de pesquisa, aparecerá o Security Group de Manutenção, clique no Security Group e depois clique no botão Add security group
  - Clique no botão Save
- Ainda em Instances no EC2, selecione a instância referente ao Owncast, clique no botão Instance state e depois clique em Start instance
- [Desfazer depois] Vá no menu Elastic IPs ainda no EC2, selecione o Elastic IP existente, clique no botão Actions e depois clique em Associate Elastic IP address
  - Resource type: mantenha Instance
  - Instance: seleciona a instância do Owncast (estará com status running)
  - Private IP address: clique no campo que aparecerá o IP privado da instância do Owncast, clique no IP privado
  - Reassociation: Allow this Elastic IP address to e reassociated - mantenha checado
  - Clique no botão Associate
- Vá no menu Instances no EC2 e selecione a instância de Proxy
  - Clique no botão Actions, depois clique em Security e depois clique em Change security groups
  - Em Associated security groups, clique na barra de busca e clique no Security Group referente à manutenção que foi criado em etapas anteriores
  - Depois clique no botão Add security group e clique no botão Save
  - Clique no botão Instance state e depois clique em Start instance, aguarde a coluna Instance state mudar de Stopped para Running

Agora vamos finalmente instalar o Owncast e configurá-lo:

- Pré-requisito: ter um terminal para uso de comandos bash, pode ser o [Git](https://git-scm.com/downloads)
- Abra um terminal bash na mesma pasta onde você tem o arquivo .pem, aquele que você eventualmente criou e atrelou à instância como "Key pair"
- Execute o seguinte comando para acessar a instância EC2:
```
ssh -i "[Nome_do_seu_arquivo_pem].pem" ubuntu@[IP_público_que_você_associou_no_Elastic_IP]
```
##### Como o sistema operacional escolhido foi o Ubuntu na criação da instância, você vai fazer a conexão com o usuário ubuntu mesmo, este usuário é super usuário
- Se aparecer uma pergunta sobre querer continuar a conexão, digite yes e depois pressione a tecla Enter
- Primeiro vamos atualizar o próprio sistema operacional com os seguintes comandos (execute um de cada vez):
```
sudo apt update -y
sudo apt upgrade -y
```
- Para que o Owncast consiga tratar os segmentos de vídeo, é necessário instalar o ffmpeg, além disso iremos instalar o unzip uma vez que o Owncast é um arquivo zip que iremos baixar:
```
sudo apt install ffmpeg unzip -y
```
- Agora vamos fazer o download do Owncast e descompactar o arquivo zip (execute um de cada vez):
```
sudo wget https://github.com/owncast/owncast/releases/download/v0.2.3/owncast-0.2.3-linux-64bit.zip
sudo unzip owncast-0.2.3-linux-64bit.zip
```
##### O link acima é referente à última versão do Owncast na data de escrita deste passo-a-passo, mas você pode checar a última versão [neste link](https://owncast.online/releases/), só mudar o link acima com a versão desejada
- Se tudo deu certo, você verá um arquivo binário chamado owncast na pasta através do comando ls
- Agora vamos criar um arquivo .service para que a aplicação abra como um serviço no Ubuntu, assim se a instância for reiniciada, ela "liga" automaticamente:
```
cat <<EOT | sudo tee /etc/systemd/system/owncast.service > /dev/null
[Unit]
Description=Owncast Streaming Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/owncast
Restart=on-failure
User=ubuntu

[Install]
WantedBy=multi-user.target
EOT
```
- Por fim, utilize os comandos à seguir para registrar e inicializar a aplicação como serviço:
```
sudo systemctl daemon-reload
sudo systemctl enable owncast
sudo systemctl start owncast
```
- Se deu tudo certo, o Owncast já estará executando e ativo, você pode checar isso com o seguinte comando:
```
systemctl status owncast
```
- Pode sair da instância com o comando "exit"
- Agora abra o browser de sua preferência e digite o seguinte: `[IP_público_associado_à_instância]:8080`
  - Se aparecer que o site não é seguro, é porque estamos indo via IP direto sem HTTPS e sem certificado digital, isso é normal neste momento, pode prosseguir
    - Se der certo, você deverá ver uma página conforme imagem Owncast_1.png mais acima
  - Agora vamos acessar o painel de administração, o browser coloque um /admin, ficando assim: `[IP_público_associado_à_instância]:8080/admin`
    - Usuário: admin
    - Senha (atual provisória): abc123
    - Se der certo, você deverá ver uma página conforme imagem Owncast_2.png mais acima
    - Primera coisa a se fazer no painel de administração é trocar a senha, vá para o menu Configuration -> Server Setup
      - Na aba Server Config, no campo Admin Password, digite uma nova senha (há validação de caracteres mínimos que a senha deve ter) e depois clique no botão Update (conforme imagem Owncast_3.png mais acima)
      - Ao atualizar a senha você será deslogado e precisará fazer o login novamente com o usuário "admin" usando a senha nova
    - Segunda coisa a se fazer é substituir a chave de live streaming, isso é feito também na página de Server Setup
      - Vá para a aba Stream Keys e clique no botão "+" (conforme imagem Owncast_4.png mais acima)
      - Tome nota da Key gerada, você pode também alterar o campo Comment descrevendo sua chave nova, depois clique no botão Add (conforme imagem Owncast_5.png mais acima), na imagem estou exemplificando com minha chave, não use a chave da imagem pois eu irei apagá-la
      - Agora você terá 2 chaves, delete a Default stream key clicano no botão de Lixeira logo à direita da chave (conforme imagem Owncast_6.png mais acima)
      - Você ficará apenas com a chave que acabou de criar (conforme imagem Owncast_7.png mais acima)
    - Por fim vamos configurar a integração com o Bucket S3, isso é feito também na página se Server Setup
      - Vá para a aba S3 Object Storage (estará conforme imagem Owncast_8.png mais acima)
      - O campo Use S3 Storage Provider mude de OFF para ON
      - Endpoint: `https://s3.[region_do_seu_bucket].amazonaws.com`
      - Access key: [access_key_atrelado_ao_usuario_iam_que_você_criou]
      - Secret key: [secret_key_atrelado_ao_usuario_iam_que_você_criou]
      - Bucket: [o_nome_do_bucket_que_você_criou]
      - Region: [region_do_seu_bucket]
      - Em Optional Settings:
        - ACL: private
      - Você pode ver um exemplo conforme imagem Owncast_9.png mais acima
      - Clique no botão Save

Agora vamos ao seu smartphone fazer a configuração apenas para testar se conseguimos conectar o device ao servidor e se os arquivos de segmento de vídeo passam a ser persistidos no bucket S3.

- No seu smartphone, baixe o aplicativo SJCAM Zone da SJCAM LLC (conforme imagem Owncast_10.png mais acima)
- No menu do aplicativo, há um ícone que simboliza a Live Stream (no meu caso é Android, então é na parte inferior do aplicativo, terceiro ícone da esquerda para a direita), veja que há a opção de conectar ao YouTube mas não usaremos essa opção, logo abaixo tem o Customize, dê um tap nesta opção (conforme imagem Owncast_11.png mais acima)
- Insira o seguinte no campo texto: `rtmp://[IP_público_da_instância_EC2]:1935/live/[Stream_Key_que_você_anotou_da_configuração_do_Owncast]` 
  - Exemplo: `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` (conforme imagem Owncast_12.png mais acima)
  - Dê um tap no botão Confirm
- Dê um tap no botão Next Step (conforme imagem Owncast_13.png mais acima)
- No meu app, já tenho as redes configuradas, mas se precisar incluir (na primeira vez que usar, por exemplo), dê um tap no botão + Add network (conforme imagem Owncast_14.png mais acima)
  - Você pode tanto escolher uma das redes WiFi que o app detecta automaticamente, ou você pode digitar o nome da rede
  - Indique a senha (se houver) da rede e depois dê um tap no botão Save and Use (conforme imagem Owncast_15.png mais acima)
  - No meu caso eu tenho a rede WiFi da minha residência e também do meu celular
    - ##### Para usar seu celular como hotstop WiFi (necessário caso queira fazer live stream fora de casa), você tem que lembrar de ativar seu celular como Roteador Wi-Fi
- Selecionada a rede que irá utilizar, dê um tap no botão Next
- Na tela de confirmação, dê um tap no botão Confirm (conforme imagem Owncast_16.png mais acima)
- Você pode escolher uma imagem de capa e uma descrição para sua Live Stream, mas neste caso não é necessário, dê um tap no botão Start live (conforme imagem Owncast_17.png mais acima)
- Se deu tudo certo, aparecerá um QR Code que você deverá ler com a sua câmera SJCAM SJ11 (conforme imagem Owncast_18.png mais acima)

Agora vamos começar a transmissão ao vivo, na sua câmera SJCAM SJ11, ligue ela e dê um "swipe up" para aparecer as opções da câmera (conforme imagem Owncast_19.png mais acima)

- Ao aparecem as opões, dê um "swipe up" novamente que aparecerá o botão de Live (conforme imagem Owncast_20.png mais acima)
- Dê um tap no botão Live broadcast (conforme imagem Owncast_21.png mais acima)
- Aponte a câmera SJCAM SJ11 para o QR Code do smartphone gerado no app SJCAM Zone (conforme imagem Owncast_22.png mais acima)
- Aguarde a conexão da câmera SJCAM SJ11 com o servidor do Owncast (sua instância EC2 recém configurada) (conforme imagem Owncast_23.png mais acima)
- Quando mudar o status na parte superior da câmera, você já estará ao vivo (no meu caso está em português do Brasil, então fica escrito "Transmissão ao vivo") (conforme imagem Owncast_24.png mais acima)
- Você pode checar se houve algum problema no painel de Administração do Owncast, no menu Utilities clique no item Logs, deveria aparecer algo igual à imagem Owncast_25.png mais acima
- E lá no serviço S3 no seu bucket, você verá que a pasta "hls" foi criada e dentro dela a pasta "0" também foi criada, os segmentos de vídeo serão persistidos nesta estrutura (conforme imagem Owncast_26.png mais acima)
- Para encerrar a live streaming, na sua câmera SJCAM SJ11 se a tela escureceu apenas dê um tap nela e depois dê um tap no "x" do canto superior esquerdo
- Quando você encerra a live streaming, segmento de vídeo "Offline" fica disponível (conforme imagem Owncast_27.png mais acima)
- E no app no smartphone, se não for mais fazer live streaming dê um tap no botão "stop live streaming"
  - Se você quiser, é possível iniciar outro live streaming sem parar este, basta apontar novamente a câmera SJCAM SJ11 no QR Code do app

Pronto! Agora sabemos que a instância EC2 do Owncast está funcionando perfeitamente!

##### Vamos desfazer algumas coisas:
- Vá em Security Groups no VPC, selecione o Security Group de Manutenção
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Custom TCP (porta 1935), Source: Anywhere-IPv4 - 0.0.0.0/0 -> Clique no botão Delete
    - Custom TCP (porta 8080), Source: Anywhere-IPv4 - 0.0.0.0/0 -> Clique no botão Delete
    - Clique no botão Save rules
- Vá em Network ACLs ainda no VPC, selecione o NACL associado à Subnet Privada
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Rule number 103 (este é um exemplo), Custom TCP (porta 1935), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 104 (este é um exemplo), Custom TCP (porta 8080), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 105 (este é um exemplo), SSH (porta 22), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 106 (este é um exemplo), Custom TCP (range de porta 1024-65535), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Clique no botão Save changes
  - Vá na aba Outbound rules e clique no botão Edit outbound rules
    - Rule number 102 (este é um exemplo), HTTP (porta 80), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 103 (este é um exemplo), DNS (UDP) (porta 53), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 104 (este é um exemplo), Custom TCP (range de porta 1024-65535), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Clique no botão Save changes
- Vá em Route tables ainda no VPC, selecione a Route table referente à Subnet Privada
  - Na aba Routes, clique no botão Edit routes
  - Clique no botão Add route
  - Na linha cujo Target é o Internet Gateway -> Clique no botão Remove
  - No campo logo abaixo, clique para selecionar o Internet Gateway específico que existe para a sua VPC e depois clique no botão Save changes

##### Não esqueça de desfazer as regras conforme as instruções acima, isso é necessário para assegurar acessos mínimos para evitar riscos de acessos indesejados

>[en-us]

In this step, we'll configure the EC2 instance for the Proxy to install and configure HAProxy, and the EC2 instance for Owncast to install and configure Owncast

We'll start with the Owncast instance in the Private Subnet, so we can perform a first test with the SJCAM SJ11

##### Note: We'll be making adjustments to the Route Table, NACL, and Security Group (all via VPC service) just to enable testing. I'll explain what to do and how to undo them at the end

- [Undo later] Go to Route tables in the VPC, select the Route table for the Private Subnet
  - In the Routes tab, click the Edit routes button
  - Click the Add route button
  - In the Destination column, select the 0.0.0.0/0 option
  - In the Target column, select the Internet Gateway option
  - In the field below, click to select the specific Internet Gateway that exists for your VPC and then click the Save changes button
  - ##### This route configuration is required for internet connectivity from the Private Subnet
- [Undo later] Go to Network ACLs still in the VPC, select the NACL associated with the Private Subnet
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button
    - Click the Add New Rule button
    - Rule number 103 (this is an example, it must be one number after the last rule you already had), Custom TCP (port 1935), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 104 (this is an example, it must be one number after the last rule you already had), Custom TCP (port 8080), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 105 (this is an example, it must be one number after the last rule you already had), SSH (port 22), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 106 (this is an example, it must be one number after the last rule you already had). one number after the last rule you already had), Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
    - Click the Save changes button
  - Go to the Outbound Rules tab and click the Edit Outbound Rules button
    - Click the Add New Rule button
    - Rule number 102 (this is an example, it must be one number after the last rule you already had), HTTP (port 80), Destination: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 103 (this is an example, it must be one number after the last rule you already had), DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 104 (this is an example, it must be one number after the last rule you already had), Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
    - Click the Save Changes button
    - ##### This subnet-level firewall configuration is required to allow internet connectivity from the Private Subnet, RTMP input, and the Web Server, internet output
- [Undo later] Go to Security Groups still in the VPC, select the Maintenance Security Group
  - Go to the Inbound rules tab and click the Edit inbound rules button
    - Click the Add new rule button
    - Custom TCP (port 1935), Source: Anywhere-IPv4 - 0.0.0.0/0
    - Click the Add new rule button
    - Custom TCP (port 8080), Source: Anywhere-IPv4 - 0.0.0.0/0
    - Click the Save rules button
  - Outbound already has outbound rules for HTTP, HTTPS, and UDP, so no action is needed
  - ##### This instance-level firewall configuration is required to enable internet connectivity from the Private Subnet, RTMP inbound, and for the Web Server, internet outbound
- Go to the Instances menu in EC2, select the Owncast instance, click the Actions button, then click the Security option, and then click Change security groups
  - Click the search bar. The Maintenance Security Group will appear. Click the Security Group and then click the Add security group button
  - Click the Save button
- Still in Instances in EC2, select the Owncast instance, click the Instance state button, and then click Start instance
- [Undo later] Go to the Elastic IPs menu in EC2, select the existing Elastic IP, click the Actions button, and then click Associate Elastic IP address
  - Resource type: Keep Instance
  - Instance: Select the Owncast instance (it will be in running status)
  - Private IP address: Click the field that will display the Owncast instance's private IP, click the private IP
  - Reassociation: Allow this Elastic IP address to be reassociated. Keep it checked
  - Click the Associate button
- Go to the Instances menu in EC2 and select the Proxy instance
  - Click the Actions button, then click Security, and then click Change security groups
  - Under Associated security groups, click the search bar and click the Security Group for maintenance that was created in previous steps
  - Then click the Add security group button and click the Save button
  - Click the Instance state button and then click Start instance. Wait for the Instance state column to change from Stopped to Running

Now let's finally install Owncast and configure it:

- Prerequisite: have a terminal for using bash commands, which can be [Git](https://git-scm.com/downloads)
- Open a bash terminal in the same folder where you have the .pem file, the one you eventually created and linked to the instance as a "Key pair."
- Run the following command to access the EC2 instance:
```
ssh -i "[Name_of_your_pem_file].pem" ubuntu@[Public_IP_you_associated_with_Elastic_IP]
```
##### Since Ubuntu was the operating system you chose when creating the instance, you will connect with the ubuntu user; this user is the superuser
- If a question appears asking if you want to continue the connection, type yes and then press Enter
- First, let's update the operating system itself with the following commands (run one at a time):
```
sudo apt update -y
sudo apt upgrade -y
```
- For Owncast to process the video segments, we need to install ffmpeg. We'll also install unzip since Owncast is a zip file that we'll download:
```
sudo apt install ffmpeg unzip -y
```
- Now let's download Owncast and unzip the zip file (run one at a time):
```
sudo wget https://github.com/owncast/owncast/releases/download/v0.2.3/owncast-0.2.3-linux-64bit.zip
sudo unzip owncast-0.2.3-linux-64bit.zip
```
##### The link above refers to the latest version of Owncast as of the date this walkthrough was written, but you can check the latest version [at this link](https://owncast.online/releases/), just change the link above to the desired version
- If everything went well, you will see a binary file called owncast in the folder using the ls command
- Now let's create a .service file so that the application opens as a service in Ubuntu, so that if the instance is restarted, it "turns on" automatically:
```
cat <<EOT | sudo tee /etc/systemd/system/owncast.service > /dev/null
[Unit]
Description=Owncast Streaming Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/owncast
Restart=on-failure
User=ubuntu

[Install]
WantedBy=multi-user.target
EOT
```
- Finally, use the following commands to register and start the application as a service:
```
sudo systemctl daemon-reload
sudo systemctl enable owncast
sudo systemctl start owncast
```
- If everything went well, Owncast will already be running and active. You can check this with the following command:
```
systemctl status owncast
```
- You can exit the instance with the "exit" command
- Now open your preferred web browser and type the following: `[Public_IP_associated_with_instance]:8080`
  - If it says the site is not secure, it's because we're using a direct IP address without HTTPS and without a digital certificate. This is normal at this point, so you can continue.
    - If successful, you should see a page as shown in the image Owncast_1.png above.
  - Now let's access the administration panel. In the browser, add /admin, making it look like this: `[Public_IP_associated_with_instance]:8080/admin`
    - Username: admin
    - Password (current, temporary): abc123
    - If successful, you should see a page as shown in the image Owncast_2.png above
    - The first thing to do in the administration panel is to change the password. Go to the Configuration -> Server Setup menu
      - On the Server Config tab, in the Admin Password field, enter a new password (there is a minimum character validation for the password) and Then click the Update button (as shown in the Owncast_3.png image above)
      - When you update your password, you will be logged out and will need to log in again with the "admin" username using the new password
    - The second thing to do is replace the live streaming key. This is also done on the Server Setup page
      - Go to the Stream Keys tab and click the "+" button (as shown in Owncast_4.png above)
      - Make a note of the generated key. You can also edit the Comment field to describe your new key. Then, click the Add button (as shown in Owncast_5.png above). In the image, I'm using my own key as an example. Don't use the key from the image, as I'll be deleting it
      - Now you'll have two keys. Delete the Default stream key by clicking the Trash button to the right of the key (as shown in Owncast_6.png above)
      - You'll only have the key you just created (as shown in Owncast_7.png above)
    - Finally, let's configure the integration with the S3 Bucket. This is also done on the Server Setup page
      - Go to the S3 Object Storage tab (it will be shown in the Owncast_8.png image above)
      - Change the Use S3 Storage Provider field from OFF to ON
      - Endpoint: `https://s3.[region_of_your_bucket].amazonaws.com`
      - Access key: [access_key_linked_to_the_iam_user_you_created]
      - Secret key: [secret_key_linked_to_the_iam_user_you_created]
      - Bucket: [the_name_of_the_bucket_you_created]
      - Region: [region_of_your_bucket]
      - In Optional Settings:
        - ACL: private
      - You can see an example as shown in the Owncast_9.png image above
      - Click the Save button

Now let's go to your smartphone to configure it just to test whether we can connect the device to the server and whether the video segment files are now persisted in the S3 bucket

- On your smartphone, download the SJCAM Zone app from SJCAM LLC (as shown in Owncast_10.png above)
- In the app menu, there's an icon that symbolizes Live Stream (in my case, it's on Android, so it's at the bottom of the app, third icon from left to right). Note that there's an option to connect to YouTube, but we won't use this option. Just below is Customize; tap this option (as shown in Owncast_11.png above)
- Enter the following in the text field: `rtmp://[public_IP_of_the_EC2_instance]:1935/live/[Stream_Key_you_noted_from_the_Owncast_configuration]`
  - Example: `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` (as shown in image Owncast_12.png above)
  - Tap the Confirm button
- Tap the Next Step button (as shown in image Owncast_13.png above)
- In my app, I already have the networks configured, but if you need to add them (the first time you use them, for example), tap the + Add network button (as shown in image Owncast_14.png above)
  - You can either choose one of the Wi-Fi networks that the app automatically detects, or you can enter the network name
  - Enter the network name. Enter the network password (if applicable) and then tap the Save and Use button (as shown in the Owncast_15.png image above)
  - In my case, I have both my home Wi-Fi network and my cell phone's
    - ##### To use your cell phone as a Wi-Fi hotspot (necessary if you want to live stream outside the home), you must remember to activate your cell phone as a Wi-Fi router
- Once you've selected the network you'll use, tap the Next button
- On the confirmation screen, tap the Confirm button (as shown in Owncast_16.png above)
- You can choose a cover image and description for your Live Stream, but in this case, it's not necessary. Tap the Start Live button (as shown in Owncast_17.png above)
- If everything went well, a QR Code will appear that you can scan with your SJCAM SJ11 camera (as shown in Owncast_18.png above)

Now let's start the live broadcast. On your SJCAM SJ11 camera, turn it on and swipe up to display the camera options (as shown in Owncast_19.png above)

- When the options appear, swipe up again to display the Live button (as shown in Owncast_20.png above)
- Tap the Live broadcast button (as shown in Owncast_21.png above)
- Point the SJCAM SJ11 camera at the QR Code on your smartphone generated in the SJCAM Zone app (as shown in Owncast_22.png above)
- Wait for the SJCAM SJ11 camera to connect to the Owncast server (your newly configured EC2 instance) (as shown in Owncast_23.png above)
- When the status at the top of the camera changes, you're already live (in my case, it's in Brazilian Portuguese, so it says "Transmissão ao vivo"). (as shown in the Owncast_24.png image above)
- You can check for any issues in the Owncast Administration panel. In the Utilities menu, click on the Logs item. You should see something similar to the Owncast_25.png image above
- And in the S3 service in your bucket, you'll see that the "hls" folder has been created, and within it, the "0" folder has also been created. The video segments will be persisted in this structure (as shown in the Owncast_26.png image above)
- To end the live stream, on your SJCAM SJ11 camera, if the screen has gone dark, just tap it and then tap the "x" in the upper left corner
- When you end the live streaming, the "Offline" video segment becomes available (as shown in the Owncast_27.png image above)
- And in the smartphone app, if you're no longer live streaming, tap the "stop live streaming" button
- If you want, you can start another live stream without stopping this one; just point the SJCAM SJ11 camera at the app's QR Code again

That's it! Now we know the Owncast EC2 instance is working perfectly!

##### Let's undo a few things:
- Go to Security Groups in the VPC, select the Maintenance Security Group
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button
    - Custom TCP (port 1935), Source: Anywhere-IPv4 - 0.0.0.0/0 -> Click the Delete button
    - Custom TCP (port 8080), Source: Anywhere-IPv4 - 0.0.0.0/0 -> Click the Delete button
    - Click the Save Rules button
- Go to Network ACLs still in the VPC, select the NACL associated with the Private Subnet
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button
    - Rule number 103 (this is an example), Custom TCP (port 1935), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example), Custom TCP (port 8080), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 105 (this is an example), SSH (port 22), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 106 (this is an example), Custom TCP (port range 1024-65535), Source: 0.0.0.0/0 -> Click the Remove button
    - Click the Save changes button
  - Go to the Outbound Rules tab and click the Edit Outbound Rules button
    - Rule number 102 (this is an example), HTTP (port 80), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 103 (this is an example), DNS (UDP) (port 53), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example), Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0 -> Click the Remove button
    - Click the Save Changes button
- Go to Route Tables in the VPC and select the Route Table for the Private Subnet
  - In the Routes tab, click the Edit Routes button
  - Click the Add Route button
  - In the row whose Target is Internet Gateway -> Click the Remove button
  - In the field below, click to select the specific Internet Gateway that exists for your VPC and then click the Save Changes button

##### Don't forget to undo the rules as per the instructions above, this is necessary to ensure minimum access to avoid the risk of unwanted access

[Retornar ao resumo | Return to summary](#summary)