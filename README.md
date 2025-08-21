# sjcam-owncast-aws
> [pt-br]
- Recursos de infraestrutura da AWS para oferecer transmissão ao vivo privada a serem usados com a câmera SJCAM SJ11

> [en-us]
- AWS infrastructure resources to serve private live streaming to be used with SJCAM SJ11 camera

## Objetivo | Objective
> [pt-br]
- Este repositório foi criado com o intuito de ajudar pessoas que desejam fazer o armazenamento de vídeos gravados pela câmera SJCAM SJ11 na nuvem, mantendo também a privacidade de acesso a esses vídeos, uma alternativa a fazer live streaming via YouTube, que seria aberto para um público maior
- Neste repositório você encontrará informações e um passo-a-passo detalhado para criar uma infraestrutura na AWS para ter um servidor de streaming utilizando a ferramenta open source Owncast e a possibilidade de assistir aos vídeos tanto em live streaming quanto o histórico de vídeos armazenados, com controle de acesso e requisitos de segurança para diminuir o risco de exposição desses vídeos. Também inclui como configurar sua SJCAM SJ11 para usar esse servidor de streaming

> [en-us]
- This repository was created with the aim of helping people who want to store videos recorded by the SJCAM SJ11 camera in the cloud, while also maintaining privacy of access to these videos, an alternative to live streaming via YouTube, which would be open to a larger audience
- In this repository, you'll find information and a detailed step-by-step guide to creating an infrastructure on AWS to have a streaming server using the open-source Owncast tool. You'll also be able to watch both live streaming and historical stored videos, with access control and security requirements to reduce the risk of video exposure. It also includes how to configure your SJCAM SJ11 to use this streaming server

## Desenho da solução | Solution design
![Owncast-Resources-Map.drawio.svg](/Images/Owncast-Resources-Map.drawio.svg)

> [pt-br]
- Tudo que estiver escrito em vermelho são dados de exemplo que usei em meu ambiente ou são placeholders para que você substitua pelo valor correto do seu ambiente AWS. Talvez seja melhor você fazer o download da imagem acima e abrir em outra ferramenta (que não o browser), dado que são muitos detalhes contidos na imagem

> [en-us]
- Everything written in red is either example data that I used in my environment or are placeholders for you to replace with the correct value for your AWS environment. It might be best to download the image above and open it in another tool (other than the browser), given that there are many details contained in the image

## Fluxos de uso da solução | Solution usage flows
#### Gravação via Live Streaming | Recording via Live Streaming
> [pt-br]
- A câmera SJCAM SJ11 utiliza o protocolo RTMP (via porta 1935) para conectividade com o servidor de Proxy que por sua vez se conecta ao servidor Owncast, que possibilita gravar os segmentos de vídeo (arquivos .ts) no Bucket

> [en-us]
- The SJCAM SJ11 camera uses the RTMP protocol (via port 1935) for connectivity with the Proxy server, which in turn connects to the Owncast server, which makes it possible to record video segments (.ts files) in the Bucket

![Owncast-Camera.drawio.svg](/Images/Owncast-Camera.drawio.svg)

#### Visualização dos vídeos | Video viewing
> [pt-br]
- Pela página HTML, o login deve ser feito (via Cognito) para acesso aos recursos, uma API é utilizada tanto para exibir o status de execução dos servidores, ligar ou desligar os servidores e listar os vídeos disponíveis, incluindo opção de assistir ao vivo. Dado que os segmentos dos vídeos são servidos através de cookies, a distribuição do CloudFront faz essa ponte com o Bucket S3 onde estão os segmentos de vídeo

> [en-us]
- Through the HTML page, you must log in (via Cognito) to access resources. An API is used to display server execution status, turn servers on or off, and list available videos, including the option to watch live. Since video segments are served via cookies, CloudFront's distribution bridges this gap with the S3 bucket where the video segments are stored

![Owncast-VideoPlayer.drawio.svg](/Images/Owncast-VideoPlayer.drawio.svg)

