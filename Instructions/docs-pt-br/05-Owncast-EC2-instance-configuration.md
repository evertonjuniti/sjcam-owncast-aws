# Configuração das instâncias EC2
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

Nesta etapa iremos configurar a instância EC2 referente ao Owncast para instalação e configuração do Owncast

### Atenção: faremos ajustes no Route Table, NACL, Security Group (todos via serviço VPC) apenas para possibilitar os testes, eu vou indicar o que fazer e como desfazer ao final

- [Desfazer depois] Vá em Route tables no VPC, selecione a Route table referente à Subnet Privada
  - Na aba Routes, clique no botão Edit routes
  - Clique no botão Add route
  - Na coluna Destination, selecione a opção 0.0.0.0/0
  - Na coluna Target, selecione a opção Internet Gateway
  - No campo logo abaixo, clique para selecionar o Internet Gateway específico que existe para a sua VPC e depois clique no botão Save changes
  - #### Esta configuração de rota é necessária para que seja possível conectividade com a internet à partir da Subnet Privada
- [Desfazer depois] Vá em Network ACLs ainda no VPC, selecione o NACL associado à Subnet Privada
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (porta 1935), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (porta 8080), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 105 (este é um exemplo, tem que ser um número após a última rule que você já tinha), SSH (porta 22), Source: 0.0.0.0/0
    - Clique no botão Save changes
  - Vá na aba Outbound rules e clique no botão Edit outbound rules
    - Clique no botão Add new rule
      - Rule number 102 (este é um exemplo, tem que ser um número após a última rule que você já tinha), HTTP (porta 80), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (range de porta 1024-65535), Destination: 0.0.0.0/0
    - Clique no botão Save changes
  - #### Esta configuração de firewall à nível de subnet é necessária para que seja possível conectividade com a internet à partir da Subnet Privada, entrada RTMP e para o Web Server, saída para internet
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

Agora vamos finalmente instalar o Owncast e configurá-lo:

