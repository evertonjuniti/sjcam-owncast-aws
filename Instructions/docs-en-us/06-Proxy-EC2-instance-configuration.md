# Proxy EC2 instance configuration
![Owncast-Instances.drawio.svg](/Images/Owncast-Instances.drawio.svg)

In this step, we will configure the EC2 instance for the proxy to install and configure HAProxy

### Attention: We will be making adjustments to the NACL only for testing purposes. I will indicate what to do and how to undo them at the end

- [Undo later] Go to Network ACLs in the VPC and select the NACL associated with the Public Subnet
  - Go to the Inbound Rules tab and click the Edit Inbound Rules button.
    - Click the Add New Rule button
      - Rule number 103 (this is an example; it must be one number after the last rule you already had), SSH (port 22), Source: 0.0.0.0/0
    - Click the Add New Rule button
      - Rule number 104 (this is an example; it must be one number after the last rule you already had), Custom TCP (port range 1024 - 65535), Source: 0.0.0.0/0
    - Click the Save Changes button
  - Go to the Outbound Rules tab and click the Edit Outbound Rules button.
    - Click the Add New Rule button
      - Rule number 103 (this is an example, it must be one number after the last rule you already had), HTTP (port 80), Destination: 0.0.0.0/0
    - Click the Add New Rule button
      - Rule number 104 (this is an example, it must be one number after the last rule you already had), DNS (UDP) (port 53), Destination: 0.0.0.0/0
    - Click the Add New Rule button
      - Rule number 105 (this is an example, it must be one number after the last rule you already had), HTTPS (port 443), Destination: 0.0.0.0/0
    - Click the Save Changes button
  - #### This subnet-level firewall configuration is required to enable internet connectivity from the Private Subnet, RTMP inbound and outbound to the Web Server, and internet outbound
- Go to the Instances menu in EC2, select the instance for the Proxy, click the Actions button, then click the Security option, and then click Change security groups
  - Click the search bar. The Maintenance Security Group will appear. Click the Security Group and then click the Add security group button
  - Click the Save button.
- Still in Instances in EC2, select the instance for the Proxy, click the Instance state button, and then click Start instance

Below, we'll configure the Public IP for the Proxy EC2 instance. This configuration can remain (it shouldn't be undone)

- Go to the Elastic IPs menu in EC2, select the existing Elastic IP, click the Actions button, and then click Associate Elastic IP address
  - Resource type: Keep Instance
  - Instance: Select the Proxy instance (it will be running)
  - Private IP address: Click the field that displays the private IP of the Proxy instance, then click the private IP
  - Reassociation: Allow this Elastic IP address to be reassociated - keep checked
  - Click the Associate button

Now let's finally install HAProxy and configure it:

