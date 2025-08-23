# Criação das instâncias EC2
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

- Instância EC2 para o servidor de Proxy (utilizando HAProxy)
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.micro
  - Key pair: pode selecionar alguma que já tenha, se não tiver crie um novo par
    - #### se for criar um, guarde o arquivo .pem em um local na sua máquina, você vai precisar disso para acessar a instância depois
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
    - #### se for criar um, guarde o arquivo .pem em um local na sua máquina, você vai precisar disso para acessar a instância depois
  - Network settings:
    - VPC: VPC default (seguindo o exemplo deste guia)
    - Subnet: a Subnet Privada que você criou
    - Security Group: escolha o Security Group que você criou para uso do Owncast
  - Demais configurações pode manter o default

### Observações importantes: Tome nota do Instance ID de ambas as instâncias EC2 e do endereço IP elástico

---
[⬅️ Anterior: Criação do Bucket S3](02-S3-Bucket.md) | [🏠 Índice](../README.md) | [Próximo: Configuração da instância EC2 do Owncast ➡️](04-Owncast-EC2-instance-configuration.md)