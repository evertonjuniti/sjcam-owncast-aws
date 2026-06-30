# Configuração de rede
![Owncast-Network.svg](/Images/Owncast-Network.svg)

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
    - Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Custom TCP (porta 8080), Source: 0.0.0.0/0
  - Regras de saída
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - HTTPS (porta 443), Destination: 0.0.0.0/0

### Observação importante: para fazer a manutenção e instalação de software na instância EC2 na Subnet Pública e Privada serão necessários passos adicionais, cuja recomendação é fazer somente em momento de manutenção, depois desfaça os itens abaixo descritos
- Inclua na Route Table associado à Subnet Privada:
  - Uma rota Destination: 0.0.0.0/0, Target: Internet Gateway
- Inclua na NACL associada à Subnet Pública e Privada:
  - Regra de entrada
    - SSH (porta 22), Source: 0.0.0.0/0
  - Regra de saída
    - HTTP (porta 80), Destination: 0.0.0.0/0
    - DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Custom TCP (range de porta 1024-65535), Destination: 0.0.0.0/0
- Inclua na NACL associada à Subnet Pública:
  - Regra de entrada
    - Custom TCP (range de porta 1024-65535), Source: 0.0.0.0/0
  - Regra de saída
    - HTTPS (porta 443), Destination: 0.0.0.0/0
- Associe à instância EC2 da Subnet Pública e Privada:
  - O Security Group de manutenção de instâncias
  - Um IP público do tipo Elastic IP (aqui é uma instância por vez)

Esses passos acima farão com que seja possível a conexão com a internet para fazer a atualização de segurança da instância e eventuais instalações

Depois de fazer as instalações, desfaça todos esses itens acima citados para manter uma maior segurança do acesso à instância na Subnet Privada

---
[🏠 Índice](../README.md) | [Próximo: Criação do Bucket S3 ➡️](02-S3-Bucket.md)
