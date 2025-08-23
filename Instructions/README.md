# Instruções de instalação e configuração | Installation and configuration instructions
## Ordem de configuração dos recursos | Resource configuration order
> [pt-br] Para facilitar o passo-a-passo, haverá uma certa ordem de configuração dos recursos no ambiente da AWS, talvez certas configurações não façam muito sentido num primeiro momento, mas tentarei explicar de forma mais detalhada possível por questões didáticas e para melhor aproveitamento das informações aqui contidas. Fica avisado que a referência das informações é a versão do Console da AWS do terceiro trimestre de 2025, a depender da época que você estiver visualizando este guia pode ser que algumas diferenças surjam

>[en-us] To make the step-by-step process easier, there will be a specific order for configuring resources in the AWS environment. Some configurations may not make much sense at first, but I'll try to explain them in as much detail as possible for educational purposes and to better understand the information contained herein. Please note that the information references the AWS Console version from Q3 2025; depending on when you're viewing this guide, some differences may arise.

<a name="summary"></a>

### Resumo dos passos de configuração | Summary of configuration steps

>[pt-br]
Vou dividir as instruções em duas partes: a primeira é para configurar o servidor em si que é a parte mais imporante, a segunda é a página de constrole das instâncias e visualização dos vídeos, que é opcional

>[en-us]
I will divide the instructions into two parts: the first is to configure the server itself, which is the most important part; the second is the instance control page and video viewing, which is optional.

#### Primeira parte | First part
- [Configuração de rede](docs-pt-br/01-Network.md) | [Network configuration](docs-en-us/01-Network.md)
- [Criação do Bucket S3](docs-pt-br/02-S3-Bucket.md) | [Creating S3 an Bucket](docs-en-us/02-S3-Bucket.md)
- [Criação das instâncias EC2](docs-pt-br/03-EC2-instance-creation.md) | [Creating EC2 instances](docs-en-us/03-EC2-instance-creation.md)
- [Configuração de policies, roles e usuário do IAM](docs-pt-br/04-IAM.md) | [Configuring IAM policies, roles, and users](docs-en-us/04-IAM.md)
- [Configuração da instância EC2 do Owncast](docs-pt-br/05-Owncast-EC2-instance-configuration.md) | [Owncast EC2 instance configuration](docs-en-us/05-Owncast-EC2-instance-configuration.md)
- [Configuração da instância EC2 de Proxy](docs-pt-br/06-Proxy-EC2-instance-configuration.md) | [Proxy EC2 instance configuration](docs-en-us/06-Proxy-EC2-instance-configuration.md)

#### Segunda parte | Second part
- [Configuração do Route 53](docs-pt-br/07-Route53.md) | [Route 53 configuration](docs-en-us/07-Route53.md)
- [Criação de certificado digital](docs-pt-br/08-Certificate.md) | [Digital certificate creation](docs-en-us/08-Certificate.md)
- [Criação das Secrets](docs-pt-br/09-Secrets.md) | [Creation of Secrets](docs-en-us/09-Secrets.md)
- [Configuração do Cognito](docs-pt-br/10-Cognito.md) | [Cognito configuration](docs-en-us/10-Cognito.md)