#### Administração do servidor Owncast | Owncast server administration
> [pt-br]
- O acesso à página de administração do Owncast é acessado via servidor de Proxy que faz o encaminhamento para o servidor do Owncast, a página com o player apesar de ser acessível, não exibe live streaming em momento de transmissão da câmera através de uma configuração no servidor de Proxy

> [en-us]
- Access to the Owncast administration page is accessed via a Proxy server that forwards to the Owncast server. The page with the player, although accessible, does not display live streaming when the camera is transmitting through a configuration on the Proxy server.

![Owncast-Administration.drawio.svg](/Images/Owncast-Administration.drawio.svg)

## Implantando a solução | Deploying the solution
> [pt-br]
- Acesse a pasta [Instructions](Instructions/README.md) deste repositório para seguir o passo-a-passo de instalação e configuração do ambiente AWS e da câmera SJCAM SJ11

> [en-us]
- Access the [Instructions](Instructions/README.md) folder of this repository to follow the step-by-step installation and configuration of the AWS environment and the SJCAM SJ11 camera

## Escolhas e Trade-offs da solução | Solution Choices and Trade-offs
> [pt-br] 
- Owncast: foi a opção open source que encontrei para live streaming compatível com a SJCAM SJ11 (através do protocolo RTMP) e que possibilitasse a guarda dos arquivos de vídeo em Bucket S3 na AWS, uma vez que eu já tinha conta na AWS. Precisava deste tipo de solução para manter os vídeos privados, até há a opção de streaming via YouTube nas configurações do aplicativo da SJCAM, porém eu precisaria ter no mínimo 50 inscritos (que não tenho) e os vídeos não ficariam tão privados, acredito que seriam acessíveis aos inscritos que obtivessem o link da live streaming. O trade-off aqui é que a documentação do Owncast diz o que é compatível, mas não há nenhum manual passo-a-passo de como configurar com um mínimo de privacidade, por isso eu criei este passo-a-passo
- HAProxy: achei muito mais simples e fácil de configurar em comparação a um Nginx (me pareceu que eu precisaria do Nginx Plus para o que precisava, que é pago), por isso o HAProxy foi minha escolha (por ser gratuito também)
- Application Load Balancer (para HTTPS) e Network Load Balancer (para RTMP): Não utilizo. Cheguei a incluir na solução, porém minha necessidade não era alta disponibilidade (só 1 servidor de Proxy e 1 servidor do Owncast bastavam) e estes serviços custam caro. Cada load balancer custa minimamente 24.82 USD mesmo que não sejam utilizados (ou seja, totalizava quase 50 USD por mês)
- WAF: Não utilizo. Cheguei a incluir na solução, porém como eu tenho controle de acesso via Cognito para o site (portanto uso de autenticação), NACLs e Security Groups bem definidos, ligo os servidores só quando preciso, colocando prós e contras achei que o custo mínimo de 9.60 USD ao mês não valia a existência do WAF na frente dos meus serviços
- NAT Gateway: Não utilizo. Cheguei a incluir na solução para a Subnet Privada, porém a única saída para a internet estava sendo o serviço do S3, o NAT Gateway gera um custo mínimo de 67.90 USD mesmo sem usar. Resolvi incluindo um VPC Endpoint para o S3, assim não precisava sair para a internet. Quando necessário configuração ou manutenção das instâncias da Subnet Privada, simplesmente incluía o Internet Gateway na Route Table associada à Subnet Privada, incluía no NACL entrada na porta 22 (TCP SSH) e saída na 80 (TCP HTTP) e 53 (DNS UDP) e atrelada o Security Group de Manutenção na instância, depois de configurar desfazia isso tudo para não permitir acesso pela internet nem pelas portas (22 no caso)
- Cognito: optei pelo uso do Cognito pois precisava de autenticação simples, cheguei a usar o Firebase validando no backend (Lambda) se o e-mail do token era um dos e-mails que cadastrei no Secrets Manager, mas haviam 2 problemas: antes eu havia configurado o Lambda para executar dentro da VPC na Subnet Privada, então o acesso ao Firebase também dependia de internet e ao remover o NAT Gateway isso não seria possível, mesmo mudando o Lambda para fora da VPC (e com isso tendo acesso à internet), a validação do e-mail versus token do Firebase no Lambda era ruim, dado que eu poderia sofrer um ataque de chamadas massivas. O Cognito me permitiu fazer a validação do token de autorização no API Gateway e assim usei essa barreira para evitar a chamada do Lambda de forma massiva
- Observação: Na criação de certificado digital (criei vários no processo por falta de conhecimento) acabei marcando o Enable export em Allow export por engano, isso gerou um custo de 164 USD em que eu precisei acionar o suporte para reembolso, então tome cuidado pois a informação sobre este custo não é claro na documentação da AWS (só na calculadora de preços)

