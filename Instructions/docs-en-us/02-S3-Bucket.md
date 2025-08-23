# Creating an S3 Bucket
![Owncast-Bucket.drawio.svg](/Images/Owncast-Bucket.drawio.svg)

- [Optional] Create an S3 bucket in the same region as your network structure (where you have your VPC and subnets) to serve your website (if you have one). This can be used for the HTML page of this repository to access recorded videos
  - Bucket name: Must be a globally unique name, one that reflects the hosting of your static website.
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access
  - Bucket versioning: Disabled
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable
  - Other settings can be left at default
  - After creating the bucket, go to the Properties tab for that bucket
    - Edit the configuration to enable the S3 static website hosting option
      - Hosting type: Host a static website
      - Index document: index.html

- Create an S3 Bucket in the same Region as your Networking structure (where you have your VPC and Subnets) to store the video segments that will be recorded.
  - Bucket name: Must be a globally unique name, one that is meaningful for storing the video segments.
  - Object Ownership: ACLs disabled (recommended)
  - Block public access: Block all public access.
  - Bucket versioning: Disabled.
  - Default encryption: Server-side encryption with Amazon S3 managed keys (SSE-S3)
  - Bucket Key: Enable.
  - Other settings can be left at default.
  - After creating the bucket, go to the Permissions tab for that bucket.
    - Bucket policy: Will be configured later.
    - Cross-origin resource sharing (CORS): Use the template in [Code -> AWS_S3_Bucket -> CORS_policy.txt](Code/AWS_S3_Bucket/CORS_policy.txt)
      - #### Attention: Change [YOUR_DOMAIN] to your domain if you have one. a configured domain, if you want to open the page locally then replace the value of AllowedOrigins to http://localhost

---
[⬅️ Previous: Network configuration](01-Network.md) | [🏠 Index](../README.md) | [Next: Creating EC2 instances ➡️](03-EC2-instance-creation.md)