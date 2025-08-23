# Configuring EC2 instances
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

In this step we will configure the EC2 instance related to Owncast for installing and configuring Owncast and the EC2 instance related to the Proxy for installing and configuring HAProxy

### Note: We'll be making adjustments to the Route Table, NACL, and Security Group (all via VPC service) just to enable testing. I'll explain what to do and how to undo them at the end

- [Undo later] Go to Route tables in the VPC, select the Route table for the Private Subnet
  - In the Routes tab, click the Edit routes button
  - Click the Add route button
  - In the Destination column, select the 0.0.0.0/0 option
  - In the Target column, select the Internet Gateway option
  - In the field below, click to select the specific Internet Gateway that exists for your VPC and then click the Save changes button
  - #### This route configuration is required for internet connectivity from the Private Subnet
- [Undo later] Go to Network ACLs still in the VPC, select the NACL associated with the Private Subnet
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button
    - Click the Add New Rule button
    - Rule number 103 (this is an example, it must be one number after the last rule you already had), Custom TCP (port 1935), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 104 (this is an example, it must be one number after the last rule you already had), Custom TCP (port 8080), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 105 (this is an example, it must be one number after the last rule you already had), SSH (port 22), Source: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 106 (this is an example, it must be one number after the last rule you already had). one number after the last rule you already had), Custom TCP (port range 1024-65535), Source: 0.0.0.0/0
    - Click the Save changes button
  - Go to the Outbound Rules tab and click the Edit Outbound Rules button
    - Click the Add New Rule button
    - Rule number 102 (this is an example, it must be one number after the last rule you already had), HTTP (port 80), Destination: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 103 (this is an example, it must be one number after the last rule you already had), DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Click the Add New Rule button
    - Rule number 104 (this is an example, it must be one number after the last rule you already had), Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0
    - Click the Save Changes button
    - #### This subnet-level firewall configuration is required to allow internet connectivity from the Private Subnet, RTMP input, and the Web Server, internet output
- Go to the Instances menu in EC2, select the Owncast instance, click the Actions button, then click the Security option, and then click Change security groups
  - Click the search bar. The Maintenance Security Group will appear. Click the Security Group and then click the Add security group button
  - Click the Save button
- Still in Instances in EC2, select the Owncast instance, click the Instance state button, and then click Start instance
- [Undo later] Go to the Elastic IPs menu in EC2, select the existing Elastic IP, click the Actions button, and then click Associate Elastic IP address
  - Resource type: Keep Instance
  - Instance: Select the Owncast instance (it will be in running status)
  - Private IP address: Click the field that will display the Owncast instance's private IP, click the private IP
  - Reassociation: Allow this Elastic IP address to be reassociated. Keep it checked
  - Click the Associate button
- Go to the Instances menu in EC2 and select the Proxy instance
  - Click the Actions button, then click Security, and then click Change security groups
  - Under Associated security groups, click the search bar and click the Security Group for maintenance that was created in previous steps
  - Then click the Add security group button and click the Save button
  - Click the Instance state button and then click Start instance. Wait for the Instance state column to change from Stopped to Running

Now let's finally install Owncast and configure it:

