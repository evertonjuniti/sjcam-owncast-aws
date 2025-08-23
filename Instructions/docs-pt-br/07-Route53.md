# Configuração do Route 53
![Owncast-Route_53.drawio.svg](/Images/Owncast-Route_53.drawio.svg)

- [Opcional] Registre um domínio, esse é um requisito opcional caso você queira acessar os recursos por um domínio seu
  - Vá no menu Registered domains no Route 53 e clique no botão Register domains
    - Check availability for a domain: especifique um nome de domínio desejado e clique no botão Search
      - Pode ser que o domínio exato não esteja disponível, mas na lista de Suggested available domains há opções de domínio possíveis para seleção
      - Observe que a depender do domínio o custo anual pode variar
      - Clique em Select na coluna Actions para o domínio selecionado e depois clique no botão Proceed to checkout
    - Observe que você pode optar pela renovação automática ou não
    - Você precisará informar dados cadastrais de registro de contato como pessoa responsável pelo domínio, você pode mudar os demais tipos de contato se quiser ou manter as opções padrão já selecionadas
    - Por fim em Terms and conditions, leia as condições e marque a caixa de seleção e depois clique no botão Submit para comprar o domínio

- [Opcional] Crie uma hosted zone, esse é um requisito opcional caso você queira usar seu domínio para registrar como você roteia tráfego para seu domínio aos serviços que criaremos com este manual
  - Vá no menu Hosted zones no Route 53 e clique no botão Create hosted zone
    - Domain name: indique o nome do domínio que você possui (pode ser o que você comprou caso tenha optado por registrar um domínio)
    - Type: Public hosted zone (para permitir chamadas/tráfego da internet)

---
[⬅️ Anterior: Configuração da instância EC2 de Proxy](06-Proxy-EC2-instance-configuration.md) | [🏠 Índice](../README.md) | [Próximo: Criação de certificado digital ➡️](08-Certificate.md)