- Pré-requisito: ter um terminal para uso de comandos bash, pode ser o [Git](https://git-scm.com/downloads)
- Abra um terminal bash na mesma pasta onde você tem o arquivo .pem, aquele que você eventualmente criou e atrelou à instância como "Key pair"
- Execute o seguinte comando para acessar a instância EC2:
```
ssh -o HostKeyAlias=Owncast -i "[Nome_do_seu_arquivo_pem].pem" ubuntu@[IP_público_que_você_associou_no_Elastic_IP]
```
### Como o sistema operacional escolhido foi o Ubuntu na criação da instância, você vai fazer a conexão com o usuário ubuntu mesmo, este usuário é super usuário
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
### O link acima é referente à última versão do Owncast na data de escrita deste passo-a-passo, mas você pode checar a última versão [neste link](https://owncast.online/releases/), só mudar o link acima com a versão desejada
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
- Agora abra o browser de sua preferência e digite o seguinte: `[PUBLIC_IP_ASSOCIATED_WITH_INSTANCE]:8080`
  - Se aparecer que o site não é seguro, é porque estamos indo via IP direto sem HTTPS e sem certificado digital, isso é normal neste momento, pode prosseguir
    - Se der certo, você deverá ver uma página

    ![Owncast_01.png](/Images/Owncast_01.png)
  - Agora vamos acessar o painel de administração, o browser coloque um /admin, ficando assim: `[PUBLIC_IP_ASSOCIATED_WITH_INSTANCE]:8080/admin`
    - Usuário: admin
    - Senha (atual provisória): abc123
    - Se der certo, você deverá ver uma página

    ![Owncast_02.png](/Images/Owncast_02.png)
    - Primera coisa a se fazer no painel de administração é trocar a senha, vá para o menu Configuration -> Server Setup
      - Na aba Server Config, no campo Admin Password, digite uma nova senha (há validação de caracteres mínimos que a senha deve ter) e depois clique no botão Update

      ![Owncast_03.png](/Images/Owncast_03.png)
      - Ao atualizar a senha você será deslogado e precisará fazer o login novamente com o usuário "admin" usando a senha nova
    - Segunda coisa a se fazer é substituir a chave de live streaming, isso é feito também na página de Server Setup
      - Vá para a aba Stream Keys e clique no botão "+"

      ![Owncast_04.png](/Images/Owncast_04.png)
      - Tome nota da Key gerada, você pode também alterar o campo Comment descrevendo sua chave nova, depois clique no botão Add, na imagem estou exemplificando com minha chave, não use a chave da imagem pois eu irei apagá-la

      ![Owncast_05.png](/Images/Owncast_05.png)
      - Agora você terá 2 chaves, delete a Default stream key clicano no botão de Lixeira logo à direita da chave

      ![Owncast_06.png](/Images/Owncast_06.png)
      - Você ficará apenas com a chave que acabou de criar

      ![Owncast_07.png](/Images/Owncast_07.png)
    - Por fim vamos configurar a integração com o Bucket S3, isso é feito também na página se Server Setup
      - Vá para a aba S3 Object Storage

      ![Owncast_08.png](/Images/Owncast_08.png)
      - O campo Use S3 Storage Provider mude de OFF para ON
      - Endpoint: `https://s3.[region_do_seu_bucket].amazonaws.com`
      - Access key: [access_key_atrelado_ao_usuario_iam_que_você_criou]
      - Secret key: [secret_key_atrelado_ao_usuario_iam_que_você_criou]
      - Bucket: [o_nome_do_bucket_que_você_criou]
      - Region: [region_do_seu_bucket]
      - Em Optional Settings:
        - ACL: private
      - Você pode ver um exemplo:

      ![Owncast_09.png](/Images/Owncast_09.png)
      - Clique no botão Save

Agora vamos ao seu smartphone fazer a configuração apenas para testar se conseguimos conectar o device ao servidor e se os arquivos de segmento de vídeo passam a ser persistidos no bucket S3.

- No seu smartphone, baixe o aplicativo SJCAM Zone da SJCAM LLC

![Owncast_10.png](/Images/Owncast_10.png)
- No menu do aplicativo, há um ícone que simboliza a Live Stream (no meu caso é Android, então é na parte inferior do aplicativo, terceiro ícone da esquerda para a direita), veja que há a opção de conectar ao YouTube mas não usaremos essa opção, logo abaixo tem o Customize, dê um tap nesta opção

![Owncast_11.png](/Images/Owncast_11.png)
- Insira o seguinte no campo texto: `rtmp://[PUBLIC_IP_ASSOCIATED_WITH_INSTANCE]:1935/live/[Stream_Key_que_você_anotou_da_configuração_do_Owncast]` 
  - Exemplo: `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T`

  ![Owncast_12.png](/Images/Owncast_12.png)
  - Dê um tap no botão Confirm
- Dê um tap no botão Next Step

![Owncast_13.png](/Images/Owncast_13.png)
- No meu app, já tenho as redes configuradas, mas se precisar incluir (na primeira vez que usar, por exemplo), dê um tap no botão + Add network

![Owncast_14.png](/Images/Owncast_14.png)
  - Você pode tanto escolher uma das redes WiFi que o app detecta automaticamente, ou você pode digitar o nome da rede
  - Indique a senha (se houver) da rede e depois dê um tap no botão Save and Use

  ![Owncast_15.png](/Images/Owncast_15.png)
  - No meu caso eu tenho a rede WiFi da minha residência e também do meu celular
    - #### Para usar seu celular como hotstop WiFi (necessário caso queira fazer live stream fora de casa), você tem que lembrar de ativar seu celular como Roteador Wi-Fi
- Selecionada a rede que irá utilizar, dê um tap no botão Next
- Na tela de confirmação, dê um tap no botão Confirm

![Owncast_16.png](/Images/Owncast_16.png)
- Você pode escolher uma imagem de capa e uma descrição para sua Live Stream, mas neste caso não é necessário, dê um tap no botão Start live

![Owncast_17.png](/Images/Owncast_17.png)
- Se deu tudo certo, aparecerá um QR Code que você deverá ler com a sua câmera SJCAM SJ11

![Owncast_18.png](/Images/Owncast_18.png)

Agora vamos começar a transmissão ao vivo, na sua câmera SJCAM SJ11, ligue ela e dê um "swipe up" para aparecer as opções da câmera

![Owncast_19.png](/Images/Owncast_19.png)

- Ao aparecem as opões, dê um "swipe up" novamente que aparecerá o botão de Live

![Owncast_20.png](/Images/Owncast_20.png)
- Dê um tap no botão Live broadcast

![Owncast_21.png](/Images/Owncast_21.png)
- Aponte a câmera SJCAM SJ11 para o QR Code do smartphone gerado no app SJCAM Zone

![Owncast_22.png](/Images/Owncast_22.png)
- Aguarde a conexão da câmera SJCAM SJ11 com o servidor do Owncast (sua instância EC2 recém configurada)

![Owncast_23.png](/Images/Owncast_23.png)
- Quando mudar o status na parte superior da câmera, você já estará ao vivo (no meu caso está em português do Brasil, então fica escrito "Transmissão ao vivo")

![Owncast_24.png](/Images/Owncast_24.png)
- Você pode checar se houve algum problema no painel de Administração do Owncast, no menu Utilities clique no item Logs, deveria aparecer algo igual ao exemplo:

![Owncast_25.png](/Images/Owncast_25.png)
- E lá no serviço S3 no seu bucket, você verá que a pasta "hls" foi criada e dentro dela a pasta "0" também foi criada, os segmentos de vídeo serão persistidos nesta estrutura

![Owncast_26.png](/Images/Owncast_26.png)
- Para encerrar a live streaming, na sua câmera SJCAM SJ11 se a tela escureceu apenas dê um tap nela e depois dê um tap no "x" do canto superior esquerdo
- Quando você encerra a live streaming, segmento de vídeo "Offline" fica disponível

![Owncast_27.png](/Images/Owncast_27.png)
- E no app no smartphone, se não for mais fazer live streaming dê um tap no botão "stop live streaming"
  - Se você quiser, é possível iniciar outro live streaming sem parar este, basta apontar novamente a câmera SJCAM SJ11 no QR Code do app

Pronto! Agora sabemos que a instância EC2 do Owncast está funcionando perfeitamente!

### Vamos desfazer algumas coisas:
- Vá em Network ACLs no VPC, selecione o NACL associado à Subnet Privada
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Rule number 103 (este é um exemplo), Custom TCP (porta 1935), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 104 (este é um exemplo), Custom TCP (porta 8080), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 105 (este é um exemplo), SSH (porta 22), Source: 0.0.0.0/0 -> Clique no botão Remove
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

### Não esqueça de desfazer as regras conforme as instruções acima, isso é necessário para assegurar acessos mínimos para evitar riscos de acessos indesejados
### Lembre de desligar as instâncias para não gerar cobranças adicionais

## Atualizações recorrentes

Lembre-se de atualizar de forma recorrente esta instância EC2 para obter as atualizações de sistema operacional e também de todo software instalado na máquina.

Acima já está explicado como fazer a atualização, que requer os passos de alteração no NACL, atribuição de Security Group e role na instância EC2, mas também há uma opção mais automatizada para fazer isso.

Em [Configuração da função Lambda](11-Lambda.md) você encontrará instruções para automatizar essas atualizações através da criação de uma nova Policy e Role e Função Lambda que fará as alterações de infraestrutura necessárias para conexão à instância via SSM e execução de todos os comandos necessários.

---
[⬅️ Anterior: Configuração de policies, roles e usuário do IAM](04-IAM.md) | [🏠 Índice](../README.md) | [Próximo: Configuração da instância EC2 de Proxy ➡️](06-Proxy-EC2-instance-configuration.md)