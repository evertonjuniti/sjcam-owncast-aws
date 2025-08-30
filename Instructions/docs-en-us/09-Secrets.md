# Creation of Secrets
![Owncast-SecretsManager.drawio.svg](/Images/Owncast-SecretsManager.drawio.svg)

There is a prerequisite for one of the secrets, which involves generating an RSA private and public key pair.

In [Code -> Keygen](Code/Keygen), there is source code written in GO for generating this key pair. Conveniently, I've already generated go_keygen.exe (built from the source code). You just need to run it, and the key pair will be generated in the folder where the executable is called. You don't need to trust the executable; if you prefer, you can build it yourself from the source code. You'll just need the latest version of GO, which can be obtained [from this page](https://go.dev/doc/install).

You may be wondering why I should generate the key pair from source code instead of using a bash command via OpenSSL. The answer is simple: on my machine, I couldn't generate a private key with the header "BEGIN RSA PRIVATE KEY," which, believe me, is required for the solution in this repository to work.

Anyway, I'll leave the commands to be done via openssl, in case your machine gives the final result (it needs to have the BEGIN RSA PRIVATE KEY header, anything different from that won't work).

```
bash
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

- Create two secrets in Secrets Manager in the same Region as your Network structure (where you have your VPC and Subnets)
  - Secret 1 - to store the emails that will be allowed to access the video page
    - Secret type: Other type of secret
    - Key/value pairs
      - Key: 0, Value: Your email address
      - [optional] Key: 1, Value: Another email address of your choice. Add more if desired
    - Encryption key: aws/secretsmanager
    - On the next page, under Secret name, give the secret a name. In the example here, it's called AllowedEmails
    - On the next page, you can keep the default values, since you don't need to rotate these secrets
  - Secret 2 - to store the private key that will be used to generate the video cookies
    - Secret type: Other type of secret
    - Plaintext: Paste the fully generated private RSA key here
    - Encryption key: aws/secretsmanager
    - On the next page, under Secret name, give the secret a name. In the example here, it's called CloudFrontPrivateKey (yes, the name is bad, but it's what I created at the time)
    - On the next page, you can keep the default values, since you don't need to rotate these secrets

### Important note: Take note of the name of both these secrets you just created

We saved the private key in Secrets Manager, now we also need to save the public key. In this case, go to the CloudFront service

- Go to the Public Keys menu and click the Create public key button
  - Name: Give your public key a name (in my example, it was OwncastCookiePublicKey)
  - Description - optional: If desired, describe the public key
  - Key: Paste the fully generated public RSA key here
  - Click the Create public key button

### Important note: Make a note of the ID of the newly created public key

- Go to the Key groups menu and click the Create key group button
  - Name: Give your key group a name (in my example, it was OwncastKeyGroup)
  - Description - optional: If desired, describe the key group
  - Public keys: Select the newly created public key
  - Click the Create key group button

---
[⬅️ Previous: Digital certificate creation](08-Certificate.md) | [🏠 Index](../README.md) | [Next: Cognito configuration ➡️](10-Cognito.md)