- Prerequisite: have a terminal for using bash commands (the same one used when we configured the Owncast EC2 instance), which can be [Git](https://git-scm.com/downloads)
- Open a bash terminal in the same folder where you have the .pem file, the one you eventually created and linked to the instance as a "Key pair."
- Run the following command to access the EC2 instance:
```
ssh -o HostKeyAlias=Proxy -i "[Name_of_your_pem_file].pem" ubuntu@[Public_IP_you_associated_with_Elastic_IP]
```
### Since Ubuntu was the operating system you chose when creating the instance, you'll connect using the ubuntu user; this user is the superuser
- If you're asked whether you want to continue connecting, type yes and then press Enter
- First, let's update the operating system itself with the following commands (run one at a time):
```
sudo apt update -y
sudo apt upgrade -y
```
- To install HAProxy, run the following command:
```
sudo apt install haproxy -y
```
### Now we have two configuration options: Option A (recommended) with use of a domain and digital certificate; Option B without use of a domain and without a digital certificate

#### Option A
- If you already have a domain and hosted zone configured in Route 53, proceed. Otherwise, go to [Route 53 Configuration](docs-en-us/07-Route53.md) and follow the instructions, then return here
- Now we need to add [YOUR_SUB_DOMAIN] (you'll need to choose a name) as a Record in Route 53. This way, we can configure the DNS so that we can call [YOUR_SUB_DOMAIN].[YOUR_DOMAIN] instead of [Public_IP]:
  - Go to Hosted zones in Route 53 and click on your hosted zone
  - Click the Create record button
  - Record name: Enter the value corresponding to your [YOUR_SUB_DOMAIN]
  - Record type: A - Routes traffic to an IPv4 address and some AWS resources
  - Alias: Keep disabled
  - Value: [Public_IP] associated with the EC2 Proxy instance
  - Other fields can keep their default values
  - Click the Create records button
- Go to the Instances menu in EC2, select the Proxy instance, click the Action button, then click Security and click the Modify IAM role option
  - In the [Configuring IAM policies, roles, and users](docs-en-us/04-IAM.md) instruction, we configured a role for the proxy with Route 53. In my example, it was called OwncastProxyRoute53CertificatePolicy. In IAM role, you must select the reference role for this creation and then click the Update IAM role button
- Run the following commands in the terminal (still connected to the instance via SSH):
```
sudo apt install certbot python3-certbot-dns-route53 -y
sudo certbot certonly --dns-route53 -d [YOUR_SUB_DOMAIN].[YOUR_DOMAIN] --agree-tos --non-interactive --email [YOUR_EMAIL_ADDRESS]
sudo mkdir -p /etc/haproxy/certs
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
sudo chmod 600 /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
```
#### Replace [YOUR_SUB_DOMAIN] and [YOUR_DOMAIN] in the commands above. [YOUR_DOMAIN] should be the domain you own. [YOUR_SUB_DOMAIN] allows you to choose how you would like this proxy server to be recognized in DNS, something like rtmp-server.example.com. Also, replace [YOUR_EMAIL_ADDRESS] with your email address
- With the digital certificate generated for the subdomain and domain, let's now configure HAProxy by typing the following command:
```
sudo nano /etc/haproxy/haproxy.cfg
```
- Scroll to the end of the file and insert the following content:
```
# ========== GLOBAL & DEFAULTS ==========
global
log stdout format raw local0
tune.ssl.default-dh-param 2048

defaults
    http mode
    timeout connect 5s
    client timeout 50s
    server timeout 5m

# ========== RTMPS PROXY FOR 1935 ==========
frontend rtmps_front
    bind *:1935 ssl crt /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
    tcp mode
    default_backend rtmp_back

rtmp_back backend
    tcp mode
    option tcp-check
    tcp-check connect port 1935
    server owncast_rtmp [Owncast_Instance_Private_IP]:1935 check

# ========== HTTPS PROXY FOR 8080 ==========
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem
    http mode
    option forwardfor
    http-request set-header X-Forwarded-Proto https

    acl blocked_path path_beg /hls
    http-request deny if blocked_path

    default_backend http_back

backend http_back
    http mode
    server owncast_http [Owncast_Instance_Private_IP]:8080 check
```
#### Remember to replace [YOUR_SUB_DOMAIN] and [YOUR_DOMAIN] in the commands above. [YOUR_DOMAIN] should be the domain you own. [YOUR_SUB_DOMAIN] allows you to choose how you would like this proxy server to be recognized in DNS, something like rtmp-server.example.com
#### Also remember to replace [Owncast_Instance_Private_IP] with the Private IP of your Owncast instance
- To save the configuration file we just modified, press the [CTRL] and [O] keys simultaneously (remembering that this example is with a standard Windows keyboard), and then press the [ENTER] key to confirm saving the file
- To exit the text editor, press the [CTRL] and [X] keys simultaneously (remembering that this example is with a standard Windows keyboard)
- Finally, run the following commands to apply the changes to the service. HAProxy:
```
sudo systemctl enable haproxy
sudo systemctl restart haproxy
exit
```
- We can run a small test to validate whether we can call the domain and whether the digital certificate worked using the following commands:
```
openssl s_client -connect [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:1935 -servername [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]
openssl s_client -connect [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:443 -servername [YOUR_SUB_DOMAIN].[YOUR_DOMAIN]
```
- Now you can repeat the same tests for accessing the Owncast administration panel and using the SJCAM SJ11 camera performed in [EC2 Instance Configuration](docs-pt-br/05-Owncast-EC2-instance-configuration.md)
- (If the Owncast instance is offline), go to Instances in EC2, select the Owncast EC2 instance, click the Instance state button, then click Start instance. Wait for the instance to change status to running
- To test the administration panel, instead of accessing via `[public_IP_associated_with_instance]:8080/admin`, access it via `https://[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/admin`
- To test live streaming, in the SJCAM Zone app, change the RMTP server (which was in the example). `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` to `rtmps://[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T`
- ##### Note: Please note that the site is now accessed via https and live streaming is via rtmps

### For Option A, the detail is that the digital certificate expires in 3 months, so you will need to renew it when it expires or before
- To renew when it expires:
  - Redo the NACL, Security Group, and IAM Role assignment steps on the Proxy EC2 instance described above
  - Access the instance via the bash terminal
  - If the certificate has already expired, re-run the following command:
```
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
```
  - If the certificate has not yet expired but you want to update it, run the command Command:
```
sudo certbot renew --force-renewal
```
  - Regardless of the command executed to generate the new certificate, after issuing it, execute the commands:
```
sudo bash -c 'cat /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/fullchain.pem /etc/letsencrypt/live/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN]/privkey.pem > /etc/haproxy/certs/[YOUR_SUB_DOMAIN].[YOUR_DOMAIN].pem'
sudo systemctl restart haproxy
```
  - Remember to replace [YOUR_SUB_DOMAIN] and [YOUR_DOMAIN] with your respective subdomain and domain

### Unassign the IAM role from the instance. Finally, under EC2 Instances, select the Proxy instance, click the Actions button, then click Security, then Modify IAM role. Under IAM role, select the No IAM Role option, and then click the Update IAM role button. In the confirmation box, type Detach in the field and then click the Detach button

### We will undo the Security Group and NACL changes to the instance at the end of this instruction page

#### Option B
- Connected to the instance, enter the following command to configure HAProxy:
```
sudo nano /etc/haproxy/haproxy.cfg
```
- Scroll to the end of the file and insert the following content:
```
# ========== GLOBAL & DEFAULTS ==========
global
    log stdout format raw local0
    tune.ssl.default-dh-param 2048

defaults
    mode    http
    timeout connect 5s
    timeout client  50s
    timeout server  5m

# ========== RTMP PROXY PARA 1935 ==========
frontend rtmp_front
    bind *:1935
    mode tcp
    default_backend rtmp_back

backend rtmp_back
    mode tcp
    option tcp-check
    tcp-check connect port 1935
    server owncast_rtmp [Owncast_Instance_Private_IP]:1935 check

# ========== HTTP PROXY PARA 8080 ==========
frontend https_front
    bind *:8080
    mode http
    option forwardfor
    http-request set-header X-Forwarded-Proto https

    acl blocked_path path_beg /hls
    http-request deny if blocked_path

    default_backend http_back

backend http_back
    mode http
    server owncast_http [Owncast_Instance_Private_IP]:8080 check
```
- To save the configuration file you just modified, press the [CTRL] key and the [O] key simultaneously (remember that this example is using a standard Windows keyboard) and then press the [ENTER] key to confirm saving the file
- To exit the text editor, press the [CTRL] key and the [X] key simultaneously (remember that this example is using a standard Windows keyboard)
- Finally, run the following commands to apply the changes to the HAProxy service:
```
sudo systemctl enable haproxy
sudo systemctl restart haproxy
exit
```
- Now you can repeat the same tests for accessing the Owncast admin panel and using the SJCAM SJ11 camera performed in [EC2 Instance Configuration](docs-en-us/05-Owncast-EC2-instance-configuration.md)
  - (If the Owncast instance is offline), go to Instances in EC2, select the Owncast EC2 instance, click the Instance state button, and then click Start instance. Wait for the instance to change status to running
  - To test the admin panel, access it via `[Public_IP_associated_with_instance]:8080/admin` in the same way as previously. The difference is that you access it via a proxy, and communication with the Owncast instance is on the private network
  - To test live streaming, in the SJCAM Zone app, also access it via `rtmp://xx.xxx.xxx.xx:1935/live/tEMfBI2K2X3Id1!bI6s^pt4c0Aun*T` in the same way as done before, the difference is that it enters via Proxy and communication with the Owncast instance is on the private network

### Let's undo a few things:
- Go to Network ACLs still in the VPC, select the NACL associated with the Public Subnet
  - Go to the Inbound rules tab and click the Edit inbound rules button
    - Rule number 103 (this is an example), SSH (port 22), Source: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example), Custom TCP (port range 1024 - 65535), Source: 0.0.0.0/0 -> Click the Remove button
    - Click the Save changes button
  - Go to the Outbound rules tab and click the Edit outbound rules button
    - Rule number 103 (this is an example), HTTP (port 80), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 104 (this is an example) (an example), DNS (UDP) (port 53), Destination: 0.0.0.0/0 -> Click the Remove button
    - Rule number 105 (this is an example), HTTPS (port 443), Destination: 0.0.0.0/0 -> Click the Remove button
    - Click the Save changes button
- Go to the Instances menu in EC2, select the instance corresponding to the Proxy, click the Actions button, then click the Security option, and then click Change security groups
  - In the Maintenance Security Group row -> Click the Remove button
  - Click the Save button

### Don't forget to undo the rules as instructed above. This is necessary to ensure minimal access and avoid the risk of unwanted access
### Remember to shut down the instances to avoid incurring additional charges

---
[⬅️ Previous: Configuring EC2 instances](05-Owncast-EC2-instance-configuration.md) | [🏠 Index](../README.md) | [Next: Route 53 configuration ➡️](07-Route53.md)