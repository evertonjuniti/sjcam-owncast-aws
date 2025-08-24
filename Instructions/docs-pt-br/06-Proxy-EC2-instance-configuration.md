# Configuração da instância EC2 de Proxy
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

Nesta etapa iremos configurar a instância EC2 referente ao Proxy para instalação e configuração do HAProxy

### Atenção: faremos ajustes no NACL apenas para possibilitar os testes, eu vou indicar o que fazer e como desfazer ao final

- [Desfazer depois] Vá em Network ACLs ainda no VPC, selecione o NACL associado à Subnet Pública
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), SSH (porta 22), Source: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), Custom TCP (range de porta 1024 - 65535), Source: 0.0.0.0/0
    - Clique no botão Save changes
  - Vá na aba Outbound rules e clique no botão Edit outbound rules
    - Clique no botão Add new rule
      - Rule number 103 (este é um exemplo, tem que ser um número após a última rule que você já tinha), HTTP (porta 80), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 104 (este é um exemplo, tem que ser um número após a última rule que você já tinha), DNS (UDP) (porta 53), Destination: 0.0.0.0/0
    - Clique no botão Add new rule
      - Rule number 105 (este é um exemplo, tem que ser um número após a última rule que você já tinha), HTTPS (porta 443), Destination: 0.0.0.0/0
    - Clique no botão Save changes
  - #### Esta configuração de firewall à nível de subnet é necessária para que seja possível conectividade com a internet à partir da Subnet Privada, entrada RTMP e para o Web Server, saída para internet
- Vá no menu Instances no EC2, selecione a instância referente ao Proxy, clique no botão Actions, depois clique na opção Security e depois clique em Change security groups
  - Clique na barra de pesquisa, aparecerá o Security Group de Manutenção, clique no Security Group e depois clique no botão Add security group
  - Clique no botão Save
- Ainda em Instances no EC2, selecione a instância referente ao Proxy, clique no botão Instance state e depois clique em Start instance

Abaixo já iremos deixar configurado o IP Público para a instância EC2 de Proxy, esta configuração pode permanecer (não deve ser desfeita)

- Vá no menu Elastic IPs ainda no EC2, selecione o Elastic IP existente, clique no botão Actions e depois clique em Associate Elastic IP address
  - Resource type: mantenha Instance
  - Instance: seleciona a instância do Proxy (estará com status running)
  - Private IP address: clique no campo que aparecerá o IP privado da instância do Proxy, clique no IP privado
  - Reassociation: Allow this Elastic IP address to e reassociated - mantenha checado
  - Clique no botão Associate

Agora vamos finalmente instalar o HAProxy e configurá-lo:

