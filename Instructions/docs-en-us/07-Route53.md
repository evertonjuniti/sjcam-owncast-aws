# Route 53 configuration
![Owncast-Route_53.drawio.svg](/Images/Owncast-Route_53.drawio.svg)

- [Optional] Register a domain. This is an optional requirement if you want to access resources through your own domain
  - Go to the Registered domains menu in Route 53 and click the Register domains button
    - Check availability for a domain: specify a desired domain name and click the Search button
      - The exact domain may not be available, but the Suggested available domains list contains possible domain options for selection
      - Note that the annual cost may vary depending on the domain
      - Click Select in the Actions column for the selected domain and then click the Proceed to checkout button
  - Note that you can choose automatic renewal or not
  - You will need to provide contact information as the person responsible for the domain. You can change the other contact types if you wish or keep the default options already selected
  - Finally, in the Terms and Conditions section, read the terms and conditions, select the checkbox, and then click the Submit button to purchase the domain

- [Optional] Create a hosted zone. This is an optional requirement if you want to use your domain to register how you route traffic for your domain to the services we'll create in this guide
  - Go to the Hosted Zones menu in Route 53 and click the Create Hosted Zone button
    - Domain Name: Enter the name of your domain (this can be the one you purchased if you chose to register a domain)
    - Type: Public hosted zone (to allow calls/internet traffic)

---
[⬅️ Previous: Route 53 configuration](06-Proxy-EC2-instance-configuration.md) | [🏠 Index](../README.md) | [Next: Digital certificate creation ➡️](08-Certificate.md)