# Lambda function configuration
![Owncast-Lambda.drawio.svg](/Images/Owncast-Lambda.drawio.svg)

### Important note: I'm assuming that in this optional section, you have your own domain in Route 53. This is important because the Lambda function generates cookies and also performs CORS checks.

- Create a new Lambda function in the same Region as your Network structure (where you have your VPC and subnets)
  - Choose the Author from scratch option
  - Function name: Choose a name for your Lambda function (in my example, it was OwncastPlaylistGenerator; yes, the name is awful)
  - Runtime: Choose the Python option (at the time I created it, it was version 3.13)
  - Architecture: Can be x86_64
  - In the Permissions tab, expand Change default execution role
    - Execution role: Use an existing role
    - Existing role: Use the role you created for Owncast (the one from the Lambda use case) (in my example, the name was OwncastLambdaS3ReadAccessRole)
  - You can leave the other options at their default values. Finally, click the Create function button. - You can ignore the Getting started screen if it appears

- Before we look at the code, go to the Configuration tab
  - In the General configuration menu, click the Edit button
    - Memory: change from 128 to 512
    - Timeout: change from 0 min 3 sec to 0 min 10 sec (i.e., the timeout will be 10 seconds)
    - You can leave the other options as they are; click the Save button
  - In the Environment variables menu, click the Edit button
    - You can click the Add environment variable button 11 times. We will create 11 environment variables. Below is the name of each variable (please do not change it) and the value for each variable
      - ALLOWED_EMAILS_SECRET: [the name you gave to Secret 1]
      - BUCKET_NAME: [the name of your S3 bucket that you created to store the video segments]
      - CF_KEY_PAIR_ID: [the ID of the public key you created in CloudFront]
      - COOKIE_DOMAIN: [your domain name with a period leading, for example: .example.com]
      - EC2_INSTANCE_ID: [the ID of your Owncast instance]
      - EC2_INSTANCE_PROXY_ID: [the ID of your proxy instance]
      - EXPIRES_IN: [time in seconds that you want the cookie to expire, 3600 means 1 hour, for example]
      - FOLDER_PREFIX: hls/0/
      - ORIGIN_DOMAIN: [your domain name with http or https (depending on whether you created a digital certificate), for example: https://example.com]
      - REGION: [the region where your S3 Bucket was created]
      - SECRETS_NAME: [the name you gave to Secret 2]
    - Finally, click the Save button

- Now go to the Code tab
  - You'll see what looks like a code editor; there will be a tab called lambda_function.py
    - In [Code -> AWS_Lambda_Function -> Playlist](Code/AWS_Lambda_Function/Playlist), you'll find the Lambda function source code inside the src folder (a file called lambda_function.py), a buildspec.yml file that can be used in a build flow with CodePipeline, and a lambda_package.zip file, ready to upload to the AWS console
    - In the AWS console, still in the Code tab, click the Upload from button and then click the .zip file option
    - Click the Upload button and choose the lambda_package.zip file and then click the Save button
    - The lambda_function.py file will be updated, and several folders and files will appear in the Lambda function's code editor explorer in the AWS console
    - Lambda function deployment is usually done automatically
  - To test, follow these instructions:
    - Go to the Test tab
    - In the Event JSON text field, paste the following content:
      ```
      {
        "requestContext": {
          "authorizer": {
            "claims": {
              "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
            }
          },
          "http": {
            "method": "GET"
          }
        },
        "rawPath": "/instance"
      }
      ```
    - Then click the Test button
    - If everything went well, you will see the message Executing function: succeeded with a green background, and if you click on Details you will see the result of the call, the result should be something like this:
      ```
      {
        "statusCode": 200,
        "headers": {
          "Access-Control-Allow-Origin": "https://example.com",
          "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
          "Access-Control-Allow-Credentials": "true",
          "Content-Type": "application/json"
        },
        "body": "{\"status\": \"stopped\"}"
      }
      ```
      - The "status" attribute with the value "stopped" in the response body indicates that the call was able to check the status of the EC2 instances
    - Let's test the other endpoints:
      - PUT - /instance/turnon
        - Request:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "PUT"
            }
          },
          "rawPath": "/instance/turnon"
        }
        ```
        - Expected response:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "{\"action\": \"starting\"}"
        }
        ```
        - You can check your instances on the EC2 service, both Owncast and Proxy instances should be powered on now
      - PUT - /instance/turnoff
        - Request:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "PUT"
            }
          },
          "rawPath": "/instance/turnoff"
        }
        ```
        - Expected response:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "{\"action\": \"stopping\"}"
        }
        ```
        - You can check your instances on EC2 service, both Owncast and Proxy instances should be stopping now
      - GET - /auth-cookies
        - Request:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "auth-cookies"
        }
        ```
        - Expected response:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "multiValueHeaders": {
            "Set-Cookie": [
              "CloudFront-Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9ldmVydG9ub2d1cmEuY29tL2hscy8wLyoiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NTY3Mjc2NDd9fX1dfQ__;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None",
              "CloudFront-Signature=Sj~HEy7Ljv5mf3J5x5n85mDXBFtC2cQKKuJj1n3jgbMcXbeNNaB~YUubHsSvvm9frCQCCycQxGkRJJanu0Ym3dV2VQyca7tC46yTElkfh9lhKQMZjkEgXF-ifTusunTZlEPl9DHW2C4x7MEB5QTd6CKjY~jgMH4H3yeBxi-VQcnIeuGv3qNDis-IOID0xhjeXhH7CSe5NP3I2XBI0Fq2-GvLbMfsidKJjkNp7-OyhTO1JsvU2RRGRGo5EUs31EuyYH30nC-CSsDZhWYz8MLQdoYtWXdtyh-x78Fex4eDd~V9-igWLMyBDHXyBSNYj0lESDRVSbzfotTky~OoIb-qyA__;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None",
              "CloudFront-Key-Pair-Id=K3KYD9LB8GV4A3;Path=/;Domain=.example.com;Secure;HttpOnly;SameSite=None"
            ]
          },
          "body": ""
        }
        ```
        - In this route, you are expected to receive Cookies, which will be used to access the video segments via CloudFront, which will be used by the video player
      - GET - /list-videos
        - Request:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "/list-videos"
        }
        ```
        - Expected response:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/json"
          },
          "body": "[{\"videoId\": \"offline\", \"dateTime\": \"2025-09-01 10:37:52 - offline\"}, {\"videoId\": \"KOOuOXuNg\", \"dateTime\": \"2025-08-28 14:51:31 - KOOuOXuNg\"}]"
        }
        ```
        - In this route you are expected to receive a list of videos if you recorded some at the time of configuring the Owncast instance (where we configured it to use the SJCAM SJ11)
      - GET - /playlist/{video-id}
        - Request:
        ```
        {
          "requestContext": {
            "authorizer": {
              "claims": {
                "email": "[EMAIL_REGISTERED_WITHIN_COGNITO]"
              }
            },
            "http": {
              "method": "GET"
            }
          },
          "rawPath": "/playlist/offline.m3u8",
          "pathParameters": {
            "video_id": "offline.m3u8"
          }
        }
        ```
        - Expected response:
        ```
        {
          "statusCode": 200,
          "headers": {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, OPTIONS, PUT",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Credentials": "true",
            "Content-Type": "application/vnd.apple.mpegurl"
          },
          "body": "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:6\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:6.000,\nhttps://example.com/hls/0/stream-offline-0.ts\n#EXT-X-ENDLIST"
        }
        ```
        - In this route you are expected to receive a list of video segments for the video Id you used in the call (in pathParameters)
    - In a way, everything is working, these tests validate that the Lambda function can make the expected calls and that the role has the correct policies for accessing the EC2 instances and the Bucket