- Prerequisite: have a terminal for using bash commands, which can be [Git](https://git-scm.com/downloads)
- Open a bash terminal in the same folder where you have the .pem file, the one you eventually created and linked to the instance as a "Key pair."
- Run the following command to access the EC2 instance:
```
ssh -i "[Name_of_your_pem_file].pem" ubuntu@[Public_IP_you_associated_with_Elastic_IP]
```
### Since Ubuntu was the operating system you chose when creating the instance, you will connect with the ubuntu user; this user is the superuser
- If a question appears asking if you want to continue the connection, type yes and then press Enter
- First, let's update the operating system itself with the following commands (run one at a time):
```
sudo apt update -y
sudo apt upgrade -y
```
- For Owncast to process the video segments, we need to install ffmpeg. We'll also install unzip since Owncast is a zip file that we'll download:
```
sudo apt install ffmpeg unzip -y
```
- Now let's download Owncast and unzip the zip file (run one at a time):
```
sudo wget https://github.com/owncast/owncast/releases/download/v0.2.3/owncast-0.2.3-linux-64bit.zip
sudo unzip owncast-0.2.3-linux-64bit.zip
```
### The link above refers to the latest version of Owncast as of the date this walkthrough was written, but you can check the latest version [at this link](https://owncast.online/releases/), just change the link above to the desired version
- If everything went well, you will see a binary file called owncast in the folder using the ls command
- Now let's create a .service file so that the application opens as a service in Ubuntu, so that if the instance is restarted, it "turns on" automatically:
```
cat <<EOT | sudo tee /etc/systemd/system/owncast.service > /dev/null
[Unit]
Description=Owncast Streaming Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/ubuntu
ExecStart=/home/ubuntu/owncast
Restart=on-failure
User=ubuntu

[Install]
WantedBy=multi-user.target
EOT
```
- Finally, use the following commands to register and start the application as a service:
```
sudo systemctl daemon-reload
sudo systemctl enable owncast
sudo systemctl start owncast
```
- If everything went well, Owncast will already be running and active. You can check this with the following command:
```
systemctl status owncast
```
- You can exit the instance with the "exit" command
- Now open your preferred web browser and type the following: `[Public_IP_associated_with_instance]:8080`
  - If it says the site is not secure, it's because we're using a direct IP address without HTTPS and without a digital certificate. This is normal at this point, so you can continue
    - If successful, you should see a page
    ![Owncast_01.png](/Images/Owncast_01.png)
  - Now let's access the administration panel. In the browser, add /admin, making it look like this: `[Public_IP_associated_with_instance]:8080/admin`
    - Username: admin
    - Password (current, temporary): abc123
    - If successful, you should see a page
    ![Owncast_02.png](/Images/Owncast_02.png)
    - The first thing to do in the administration panel is to change the password. Go to the Configuration -> Server Setup menu
      - On the Server Config tab, in the Admin Password field, enter a new password (there is a minimum character validation for the password) and Then click the Update button
      ![Owncast_03.png](/Images/Owncast_03.png)
      - When you update your password, you will be logged out and will need to log in again with the "admin" username using the new password
    - The second thing to do is replace the live streaming key. This is also done on the Server Setup page
      - Go to the Stream Keys tab and click the "+" button
      ![Owncast_04.png](/Images/Owncast_04.png)
      - Make a note of the generated key. You can also edit the Comment field to describe your new key. Then, click the Add button. In the image, I'm using my own key as an example. Don't use the key from the image, as I'll be deleting it
      ![Owncast_05.png](/Images/Owncast_05.png)
      - Now you'll have two keys. Delete the Default stream key by clicking the Trash button to the right of the key
      ![Owncast_06.png](/Images/Owncast_06.png)
      - You'll only have the key you just created
      ![Owncast_07.png](/Images/Owncast_07.png)
    - Finally, let's configure the integration with the S3 Bucket. This is also done on the Server Setup page
      - Go to the S3 Object Storage tab
      ![Owncast_08.png](/Images/Owncast_08.png)
      - Change the Use S3 Storage Provider field from OFF to ON
      - Endpoint: `https://s3.[region_of_your_bucket].amazonaws.com`
      - Access key: [access_key_linked_to_the_iam_user_you_created]
      - Secret key: [secret_key_linked_to_the_iam_user_you_created]
      - Bucket: [the_name_of_the_bucket_you_created]
      - Region: [region_of_your_bucket]
      - In Optional Settings:
        - ACL: private
      - You can see an example:
      ![Owncast_09.png](/Images/Owncast_09.png)
      - Click the Save button

Now let's go to your smartphone to configure it just to test whether we can connect the device to the server and whether the video segment files are now persisted in the S3 bucket

- On your smartphone, download the SJCAM Zone app from SJCAM LLC
![Owncast_10.png](/Images/Owncast_10.png)
- In the app menu, there's an icon that symbolizes Live Stream (in my case, it's on Android, so it's at the bottom of the app, third icon from left to right). Note that there's an option to connect to YouTube, but we won't use this option. Just below is Customize; tap this option
![Owncast_11.png](/Images/Owncast_11.png)
- Enter the following in the text field: `rtmp://[public_IP_of_the_EC2_instance]:1935/live/[Stream_Key_you_noted_from_the_Owncast_configuration]`
  - Example: `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T`
  ![Owncast_12.png](/Images/Owncast_12.png)
  - Tap the Confirm button
- Tap the Next Step button
![Owncast_13.png](/Images/Owncast_13.png)
- In my app, I already have the networks configured, but if you need to add them (the first time you use them, for example), tap the + Add network button
![Owncast_14.png](/Images/Owncast_14.png)
  - You can either choose one of the Wi-Fi networks that the app automatically detects, or you can enter the network name
  - Enter the network name. Enter the network password (if applicable) and then tap the Save and Use button
  ![Owncast_15.png](/Images/Owncast_15.png)
  - In my case, I have both my home Wi-Fi network and my cell phone's
    - #### To use your cell phone as a Wi-Fi hotspot (necessary if you want to live stream outside the home), you must remember to activate your cell phone as a Wi-Fi router
- Once you've selected the network you'll use, tap the Next button
- On the confirmation screen, tap the Confirm button
![Owncast_16.png](/Images/Owncast_16.png)
- You can choose a cover image and description for your Live Stream, but in this case, it's not necessary. Tap the Start Live button
![Owncast_17.png](/Images/Owncast_17.png)
- If everything went well, a QR Code will appear that you can scan with your SJCAM SJ11 camera
![Owncast_18.png](/Images/Owncast_18.png)

Now let's start the live broadcast. On your SJCAM SJ11 camera, turn it on and swipe up to display the camera options
![Owncast_19.png](/Images/Owncast_19.png)

- When the options appear, swipe up again to display the Live button
![Owncast_20.png](/Images/Owncast_20.png)
- Tap the Live broadcast button
![Owncast_21.png](/Images/Owncast_21.png)
- Point the SJCAM SJ11 camera at the QR Code on your smartphone generated in the SJCAM Zone app
![Owncast_22.png](/Images/Owncast_22.png)
- Wait for the SJCAM SJ11 camera to connect to the Owncast server (your newly configured EC2 instance)
![Owncast_23.png](/Images/Owncast_23.png)
- When the status at the top of the camera changes, you're already live (in my case, it's in Brazilian Portuguese, so it says "Transmissão ao vivo", it means "Live streaming")
![Owncast_24.png](/Images/Owncast_24.png)
- You can check for any issues in the Owncast Administration panel. In the Utilities menu, click on the Logs item. You should see something similar to the example:
![Owncast_25.png](/Images/Owncast_25.png)
- And in the S3 service in your bucket, you'll see that the "hls" folder has been created, and within it, the "0" folder has also been created. The video segments will be persisted in this structure
![Owncast_26.png](/Images/Owncast_26.png)
- To end the live stream, on your SJCAM SJ11 camera, if the screen has gone dark, just tap it and then tap the "x" in the upper left corner
- When you end the live streaming, the "Offline" video segment becomes available
![Owncast_27.png](/Images/Owncast_27.png)
- And in the smartphone app, if you're no longer live streaming, tap the "stop live streaming" button
- If you want, you can start another live stream without stopping this one; just point the SJCAM SJ11 camera at the app's QR Code again

