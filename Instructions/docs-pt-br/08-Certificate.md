# Criação de certificado digital
![Owncast-Certificate_Manager.svg](/Images/Owncast-Certificate_Manager.svg)

- [Opcional] Caso queira usar o certificado digital em conjunto com o seu domínio de registro
  - #### Atenção: aqui você precisa estar na region us-east-1 (N. Virginia) para uso com o CloudFront
  - Vá no meu List certificates no AWS Certificate Manager e clique no botão Request
  - Certificate type: Request a public certificate
  - Fully qualified domain name: Adicione o seu domínio e também um wildcard do seu domínio (isso vai te ajudar depois), vou indicar um exemplo:
    - example.com
    - *.example.com
    - #### Observação: para adicionar mais de um domínio, após adicionar o primeiro domínio, clique no botão Add another name to this certificate para adionar demais domínios ou sub-domínios
  - Allow export: Disable export
    - #### Cuidado: não clique em Enable export se você não vai exportar o certificado para usar fora da AWS, se você selecionar essa opção vai te gerar um custo de $ 164.00 USD
  - Validation method: DNS validation - recommended
  - Key algorithm: RSA 2048 (mas pode selecionar outro se quiser)
  - É necessário aguardar a AWS fazer a validação do nome de domínio para verificar se você é o dono, se você registrou o domínio no Route 53 e se você criou a Hosted zone, clique no botão Create records in Route 53 para que o AWS Certificate Manager adicione os registros de domínios e sub-domínios para você na sua Hosted zone e aí a validação ocorrerá com sucesso

---
[⬅️ Anterior: Configuração do Route 53](07-Route53.md) | [🏠 Índice](../README.md) | [Próximo: Criação das Secrets ➡️](09-Secrets.md)