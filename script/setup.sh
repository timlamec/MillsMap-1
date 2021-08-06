#!/bin/bash

# Sets up a MillsMap server.
# Tested on a $10/month Digital Ocean droplet with Ubuntu 20.04
# installed.

# Assumes a non-root sudo user called reetta.

echo please enter the domain name of your server
read domain_name
echo
echo Please enter an email address for certificate renewal information
read email
echo
echo Updating and upgrading the OS
sudo apt -y update
sudo apt -y upgrade

echo setting up a few random Python dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3-setuptools

echo setting up virtualenv and Flask infrastructure
sudo apt install -y python3-venv
sudo apt install -y python3-dev
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install flask
pip install uwsgi

echo installing nginx
if ! type "nginx"; then
    sudo apt install -y nginx
else echo Nginx seems to be already installed
fi


echo adding the Web map site to nginx
cat > millsmap <<EOF
server {
    listen 80;
    server_name $domain_name www.$domain_name;

    location / {
        include uwsgi_params;
        uwsgi_pass unix:/millsmap/millsmap.soc
    }
}
EOF

sudo mv millsmap /etc/nginx/sites-available/

echo creating symlink to millsmap site in nginx sites-enabled
if [ ! -f /etc/nginx/sites-enabled/millsmap ]; then
    sudo ln -s /etc/nginx/sites-available/millsmap /etc/nginx/sites-enabled
else echo Looks like the symlink has already been created
fi

echo installing Certbot
if ! type "certbot"; then
    sudo apt install -y certbot python3-certbot-nginx
else echo Certbot seems to be already installed
fi

echo Procuring a certificate for the site from LetsEncrypt using Certbot
sudo certbot --nginx -n --agree-tos --redirect -m $email -d $domain_name -d www.$domain_name


echo adding the MillsMap service to Systemd
cat > millsmap.service <<EOF
[Unit]
Description=uWSGI instance to serve millsmap
After=network.target

[Service]
User=reetta
Group=www-data
WorkingDirectory=/home/millsmap
Environment="PATH=/home/millsmap/venv/bin"
ExecStart=/home/millsmap/venv/bin/uwsgi --ini millsmap.ini

[Install]
WantedBy=multi-user.target
EOF

sudo mv millsmap.service /etc/systemd/system/

echo starting and enabling the MillsMap service with Systemd
sudo systemctl start millsmap.service
sudo systemctl enable millsmap.service

echo
echo ##################################################
echo NOW YOU NEED TO PROVIDE A URL_formats.txt FILE!!!!
echo ##################################################