### Optional: Lambda function for maintenance

As previously mentioned in [Owncast EC2 instance configuration](05-Owncast-EC2-instance-configuration.md) and [Proxy EC2 instance configuration](06-Proxy-EC2-instance-configuration.md), this option enables automated updates for both the Owncast EC2 instance (in a private subnet) and the Proxy instance (in a public subnet).

In this case, the Lambda function has three different modes:

- owncast-os-update
  - Modifies the route table to allow the private subnet to access the internet
  - Adds inbound and outbound rules to the private subnet's NACL
  - Associates the maintenance Security Group with the EC2 instance running Owncast
  - Associates a maintenance Role with the EC2 instance running Owncast
  - Associates the existing public IP (previously linked to the Proxy EC2 instance) with the EC2 instance running Owncast
  - Starts the EC2 instance running Owncast
  - Accesses the instance via SSM
  - Executes the following commands:
    ```
    sudo apt update -y
    sudo apt upgrade -y
    ```
  - After command execution, exits the instance, stops the instance, and reverts all previously mentioned steps
- proxy-os-update
  - Adds inbound and outbound rules to the public subnet's NACL
  - Associates the maintenance Security Group with the EC2 instance running HAProxy
  - Associates a maintenance Role with the EC2 instance running HAProxy
  - Starts the EC2 instance running HAProxy
  - Accesses the instance via SSM
  - Executes the following commands:
    ```
    sudo apt update -y
    sudo apt upgrade -y
    ```
  - After executing the commands, exits the instance, stops the instance, and reverses all the previously mentioned steps
