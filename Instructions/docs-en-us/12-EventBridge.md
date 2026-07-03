# EventBridge Configuration
![Owncast-Lambda.svg](/Images/Owncast-EventBridge.svg)

## Important note: here I am assuming that, in this optional part, you want to both shut down the Owncast and HAProxy EC2 instances and update them using the maintenance Lambda function.

### To automatically shut down the Owncast and HAProxy EC2 instances every day at 00:00 AM:

- Create a new EventBridge Schedule in the same region as your EC2 instances
  - Schedule name: define a name for the schedule; in my example, I used OwncastStopEC2Instances
  - Description: optional
  - Schedule group: you can keep the "default"
  - Schedule patterns: select the "Recurring schedule" option
  - Time zone: choose your preferred time zone (the default for your region may already be selected)
  - Schedule type: choose the option that works best for you; in this example, "Cron-based schedule" was selected
  - Cron expression (suggestion to run every day at 00:00):
    - Minutes: 0
    - Hours: 0
    - Day of the month: *
    - Month: *
    - Day of the week: ? - Year: *
  - Flexible time window: select the "Off" option from the dropdown menu
  - Timeframe: leave the fields blank (default)
  - Click the "Next" button
  - Under Target API, select "All APIs"
    - In the "Find service" search field, type "EC2" and select "Amazon EC2 (502)"
    - In the "Find API" search field, type "Stop" and select "StopInstances"
    - In the section that appears below, add the IDs for both EC2 instances to the list: the one where Owncast is installed and the one where HAProxy is installed
  - Click the "Next" button
  - Schedule state: keep enabled
  - Action after schedule completion: leave blank (do not select any option)
  - Retry policy: keep disabled
    - Dead-letter queue (DLQ): keep "None" selected
  - Customize encryption settings (advanced): leave unchecked
  - Permissions: you are required to select a Role, so only the "Use existing role" option will be available
  - Select an existing role: select the specific Role (in my example, it is named OwncastStopEC2InstanceRole)
  - Click the "Next" button
  - Review the settings and click the "Create schedule" button

### To automatically update the Owncast and HAProxy EC2 instances:

#### Cron schedule to update the Owncast EC2 instance, running on the first day of the month at 01:00 AM:

- Create a new EventBridge Schedule in the same region as your EC2 instances
  - Schedule name: set a name for the schedule; in my example, I used Owncast_OS_Update
  - Description: optional
  - Schedule group: you can keep the "default"
  - Schedule patterns: select the "Recurring schedule" option
  - Time zone: choose your preferred time zone (the default for your region may already be selected)
  - Schedule type: choose the option that works best for you; in this example, "Cron-based schedule" was selected
  - Cron expression (suggestion to run on the first day of every month at 01:00):
    - Minutes: 0
    - Hours: 1
    - Day of the month: 1
    - Month: *
    - Day of the week: ? - Year: *
  - Flexible time window: select the "Off" option from the dropdown menu
  - Timeframe: leave the fields blank (default)
  - Click the "Next" button
  - Under Target API, select the "Templated targets" option
  - Select the "AWS Lambda" option
  - Lambda function: select the maintenance Lambda function; in my case, it is named "OwncastMaintenance"
  - Payload: enter the following value -> {"mode":"owncast-os-update"}
  - Click the "Next" button
  - Schedule state: keep it enabled ("Enable")
  - Action after schedule completion: leave blank (do not select any option)
  - Retry policy: keep it disabled
    - Dead-letter queue (DLQ): keep "None" selected
  - Customize encryption settings (advanced): leave unchecked
  - Permissions: you can create a new role configured for this type of execution, or select "Use existing role" if you already have one
  - Select an existing role: select the specific role; in my example, it is named Amazon_EventBridge_Scheduler_LAMBDA (I created it for the first schedule and reused it for the others)
  - Click the "Next" button
  - Review the settings and click the "Create schedule" button

#### Cron schedule to update the HAProxy EC2 instance, running on the first day of the month at 01:30 AM:

- Create a new EventBridge Schedule in the same region as your EC2 instances
  - Schedule name: define a name for the schedule (in my example, I used Proxy_OS_Update)
  - Description: optional
  - Schedule group: you can keep the "default"
  - Schedule patterns: select the "Recurring schedule" option
  - Time zone: choose your preferred time zone (the default for your region may already be selected)
  - Schedule type: choose the option that works best for you; in this example, "Cron-based schedule" was selected
  - Cron expression (suggestion to run on the first day of every month at 01:30):
    - Minutes: 30
    - Hours: 1
    - Day of the month: 1
    - Month: *
    - Day of the week: ? - Year: *
  - Flexible time window: select the "Off" option from the combo box
  - Timeframe: leave the fields blank (this is the default)
  - Click the "Next" button
  - Under Target API, select the "Templated targets" option
  - Select the "AWS Lambda" option
  - Lambda function: select the maintenance Lambda function; in my case, it is named "OwncastMaintenance"
  - Payload: enter the following value -> {"mode":"proxy-os-update"}
  - Click the "Next" button
  - Schedule state: keep it enabled ("Enable")
  - Action after schedule completion: leave blank (do not select any option)
  - Retry policy: keep it disabled
    - Dead-letter queue (DLQ): keep the "None" option selected
  - Customize encryption settings (advanced): do not check this option
  - Permissions: you can create a new Role prepared for this type of execution, or select the "Use existing role" option if you already have one
  - Select an existing role: select the specific Role; in my example, it is named Amazon_EventBridge_Scheduler_LAMBDA (I created it for the first schedule and reused it for the others)
  - Click the "Next" button
  - Review the settings and click the "Create schedule" button

#### Cron schedule to update the digital certificate for the HAProxy EC2 instance, running on the first day of the month at 02:00 AM:

- Create a new EventBridge Schedule in the same region as your EC2 instances
  - Schedule name: define a name for the schedule; in my example, I used Proxy_Cert_Renew
  - Description: optional
  - Schedule group: you can keep the "default"
  - Schedule patterns: select the "Recurring schedule" option
  - Time zone: choose your preferred time zone (the default for your region may already be selected)
  - Schedule type: choose the option that works best for you; in this example, "Cron-based schedule" was selected
  - Cron expression (suggestion to run on the first day of every month at 02:00):
    - Minutes: 00
    - Hours: 2
    - Day of the month: 1
    - Month: *
    - Day of the week: ? - Year: *
  - Flexible time window: select the "Off" option from the dropdown menu
  - Timeframe: leave the fields blank (default)
  - Click the "Next" button
  - Under Target API, select "Templated targets"
  - Select "AWS Lambda"
  - Lambda function: select the maintenance Lambda function; in my case, it is named "OwncastMaintenance"
  - Payload: enter the following value -> {"mode":"proxy-cert-renew"}
  - Click the "Next" button
  - Schedule state: keep enabled
  - Action after schedule completion: leave blank (do not select any option)
  - Retry policy: keep disabled
    - Dead-letter queue (DLQ): keep "None" selected
  - Customize encryption settings (advanced): leave unchecked
  - Permissions: you can create a new role configured for this type of execution, or select "Use existing role" if you already have one
  - Select an existing role: select the specific role; in my example, it is named Amazon_EventBridge_Scheduler_LAMBDA (I created it for the first schedule and reused it for the others)
  - Click the "Next" button
  - Review the settings and click the "Create schedule" button

---
[⬅️ Previous: Lambda Function configuration](11-Lambda.md) | [🏠 Index](../README.md) | [Next: API Gateway Configuration ➡️](13-API-Gateway.md)