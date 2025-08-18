# Instruções de instalação e configuração | Installation and configuration instructions
## Ordem de configuração dos recursos | Resource configuration order
> [pt-br] Para facilitar o passo-a-passo, haverá uma certa ordem de configuração dos recursos no ambiente da AWS, talvez certas configurações não façam muito sentido num primeiro momento, mas tentarei explicar de forma mais detalhada possível por questões didáticas e para melhor aproveitamento das informações aqui contidas. Fica avisado que a referência das informações é a versão do Console da AWS do terceiro trimestre de 2025, a depender da época que você estiver visualizando este guia pode ser que algumas diferenças surjam

>[en-us] To make the step-by-step process easier, there will be a specific order for configuring resources in the AWS environment. Some configurations may not make much sense at first, but I'll try to explain them in as much detail as possible for educational purposes and to better understand the information contained herein. Please note that the information references the AWS Console version from Q3 2025; depending on when you're viewing this guide, some differences may arise.

<a name="summary"></a>

### Resumo dos passos de configuração | Summary of configuration steps

- [Configuração de rede | Network configuration](#network-configuration)

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
  - Faça a associação desta Route Table à Subnet Privada criada

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

[Retornar ao resumo | Return to summary](#summary)