> [en-us] 
- Owncast: This was the open-source option I found for live streaming compatible with the SJCAM SJ11 (via the RTMP protocol) and that allowed me to save the video files in an S3 bucket on AWS, since I already had an AWS account. I needed this type of solution to keep the videos private. There is even a YouTube streaming option in the SJCAM app settings, but I would need to have at least 50 subscribers (which I don't have), and the videos wouldn't be as private. I believe they would be accessible to subscribers who obtained the live streaming link. The trade-off here is that the Owncast documentation says what is supported, but there is no step-by-step guide on how to set it up with a minimum of privacy, so I created this walkthrough
- HAProxy: I found it much simpler and easier to configure than Nginx (it seemed to me that I would need Nginx Plus for what I needed, which is paid), which is why HAProxy was my choice (because it's free too)
- Application Load Balancer (for HTTPS) and Network Load Balancer (for RTMP): I don't use them. I included them in the solution, but my need wasn't for high availability (just one proxy server and one Owncast server would be enough), and these services are expensive. Each load balancer costs at least USD 24.82 even if they're not used (i.e. it totaled almost 50 USD per month)
- WAF: I don't use them. I included them in the solution, but since I have access control via Cognito for the website (thus using authentication), NACLs, and well-defined Security Groups, I only turn on the servers when needed. Weighing the pros and cons, I felt the minimum cost of USD 9.60 per month wasn't worth the WAF's presence in front of my services
- NAT Gateway: I don't use it. I included it in the Private Subnet solution, but the only way to access the internet was through S3. The NAT Gateway generates a minimum cost of USD 67.90 even without using it. I resolved this by including a VPC Endpoint for S3, so I didn't need to access the internet. When it was necessary to configure or maintain instances in the Private Subnet, I simply included the Internet Gateway in the Route Table associated with the Private Subnet, included in the NACL inbound port 22 (TCP SSH) and outbound ports 80 (TCP HTTP) and 53 (DNS UDP), and attached the Maintenance Security Group to the instance. After configuring, I undid all of this to prevent access from the internet or through ports (22 in this case)
- Cognito: I chose to use Cognito because I needed simple authentication. I even used Firebase, validating in the backend (Lambda) whether the token's email was one of the emails I registered in Secrets Manager. However, there were two problems: I had previously configured Lambda to run within the VPC in the Private Subnet, so access to Firebase also depended on the internet. By removing the NAT Gateway, this would not be possible. Even moving Lambda outside the VPC (and thus having internet access), the validation of the email versus the Firebase token in Lambda was difficult, as I could suffer a mass call attack. Cognito allowed me to validate the authorization token in the API Gateway, and so I used this barrier to prevent the mass Lambda call
- Note: When creating a digital certificate (I created several during the process due to lack of knowledge), I ended up selecting the Enable export option under Allow export by mistake. This generated a cost of USD 164, for which I had to contact support for a refund. So be careful, as the information about this cost is not clear in the AWS documentation (only in the pricing calculator)