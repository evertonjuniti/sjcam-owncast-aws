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
  - Go to the App clients menu for this user pool
    - #### Take note the value in the Client ID column
  - Go to the Users menu for this user pool
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
  - Go to the Sign-up menu
    - At the bottom of the page, under Self-service sign-up, click the Edit button
    - Under Self-registration, Enable self-registration: Leave it unchecked and save the changes

---
[⬅️ Previous: Creation of Secrets](09-Secrets.md) | [🏠 Index](../README.md) | [Next: Configuring EC2 instances ➡️](05-Owncast-EC2-instance-configuration.md)