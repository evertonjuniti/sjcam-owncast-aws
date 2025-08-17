# sjcam-owncast-aws
> [pt-br] Recursos de infraestrutura da AWS para oferecer transmissão ao vivo privada a serem usados com a câmera SJCAM SJ11

> [en-us] AWS infrastructure resources to serve private live streaming to be used with SJCAM SJ11 camera

## Objetivo | Objective
> [pt-br] Este repositório foi criado com o intuito de ajudar pessoas que desejam fazer o armazenamento de vídeos gravados pela câmera SJCAM SJ11 na nuvem, mantendo também a privacidade de acesso a esses vídeos, uma alternativa a fazer live streaming via YouTube, que seria aberto para um público maior

> [en-us] This repository was created with the aim of helping people who want to store videos recorded by the SJCAM SJ11 camera in the cloud, while also maintaining privacy of access to these videos, an alternative to live streaming via YouTube, which would be open to a larger audience

<br/>

> [pt-br] Neste repositório você encontrará informações e um passo-a-passo detalhado para criar uma infraestrutura na AWS para ter um servidor de streaming utilizando a ferramenta open source Owncast e a possibilidade de assistir aos vídeos tanto em live streaming quanto o histórico de vídeos armazenados, com controle de acesso e requisitos de segurança para diminuir o risco de exposição desses vídeos. Também inclui como configurar sua SJCAM SJ11 para usar esse servidor de streaming

> [en-us] In this repository, you'll find information and a detailed step-by-step guide to creating an infrastructure on AWS to have a streaming server using the open-source Owncast tool. You'll also be able to watch both live streaming and historical stored videos, with access control and security requirements to reduce the risk of video exposure. It also includes how to configure your SJCAM SJ11 to use this streaming server

## Desenho da solução | Solution design
![Owncast-Resources-Map.drawio.svg](/Images/Owncast-Resources-Map.drawio.svg)

> [pt-br] Tudo que estiver escrito em vermelho são dados de exemplo que usei em meu ambiente ou são placeholders para que você substitua pelo valor correto do seu ambiente AWS. Talvez seja melhor você fazer o download da imagem acima e abrir em outra ferramenta (que não o browser), dado que são muitos detalhes contidos na imagem

> [en-us] Everything written in red is either example data that I used in my environment or are placeholders for you to replace with the correct value for your AWS environment. It might be best to download the image above and open it in another tool (other than the browser), given that there are many details contained in the image

## Fluxos de uso da solução | Solution usage flows
#### Gravação via Live Streaming | Recording via Live Streaming
> [pt-br] A câmera SJCAM SJ11 utiliza o protocolo RTMP (via porta 1935) para conectividade com o servidor de Proxy que por sua vez se conecta ao servidor Owncast, que possibilita gravar os segmentos de vídeo (arquivos .ts) no Bucket

> [en-us] The SJCAM SJ11 camera uses the RTMP protocol (via port 1935) for connectivity with the Proxy server, which in turn connects to the Owncast server, which makes it possible to record video segments (.ts files) in the Bucket

![Owncast-Camera.drawio.svg](/Images/Owncast-Camera.drawio.svg)

#### Visualização dos vídeos | Video viewing
> [pt-br] Pela página HTML, o login deve ser feito (via Cognito) para acesso aos recursos, uma API é utilizada tanto para exibir o status de execução dos servidores, ligar ou desligar os servidores e listar os vídeos disponíveis, incluindo opção de assistir ao vivo. Dado que os segmentos dos vídeos são servidos através de cookies, a distribuição do CloudFront faz essa ponte com o Bucket S3 onde estão os segmentos de vídeo

> [en-us] Through the HTML page, you must log in (via Cognito) to access resources. An API is used to display server execution status, turn servers on or off, and list available videos, including the option to watch live. Since video segments are served via cookies, CloudFront's distribution bridges this gap with the S3 bucket where the video segments are stored

![Owncast-VideoPlayer.drawio.svg](/Images/Owncast-VideoPlayer.drawio.svg)

#### Administração do servidor Owncast | Owncast server administration
> [pt-br] O acesso à página de administração do Owncast é acessado via servidor de Proxy que faz o encaminhamento para o servidor do Owncast, a página com o player apesar de ser acessível, não exibe live streaming em momento de transmissão da câmera através de uma configuração no servidor de Proxy

> [en-us] Access to the Owncast administration page is accessed via a Proxy server that forwards to the Owncast server. The page with the player, although accessible, does not display live streaming when the camera is transmitting through a configuration on the Proxy server.

![Owncast-Administration.drawio.svg](/Images/Owncast-Administration.drawio.svg)

## Implantando a solução | Deploying the solution
> [pt-br] Acesse a pasta [Instructions](Instructions/README.md) deste repositório para seguir o passo-a-passo de instalação e configuração do ambiente AWS e da câmera SJCAM SJ11

> [en-us] Access the [Instructions](Instructions/README.md) folder of this repository to follow the step-by-step installation and configuration of the AWS environment and the SJCAM SJ11 camera