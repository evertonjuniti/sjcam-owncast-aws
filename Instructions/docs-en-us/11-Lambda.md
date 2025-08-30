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
    - In [Code -> AWS_Lambda_Function](Code/AWS_Lambda_Function), you'll find the Lambda function source code inside the src folder (a file called lambda_function.py), a buildspec.yml file that can be used in a build flow with CodePipeline, and a lambda_package.zip file, ready to upload to the AWS console
    - In the AWS console, still in the Code tab, click the Upload from button and then click the .zip file option
    - Click the Upload button and choose the lambda_package.zip file and then click the Save button
    - The lambda_function.py file will be updated, and several folders and files will appear in the Lambda function's code editor explorer in the AWS console
    - Lambda function deployment is usually done automatically
  - Testing here is a bit laborious, but it's possible if you do it with Caution:
    - In the editor's source code, go to the definition of the function called validate_authorization
    - Before the try, place the statement:
      ```
      return None
      ```
    - Then click the Deploy button
    - #### Attention: After you finish testing, remember to remove this code
    - Now go to the Test tab
    - In the Event JSON text field, paste the following content:
      ```
      {
        "requestContext": {
          "http": {
            "method": "GET"
          }
        },
        "rawPath": "/instance"
      }
      ```
    - Then click the Test button
    - If everything went well, you'll see the message Executing function: succeeded with a green background. If you click Details, you'll see the result of the call
    - Everything seems to be working, but you could check the source code to test the other available methods and routes if you prefer. For example, /list-videos only changes the route; the rest of the JSON is the same
    - #### Let's undo the change we made for the test
    - In the editor's source code, go to the definition of the function called validate_authorization
    - Before the try, remove the statement:
      ```
      return None
      ```
    - Then click the Deploy button

---
[⬅️ Previous: Cognito configuration](10-Cognito.md) | [🏠 Index](../README.md) | [Next: CloudFront Configuration ➡️](12-CloudFront.md)