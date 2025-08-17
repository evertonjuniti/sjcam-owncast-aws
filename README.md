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
![Owncast.drawio.png](/Images/Owncast.drawio.png)

> [pt-br] Tudo que estiver escrito em vermelho são dados de exemplo que usei em meu ambiente ou são placeholders para que você substitua pelo valor correto do seu ambiente AWS. Talvez seja melhor você fazer o download da imagem acima e abrir em outra ferramenta (que não o browser), dado que são muitos detalhes contidos na imagem

> [en-us] Everything written in red is either example data that I used in my environment or are placeholders for you to replace with the correct value for your AWS environment. It might be best to download the image above and open it in another tool (other than the browser), given that there are many details contained in the image