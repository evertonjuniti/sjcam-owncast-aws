# Criação das Secrets
![Owncast-SecretsManager.drawio.svg](/Images/Owncast-SecretsManager.drawio.svg)

Há um pré-requisito para uma das secrets, que envolve a geração do par de chaves privada e pública do tipo RSA.

Em [Code -> Keygen](Code/Keygen) há um código-fonte feito em linguagem GO para geração deste par de chaves, convenientemente eu deixei o go_keygen.exe já gerado (feito o build à partir do código-fonte), você só precisa executar e o par será gerado na pasta em que for chamado o executável. Você não precisa confiar no executável, se preferir você mesmo pode fazer o build do código-fonte, você só vai precisar da versão mais recente do GO que pode ser obtido [nesta página](https://go.dev/doc/install).

Você pode estar se perguntando porque gerar o par de chaves através de um código-fonte ao invés de usar um comando bash via openssl, a resposta é simples: na minha máquina eu não consegui gerar uma chave privada cujo cabeçalho ficasse "BEGIN RSA PRIVATE KEY", que acreditem é necessário ter esse cabeçalho para a solução deste repositório funcionar.

De qualquer maneira, vou deixar os comandoss para fazer via openssl, caso em sua máquina dê o resultado final (precisa ter o cabeçalho BEGIN RSA PRIVATE KEY, qualquer coisa diferente disso não funcionará).

```
bash
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

- Crie duas secrets na Secrets Manager na mesma Region da sua estrutura de Redes (onde você tem seu VPC e suas Subnets)
  - Secret 1 - para armazenar os e-mails que terão permissão de acesso à página dos vídeos
    - Secret type: Other type of secret
    - Key/value pairs
      - Key: 0, Value: seu endereço de e-mail
      - [opcional] Key: 1, Value: outro endereço de e-mail que você deseje. Vá adicionando mais caso deseje
    - Encryption key: aws/secretsmanager
    - Na próxima página, em Secret name dê um nome para a secret, no exemplo aqui se chama AllowedEmails
    - Ná próxima página pode manter os valores default, já que não precisa rotacionar essas secrets
  - Secret 2 - para armazenar a chave privada que será utilizada para gerar os cookies dos vídeos
    - Secret type: Other type of secret
    - Plaintext: cole a chave RSA privada gerada integralmente aqui
    - Encryption key: aws/secretsmanager
    - Na próxima página, em Secret name dê um nome para a secret, no exemplo aqui se chama CloudFrontPrivateKey (sim, o nome é ruim, mas é o que eu havia criado na época)
    - Ná próxima página pode manter os valores default, já que não precisa rotacionar essas secrets

### Observações importantes: Tome nota do nome de ambas essas secrets que você acabou de criar

---
[⬅️ Anterior: Criação de certificado digital](08-Certificate.md) | [🏠 Índice](../README.md) | [Próximo: Configuração do Cognito ➡️](10-Cognito.md)