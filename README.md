# MillsMapping

This repo queries odk central server and updates a webmap automatically

## Install instructions

- Create a Digital Ocean droplet, and associate a domain name with it.
- Create a user called ```millsmap``` with sudo privileges.
- From the ```millsmap``` user account, clone this repo. Step into it with ```cd MillsMap```.
- Run the installation script with ```script/setup.sh```.
  - Follow instructions. It needs the domain name, and your email so that LetsEncrypt can inform you when your certificate is expiring.