- Pré-requisito: ter um terminal para uso de comandos bash (o mesmo usado quando configuramos a instância EC2 do Owncast), pode ser o [Git](https://git-scm.com/downloads)
- Abra um terminal bash na mesma pasta onde você tem o arquivo .pem, aquele que você eventualmente criou e atrelou à instância como "Key pair"
- Execute o seguinte comando para acessar a instância EC2:
```
ssh -o HostKeyAlias=Proxy -i "[Nome_do_seu_arquivo_pem].pem" ubuntu@[Public_IP_que_você_associou_no_Elastic_IP]
```
### Como o sistema operacional escolhido foi o Ubuntu na criação da instância, você vai fazer a conexão com o usuário ubuntu mesmo, este usuário é super usuário
- Se aparecer uma pergunta sobre querer continuar a conexão, digite yes e depois pressione a tecla Enter
- Primeiro vamos atualizar o próprio sistema operacional com os seguintes comandos (execute um de cada vez):
```
sudo apt update -y
sudo apt upgrade -y
```
- Para instalar o HAProxy, execute o seguinte comando:
```
sudo apt install haproxy -y
```
### Agora temos 2 opções de configuração: Opção A (recomendado) com uso de domínio e certificado digital; Opção B sem uso de domínio e sem certificado digital

#### Opção A
- Se você já tiver um domínio e hosted zone configurado no Route 53 prossiga, caso contrário vá para a instrução [Configuração do Route 53](docs-pt-br/07-Route53.md) e siga as instruções, depois retorne aqui
- Agora precisamos adicionar o [YOUR_SUB_DOMAIN] (você vai precisar escolher algum nome) como Record no Route 53, assim conseguiremos configurar o DNS para que possamos chamar [YOUR_SUB_DOMAIN].[YOUR_DOMAIN] ao invés do [Public_IP]:
  - Vá em Hosted zones no Route 53 e clique na sua hosted zone
  - Clique no botão Create record
  - Record name: digite o valor referente ao seu [YOUR_SUB_DOMAIN]
  - Record type: A - Routes traffic to an IPv4 address and some AWS resources
  - Alias: mantenha desabilitado
  - Value: O [Public_IP] associado à instância EC2 de Proxy
  - Demais campos pode manter os valores default
  - Clique no botão Create records
- Vá no menu Instances no EC2, selecione a instância de Proxy, clique no botão Action, depois clique em Security e clique na opção Modify IAM role
  - Na instrução [Configuração de policies, roles e usuário do IAM](docs-pt-br/04-IAM.md) nós configuramos uma role referente à proxy com Route 53, no meu exemplo chamado OwncastProxyRoute53CertificatePolicy, em IAM role você deve selecionar a role de referência desta criação e depois clicar no botão Update IAM role
- Execute os seguintes comandos no terminal (ainda conectado à instância via SSH):
```
sudo apt install certbot python3-certbot-dns-route53 -y
sudo certbot certonly --dns-route53 -d [YOUR_SUB_DOMAIN].[YOUR_DOMAIN] --agree-tos --non-interactive --email [YOUR_EMAIL_ADDRESS]
sudo mkdir -p /etc/haproxy/certs
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
sudo chmod 600 /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
```
#### Substitua [YOUR_SUB_DOMAIN] e [YOUR_DOMAIN] nos comandos acima, [YOUR_DOMAIN] deve ser o domínio que você é dono, [YOUR_SUB_DOMAIN] você pode escolher como gostaria que este servidor de Proxy fosse reconhecido no DNS, algo como rtmp-server.example.com, substitua também o [YOUR_EMAIL_ADDRESS] pelo seu e-mail
- Com o certificado digital gerado para o sub-domínio e domínio, agora vamos configurar o HAProxy digitando o seguinte comando:
```
sudo nano /etc/haproxy/haproxy.cfg
```
- Vá até o final do arquivo e insira o seguinte conteúdo:
```
# ========== GLOBAL & DEFAULTS ==========
global
    log stdout format raw local0
    tune.ssl.default-dh-param 2048

defaults
    mode    http
    timeout connect 5s
    timeout client  50s
    timeout server  5m

# ========== RTMPS PROXY PARA 1935 ==========
frontend rtmps_front
    bind *:1935 ssl crt /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
    mode tcp
    default_backend rtmp_back

backend rtmp_back
    mode tcp
    option tcp-check
    tcp-check connect port 1935
    server owncast_rtmp [OWNCAST_INSTANCE_PRIVATE_IP]:1935 check

# ========== HTTPS PROXY PARA 8080 ==========
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https

    acl blocked_path path_beg /hls
    http-request deny if blocked_path

    default_backend http_back

backend http_back
    mode http
    server owncast_http [OWNCAST_INSTANCE_PRIVATE_IP]:8080 check
```
#### Lembre de substituir [YOUR_SUB_DOMAIN] e [YOUR_DOMAIN] nos comandos acima, [YOUR_DOMAIN] deve ser o domínio que você é dono, [YOUR_SUB_DOMAIN] você pode escolher como gostaria que este servidor de Proxy fosse reconhecido no DNS, algo como rtmp-server.example.com
#### Também lembre de substituir [OWNCAST_INSTANCE_PRIVATE_IP] pelo IP Privado da sua instância do Owncast
- Para salvar o arquivo de configuração que acabamos de modificar, pressione simultaneamente a tecla [CTRL] e a tecla [O] (lembrando que este exemplo é com um teclado padrão Windows) e depois pressione a tecla [ENTER] para confirmar a gravação do arquivo
- Para sair do editor de texto, pressione simultaneament3e a tecla [CTRL] e a tecla [X] (lembrando que este exemplo é com um teclado padrão Windows)
- Por fim execute os seguintes comandos para aplicar as alterações no serviço do HAProxy:
```
sudo systemctl enable haproxy
sudo systemctl restart haproxy
exit
```
- Podemos fazer um pequeno teste para validar se conseguimos chamar pelo domínio e se o certificado digital deu certo através dos seguintes comandos:
```
openssl s_client -connect [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:1935 -servername [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]
openssl s_client -connect [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:443 -servername [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]
```
- Agora você pode repetir os mesmos testes de acesso ao painel de administração do Owncast e o uso da câmera SJCAM SJ11 feitos na [Configuração das instâncias EC2](docs-pt-br/05-Owncast-EC2-instance-configuration.md)
  - (caso a instância Owncast esteja desligada) Para isso vá em Instances no EC2, selecione a instância EC2 do Owncast, clique no botão Instance state e depois Start instance, aguarde a instância mudar o status para running
  - Para testar o painel administrativo, ao invés de acessar via `[PUBLIC_IP_ASSOCIATED_WITH_INSTANCE]:8080/admin`, acesse via `https://[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/admin`
  - Já para testar a live streaming, no aplicativo SJCAM Zone mude o servidor RMTP que no exemplo estava `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` para `rtmps://[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T`
  - ##### Observação: note que agora o acesso ao site é via https e a live streaming é via rtmps

### Para a Opção A, o detalhe é que o certificado digital expira em 3 meses, então você precisará renová-lo quando vencer ou antes
- Para renovar quando vencer:
  - refaça os passos do NACL, Security Group e atribuição da IAM Role na instância EC2 do Proxy acima descritos
  - acesse a instância via terminal bash
  - se o certificado já venceu, re-execute o seguinte comando:
```
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
```
  - já se o certificado ainda não venceu mas você quer atualizar, execute o comando:
```
sudo certbot renew --force-renewal
```
  - independente do comando executado para geração do certificado novo, após a emissão execute os comandos:
```
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
sudo systemctl restart haproxy
```
  - Lembre de substituir o [YOUR_SUB_DOMAIN] e [YOUR_DOMAIN] pelos seus respectivos sub-domínio e domínio

### Desfaça a atribuição do IAM Role na instância ao final, em Instances no EC2, selecione a instância de Proxy, clique no botão Actions, depois clique em Security e depois em Modify IAM role, em IAM role selecione a opção No IAM Role e depois clique no botão Update IAM role. Na caixa de confirmação digite Detach no campo e depois clique no botão Detach

### Iremos desfazer as alterações de Security Group na instância e NACL ao final desta página de instruções

#### Opção B
- Conectado à instância, digite o seguinte comando para configurarmos o HAProxy: 
```
sudo nano /etc/haproxy/haproxy.cfg
```
- Vá até o final do arquivo e insira o seguinte conteúdo:
```
# ========== GLOBAL & DEFAULTS ==========
global
    log stdout format raw local0
    tune.ssl.default-dh-param 2048

defaults
    mode    http
    timeout connect 5s
    timeout client  50s
    timeout server  5m

# ========== RTMP PROXY PARA 1935 ==========
frontend rtmp_front
    bind *:1935
    mode tcp
    default_backend rtmp_back

backend rtmp_back
    mode tcp
    option tcp-check
    tcp-check connect port 1935
    server owncast_rtmp [OWNCAST_INSTANCE_PRIVATE_IP]:1935 check

# ========== HTTP PROXY PARA 8080 ==========
frontend https_front
    bind *:8080
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https

    acl blocked_path path_beg /hls
    http-request deny if blocked_path

    default_backend http_back

backend http_back
    mode http
    server owncast_http [OWNCAST_INSTANCE_PRIVATE_IP]:8080 check
```
- Para salvar o arquivo de configuração que acabamos de modificar, pressione simultaneamente a tecla [CTRL] e a tecla [O] (lembrando que este exemplo é com um teclado padrão Windows) e depois pressione a tecla [ENTER] para confirmar a gravação do arquivo
- Para sair do editor de texto, pressione simultaneament3e a tecla [CTRL] e a tecla [X] (lembrando que este exemplo é com um teclado padrão Windows)
- Por fim execute os seguintes comandos para aplicar as alterações no serviço do HAProxy:
```
sudo systemctl enable haproxy
sudo systemctl restart haproxy
exit
```
- Agora você pode repetir os mesmos testes de acesso ao painel de administração do Owncast e o uso da câmera SJCAM SJ11 feitos na [Configuração das instâncias EC2](docs-pt-br/05-Owncast-EC2-instance-configuration.md)
  - (caso a instância Owncast esteja desligada) Para isso vá em Instances no EC2, selecione a instância EC2 do Owncast, clique no botão Instance state e depois Start instance, aguarde a instância mudar o status para running
  - Para testar o painel administrativo, acesse via `[PUBLIC_IP_ASSOCIATED_WITH_INSTANCE]:8080/admin` da mesma forma que havia feito anteriormente, a diferença é que entra via Proxy e a comunicação com a instância do Owncast fica na rede privada
  - Já para testar a live streaming, no aplicativo SJCAM Zone também acesse via `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` da mesma forma como feito antes, a diferença também é que entra via Proxy e a comunicação com a instância do Owncast fica na rede privada

### Vamos desfazer algumas coisas:
- Vá em Network ACLs ainda no VPC, selecione o NACL associado à Subnet Pública
  - Vá na aba Inbound rules e clique no botão Edit inbound rules
    - Rule number 103 (este é um exemplo), SSH (porta 22), Source: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 104 (este é um exemplo), Custom TCP (range de porta 1024 - 65535), Source: 0.0.0.0/0  -> Clique no botão Remove
    - Clique no botão Save changes
  - Vá na aba Outbound rules e clique no botão Edit outbound rules
    - Rule number 103 (este é um exemplo), HTTP (porta 80), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 104 (este é um exemplo), DNS (UDP) (porta 53), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Rule number 105 (este é um exemplo), HTTPS (porta 443), Destination: 0.0.0.0/0 -> Clique no botão Remove
    - Clique no botão Save changes
- Vá no menu Instances no EC2, selecione a instância referente ao Proxy, clique no botão Actions, depois clique na opção Security e depois clique em Change security groups
  - Na linha do Security Group de manutenção -> Clique no botão Remove
  - Clique no botão Save

### Não esqueça de desfazer as regras conforme as instruções acima, isso é necessário para assegurar acessos mínimos para evitar riscos de acessos indesejados
### Lembre de desligar as instâncias para não gerar cobranças adicionais

---
[⬅️ Anterior: Configuração das instâncias EC2](05-Owncast-EC2-instance-configuration.md) | [🏠 Índice](../README.md) | [Próximo: Configuração do Route 53 ➡️](07-Route53.md)