That's it! Now we know the Owncast EC2 instance is working perfectly!

### Let's undo a few things:
- Go to Network ACLs in the VPC, select the NACL associated with the Private Subnet
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button
    - Rule number 103 (this is an example), Custom TCP (port 1935), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example), Custom TCP (port 8080), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 105 (this is an example), SSH (port 22), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 106 (this is an example), Custom TCP (port range 1024-65535), Source: 0.0.0.0/0 -> Click the Remove button
    - Click the Save changes button
  - Go to the Outbound Rules tab and click the Edit Outbound Rules button
    - Rule number 102 (this is an example), HTTP (port 80), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 103 (this is an example), DNS (UDP) (port 53), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example), Custom TCP (port range 1024-65535), Destination: 0.0.0.0/0 -> Click the Remove button
    - Click the Save Changes button
- Go to Route Tables in the VPC and select the Route Table for the Private Subnet
  - In the Routes tab, click the Edit Routes button
  - Click the Add Route button
  - In the row whose Target is Internet Gateway -> Click the Remove button
  - In the field below, click to select the specific Internet Gateway that exists for your VPC and then click the Save Changes button

### Don't forget to undo the rules as per the instructions above, this is necessary to ensure minimum access to avoid the risk of unwanted access

---
[⬅️ Previous: Configuring IAM policies, roles, and users](04-IAM.md) | [🏠 Index](../README.md) | [Next: Proxy EC2 instance configuration ➡️](06-Proxy-EC2-instance-configuration.md)