- proxy-cert-renew (this mode applies only if you have chosen to use DNS with HAProxy alongside a digital certificate)
  - Adds inbound and outbound rules to the public subnet's NACL
  - Associates the maintenance Security Group with the EC2 instance running HAProxy
  - Associates a maintenance Role with the EC2 instance running HAProxy
  - Starts the EC2 instance running HAProxy
  - Accesses the instance via SSM
  - Executes the following commands:
    ```
    sudo certbot renew --force-renewal
    sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_DOMAIN].pem'
    sudo systemctl restart haproxy
    ```
  - After executing the commands, exits the instance, stops the instance, and reverses all the previously mentioned steps

Here is what needs to be done to create this new Lambda function:

- Create a new Lambda function in the same Region as your network infrastructure (where your VPC and subnets are located)
  - Choose the "Author from scratch" option
  - Function name: choose a name for your Lambda function (in my example, I used `OwncastMaintenance`—yes, it's a terrible name)
  - Runtime: choose Python (at the time I created it, version 3.14 was available)
  - Architecture: you can use x86_64
  - Under the Permissions tab, expand "Change default execution role"
    - Execution role: Use an existing role
    - Existing role: use the role you created for maintenance (in my example, the name was `OwncastMaintenanceRole`)
  - Leave the other options at their default values, then click the "Create function" button
  - You can ignore the "Getting started" screen if it appears

- Before looking at the code, go to the Configuration tab
  - In the General configuration menu, click the Edit button
    - Timeout: change from 0 min 3 sec to 15 min 00 sec (i.e., the timeout will be 15 minutes, which is usually the maximum allowed)
    - Leave the other options as they are and click the Save button
  - In the Environment variables menu, click the Edit button
    - Click the **Add environment variable** button 11 times; we will create 11 environment variables. Below are the names for each variable (please do not change them) and what their values ​​should be:
      - ELASTIC_IP_ALLOC_ID: [the Elastic IP allocation ID]
      - INSTANCE_PROFILE_NAME: [the name of the digital certificate update role; in my case, it was OwncastProxyRoute53CertificateRole]
      - INTERNET_GATEWAY_ID: [the VPC Internet Gateway ID]
      - MAINTENANCE_SG_ID: [the Maintenance Security Group ID]
      - OWNCAST_INSTANCE_ID: [your Owncast instance ID]
      - PRIVATE_NACL_ID: [the NACL ID associated with the Private Subnet]
      - PRIVATE_ROUTE_TABLE_ID: [the Route Table ID associated with the Private Subnet]
      - PROXY_DOMAIN: [the Route 53 domain name related to the Owncast streaming address]
      - PROXY_INSTANCE_ID: [your Proxy instance ID]
      - PUBLIC_NACL_ID: [the NACL ID associated with the Public Subnet]
      - REGION: [your infrastructure region ID]
    - Finally, click the Save button

- Now go to the Code tab
  - You will see what looks like a code editor; there, you will find a tab named lambda_function.py
    - In [Code -> AWS_Lambda_Function -> Maintenance](Code/AWS_Lambda_Function/Maintenance), you will find the Lambda function source code inside the src folder (a file named lambda_function.py), a buildspec.yml file that can be used in a CodePipeline build workflow, and a lambda_package.zip file ready for upload to the AWS console
    - In the AWS console, while still on the Code tab, click the Upload from button and then select the .zip file option
    - Click the Upload button, select the lambda_package.zip file, and then click the Save button
    - The lambda_function.py file will be updated, and several folders and files will appear in the code editor's explorer within the AWS console
    - Generally, the Lambda function is deployed automatically
  - To test, follow these instructions:
    - Go to the Test tab.
    - In the Event JSON text field, paste the following content:
      ```
      {
        "mode": "owncast-os-update"
      }
      ```
    - Then, click the Test button.
    - If successful, you will see the message "Executing function: succeeded" with a green background; additionally, if you click Details, you will see the call result (an execution log), and you can also click the CloudWatch Log Group link to view the execution log in detail.
    - Let's test the other execution options:
      ```
      {
        "mode": "proxy-os-update"
      }
      ```
      ```
      {
        "mode": "proxy-cert-renew"
      }
        ```
      - Depending on the frequency of updates, the time the Lambda Function takes to execute the commands may vary; this is why the function's execution timeout is configured for up to 15 minutes.
      - Another important point concerns separating the execution tasks rather than performing everything at once: depending on what needs updating, running everything simultaneously could exceed the 15-minute execution limit, resulting in an error.

My recommendation is to perform these updates at least once a month, in the following order:

1) owncast-os-update
2) proxy-os-update
3) proxy-cert-renew (note that this one depends on whether you chose to use a digital certificate)

Ideally, allow at least 15 minutes between executions to ensure each update completes successfully.

---
[⬅️ Previous: Cognito configuration](10-Cognito.md) | [🏠 Index](../README.md) | [Next: API Gateway Configuration ➡️](12-API-Gateway.md)