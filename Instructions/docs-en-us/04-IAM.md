# Configuring IAM policies, roles, and users
![Owncast-IAM.drawio.svg](/Images/Owncast-IAM.drawio.svg)

- In the Policies menu, create a new Policy, this will be the main policy for Owncast
  - Instead of selecting with the Visual editor, switch to the JSON editor.
  - Use the template file from this repository in [Code -> AWS_IAM -> Owncast_Policy.txt](Code/AWS_IAM/Owncast_Policy.txt)
    - Change the [OwncastSegmentsBucketName] tag to the name of the bucket you created for the video segment files.
    - Change the [YourRegion] tag to the same region as your VPC and Subnet.
    - Change the [YourAccount] tag to your AWS account ID (you can see this in the upper right corner of the AWS Console; use only numbers).
    - Change the [ProxyInstanceId] tag to the ID of the EC2 instance for the Public Subnet Proxy (remember I told you to write this down!)
    - Change the [OwncastInstanceId] tag to the ID of the EC2 instance for the Private Subnet Owncast (Remember, I told you to write this down!)
    - Change the name of the CloudFrontPrivateKey secret if you created it with a different name in Secrets Manager (remember, I told you to write this down!)
    - Change the name of the AllowedEmails secret if you created it with a different name in Secrets Manager (remember, I told you to write this down!)
    - On the next page, give your policy a name (in my case it was OwncastPolicy)

- In the Roles menu, create a new role. This will be the primary role for Owncast, linked to the Owncast Policy.
  - Trusted entity type: AWS Service
  - Use case: Lambda
  - Permission policies: select:
    - AWSLambdaBasicExecutionRole (AWS managed)
    - The name of the Owncast Policy. In this example, it's called OwncastPolicy (Customer managed)
    - Remember to check the boxes for both policies mentioned above
  - Role details:
    - Role name: Give the role a name (in my case, it was OwncastLambdaS3ReadAccessRole)
    - You can leave the other fields at their default values

- [Optional] Create a policy to generate a digital certificate via Let's Encrypt for the Proxy instance
  - This policy is for if you have a domain in Route 53 and want to validate the domain with a digital certificate when calling the Proxy through the domain
  - Instead of selecting with the Visual editor, switch to the JSON editor
  - Use the template file from this repository in [Code -> AWS_IAM -> Route53Certificate_Policy.txt](Code/AWS_IAM/Route53Certificate_Policy.txt)
    - Change the [YourHostedZoneId] tag to the ID of your Hosted Zone in Route 53
    - On the next page, give your policy a name (in my case, it was OwncastProxyRoute53CertificatePolicy)

- [Optional] Create a Role to generate a digital certificate via Let's Encrypt for the Proxy instance using the optional Policy
  - Trusted entity type: AWS Service
  - Use case: EC2 (in the list of options, keep the EC2 option)
  - Permission policies: select:
    - The name of the digital certificate policy. In this example, it's called OwncastProxyRoute53CertificatePolicy (Customer managed)
    - Remember to check the box for the policy mentioned above
  - Role details:
    - Role name: Give the role a name (in my case, it was called OwncastProxyRoute53CertificateRole)
    - You can leave the other fields at their default values

- [Optional] Create a policy to enable automated maintenance for the Proxy and Owncast EC2 instances
  - Use the template file from this repository at [Code -> AWS_IAM -> MaintenanceLambda_Policy.txt](Code/AWS_IAM/MaintenanceLambda_Policy.txt)
    - Replace the `[YourRegion]` tag with the same region where your VPC and Subnet are located
    - Replace the `[YourAccount]` tag with your AWS account ID (you can find this in the top-right corner of the AWS Console; use only the numbers)
    - Replace the `[PublicSubnetNaclId]` tag with the ID of your VPC's Public Subnet
    - Replace the `[PrivateSubnetNaclId]` tag with the ID of your VPC's Private Subnet
    - Replace the `[PrivateRouteTableId]` tag with the ID of the Route Table associated with your VPC's Private Subnet
    - Replace the `[ProxyInstanceId]` tag with the EC2 instance ID for the Public Subnet Proxy (remember, I told you to note this down!)
    - Replace the `[OwncastInstanceId]` tag with the EC2 instance ID for the Private Subnet Owncast instance (remember, I told you to note this down!)
    - Replace the `[SharedIAMRoleName]` tag with the name of the previously created Role (the one for the digital certificate, if you chose to create that role)
    - Replace the `[MaintenanceSGId]` tag with the ID of the Security Group you created for instance maintenance
    - Replace the `[ExistingProxySGId]` tag with the ID of the Security Group you created for the Proxy instance
    - Replace the `[ExistingOwncastSGId]` tag with the ID of the Security Group you created for the Owncast instance
    - Replace the `[MaintenanceLambdaFunctionName]` tag with the name of the maintenance Lambda Function (you can optionally create this in [Lambda Function Configuration](11-Lambda.md))
    - On the next page, name your policy (in my case, I named it OwncastMaintenancePolicy)

- [Optional] Create a Role to perform automated maintenance on the Proxy and Owncast EC2 instances
  - Trusted entity type: AWS Service
  - Use case: EC2 (keep the EC2 option selected from the list)
  - Permission policies: select
    - The maintenance policy name (in this example, it is named OwncastMaintenancePolicy [Customer managed])
    - Make sure the checkbox for the aforementioned policy remains selected
  - Role details:
    - Role name: assign a name to the role (in my case, I used OwncastMaintenanceRole)
    - You can leave the default values ​​for the remaining fields

- In the Users menu, create a new user
  - User name: Give it a name (in my example, it was Owncast)
  - Provide user access to the AWS Management Console - optional: leave unchecked
  - After creating the user, click on the newly created user to view the details
  - In the Security Credentials tab, under Access keys, click the Create access key button
    - Use case: Third-party service (will be used within the Owncast application settings)
    - Confirmation (I understand the above recommendation and want to proceed to create an access key): leave checked
    - The rest is optional
    - Write down the Access key
    - In the Secret access key column, click Show and write down the Secret Key
    - You can optionally download the .csv file with the Access Key and Secret Key information. Save this file if you choose to download it
    - #### Attention: This will be the only opportunity to write down the Secret Key. Do not click the Done button before writing down this information

### Important notes: Take note of the name of the Policies created

---
[⬅️ Previous: Creating EC2 instances](03-EC2-instance-creation.md) | [🏠 Index](../README.md) | [Next: Configuring EC2 instances ➡️](05-Owncast-EC2-instance-configuration.md)