# Digital certificate creation
![Owncast-Certificate_Manager.drawio.svg](/Images/Owncast-Certificate_Manager.drawio.svg)

- [Optional] If you want to use the digital certificate in conjunction with your registered domain,
  - #### Note: You must be in the us-east-1 (N. Virginia) region for use with CloudFront
  - Go to my List certificates in AWS Certificate Manager and click the Request button
  - Certificate type: Request a public certificate
  - Fully qualified domain name: Add your domain and a wildcard for your domain (this will help you later). Here's an example:
    - example.com
    - *.example.com
    - #### Note: To add more than one domain, after adding the first domain, click the Add another name to this certificate button to add additional domains or subdomains
  - Allow export: Disable export
    - #### Caution: Do not click Enable export if you will not export the certificate for use outside of AWS. Selecting this option will incur a cost of $164.00 USD
  - Validation method: DNS validation - recommended
  - Key algorithm: RSA 2048 (but you can select another if you wish)
  - You must wait for AWS to validate the domain name to verify that you are the owner. If you registered the domain with Route 53 and created the Hosted zone, click the Create records in Route 53 button so that AWS Certificate Manager adds the domain and subdomain records for you to your Hosted zone, and then the validation will be successful

---
[⬅️ Previous: Proxy EC2 instance configuration](07-Route53.md) | [🏠 Index](../README.md) | [Next: Creation of Secrets ➡️](09-Secrets.md)