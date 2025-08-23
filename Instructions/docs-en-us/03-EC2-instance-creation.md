# Creating EC2 instances
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

- EC2 instance for the Proxy server (using HAProxy)
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.micro
  - Key pair: You can select one you already have; if you don't have one, create a new pair
    - #### if you are going to create one, save the .pem file somewhere on your machine, you will need it to access the instance later
  - Network settings:
    - VPC: Default VPC (following the example in this guide)
    - Subnet: The Public Subnet you created
    - Security Group: Choose the Security Group you created for Proxy use
  - Other settings can remain at the default
  - In the Elastic IP tab, create one and associate it with this instance
- EC2 instance for the Owncast server
  - Application and OS Image: Ubuntu
  - Architecture: 64-bit
  - Instance Type: t3.small
  - Key pair: You can select one you already have (for example, the one you assigned to the Proxy EC2 instance), or create a new pair
    - #### if you are going to create one, save the .pem file somewhere on your machine, you will need it to access the instance later
  - Network settings:
    - VPC: Default VPC (following the example in this guide)
    - Subnet: The Private Subnet you created
    - Security Group: Choose the Security Group you created. You created it for Owncast use
  - You can keep the other settings at the default

### Important Notes: Take note of the Instance ID of both EC2 instances and the Elastic IP address

---
[⬅️ Previous: Creating an S3 Bucket](02-S3-Bucket.md) | [🏠 Index](../README.md) | [Next: Owncast EC2 instance configuration ➡️](04-Owncast-EC2-instance-configuration.md)