# Cognito configuration
![Owncast-Cognito.drawio.svg](/Images/Owncast-Cognito.drawio.svg)

- In Cognito, in the region you chose (the same as the VPC and Subnets), go to the User Pools menu and create a new user pool
  - Application type: Single-page application (SPA)
  - Name your application: Give your application a name (in my example, it was Owncast SPA app)
  - Options for sign-in identifiers: Email and Username
  - Required attributes for sign-up: Email (there won't be a sign-up option, but this field is required)
  - Leave the remaining fields default and create the user directory
  - Scroll to the bottom of the page and click the Go to Overview button
    - #### Under User pool information, take note the User pool ID
  - Go to the App clients (under Applications) menu for this user pool
    - #### Take note the value in the Client ID column
  - Go to the Users (under User Management) menu for this user pool
    - Click the Create user button
    - Alias attributes used to sign in: Leave the Email option checked
    - Invitation message: Don't send an invitation
    - User name: Choose a username
    - Email address: Include your email address
    - Mark email address as verified: Leave checked
    - Phone number - optional: Optional; you can leave it blank if you wish
    - Mark phone number as verified: Also optional
    - Temporary password: Set a password
    - Password: Choose a temporary password. You will need to log in a first time to change the password, but this will be displayed in the video access page
    - #### Repeat this user creation process for all users you wish to include
  - Go to the Sign-up (under Authentication) menu
    - At the bottom of the page, under Self-service sign-up, click the Edit button
    - Under Self-registration, Enable self-registration: Leave it unchecked and save the changes
  - Go to the Managed login menu (under Branding)
    - Click the Create a style button
      - In Choose an app client, select the App client generated at the beginning and then click the Create button
      - #### This step is essential for you to be able to open the Cognito login page, otherwise you will get an error
  - In the App clients menu (under Application), click on the App client you created earlier
    - Click the View login page button
      - If the Cognito login page appears asking for the username (or email), then everything went well
      - Take the opportunity to try logging in with the users you created and reset the password for all users

---
[⬅️ Previous: Creation of Secrets](09-Secrets.md) | [🏠 Index](../README.md) | [Next: Lambda function Configuration ➡️](11-Lambda.md)