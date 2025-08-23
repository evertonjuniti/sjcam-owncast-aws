# Network configuration
![Owncast-Network.drawio.svg](/Images/Owncast-Network.drawio.svg)

- I chose the sa-east-1 region for my structure, you can choose whatever you prefer
- I'm using my account's default VPC
  - VPC CIDR Block: 172.31.0.0/16
- Create 2 subnets, one representing the public subnet and the other the private subnet
  - Public Subnet CIDR Block: 172.31.101.0/28 (only 8 IPs)
  - Private Subnet CIDR Block: 172.31.100.0/28 (only 8 IPs)
  - Only 8 IPs is intentional, to avoid creating too many EC2 instances
- Create 1 Endpoint, necessary for integration with the S3 bucket without leaving the VPC
  - In the Endpoints menu, I created one of the "AWS Services" type, service "com.amazonaws.sa-east-1.s3" (given my region) of the "Gateway" type linked to my default VPC
- Create a route table for the public subnet
  - Routes:
    - Destination: 0.0.0.0./0 | Target: [Internet Gateway]
    - Destination: 172.31.0.0/16 | Target: local
  - Note: An Internet Gateway must be attached to your VPC
  - Associate this route table with the public subnet you created
- Create a route table for the private subnet
  - Routes:
    - Destination: [S3 Alias] | Target: [S3 VPC Endpoint]
    - Destination: 172.31.0.0/16 | Target: local
  - Note: The S3 Alias can be found in the "Managed prefix lists" menu
  - Associate this route table with the private subnet you created
- Create a NACL (Network Access Control List) for the public subnet
  - Inbound Rules
    - Rule number 100, HTTPS (port 443), Source: 0.0.0.0/0
    - Rule number 101, Custom TCP (port 1935), Source: 0.0.0.0/0
    - Rule number 102, Custom TCP (port range 1024-65535), Source: 172.31.100.0/28
  - Outbound Rules
    - Rule number 100, HTTP* (port 8080), Destination: 172.31.100.0/28
    - Rule number 101, Custom TCP (port 1935), Destination: 172.31.100.0/28
    - Rule number 102, Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
  - Associate this NACL with the created Public Subnet
- Create a NACL (Network Access Control List) for the private subnet
  - Inbound Rules
    - Rule number 100, Custom TCP (port 1935), Source: 172.31.101.0/28
    - Rule number 101, HTTP* (port 8080), Source: 172.31.101.0/28
    - Rule number 102, Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
  - Outbound Rules
    - Rule number 100, Custom TCP (port range 1024-65535), Destination: 172.31.101.0/28
    - Rule number 101, HTTPS (port 443), Destination: 0.0.0.0/0
  - Associate this Route Table with the created Private Subnet
- Create a Security Group (will be used on the Proxy instance)
  - Inbound Rules
    - HTTPS (port 443), Source: 0.0.0.0/0
    - Custom TCP (port 1935), Source: 0.0.0.0/0
  - Outbound Rules
    - Custom TCP (port 1935), Destination: 172.31.100.0/28
    - Custom TCP (port 8080), Destination: 172.31.100.0/28
- Create a Security Group (will be used on the Owncast instance)
  - Inbound Rules
    - Custom TCP (port 1935), Source: 172.31.101.0/28
    - Custom TCP (port 8080), Source: 172.31.101.0/28
  - Outbound Rules
    - HTTPS (port 443), Destination: [S3 Alias]
- Create a Security Group (will be used for instance maintenance)
  - Inbound Rules
    - SSH (port 22), Source: 0.0.0.0/0
    - Custom TCP (port 1935), Source: 0.0.0.0/0
    - Custom TCP (port 8080), Source: 0.0.0.0/0
  - Outbound Rules
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - HTTP (port 80), Destination: 0.0.0.0/0
    - HTTPS (port 443), Destination: 0.0.0.0/0

### Important note: to perform maintenance and software installation on the EC2 instance in the Public and Private Subnet, additional steps will be required. We recommend that you only do these during maintenance, then undo the items described below
- Include the following in the Route Table associated with the Private Subnet:
  - A route Destination: 0.0.0.0/0, Target: Internet Gateway
- Include the following in the NACL associated with the Public and Private Subnet:
  - Inbound Rule
    - SSH (port 22), Source: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
  - Outbound Rule
    - HTTP (port 80), Destination: 0.0.0.0/0
    - DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
- Include the following in the NACL associated with the Public Subnet:
  - Outbound Rule
    - HTTPS (port 443), Destination: 0.0.0.0/0
- Associate it with the EC2 instance in the Public and Private Subnet:
  - The instance maintenance security group
  - An Elastic IP public IP (here is one instance at a time)

These steps above will enable an internet connection for instance security updates and any installations

After completing the installations, undo all of the above items to maintain greater security when accessing the instance in the Private Subnet

---
[🏠 Index](../README.md) | [Next: Creating S3 an Bucket ➡️](02-S3-Bucket.md)