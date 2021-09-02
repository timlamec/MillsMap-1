# MillsMapping

This repo queries odk central server and updates a webmap automatically. Currently specific to a project in Tanzania mapping mills. Could be generalized in the future, but that's out of scope for the current project!

## Install instructions

- Create a Digital Ocean droplet (or other server on whatever infrastructure you prefer), and associate a domain name with it. Either disable the UFW firewall or poke the appropriate holes in it for nginx and ssh.
- Create a user called ```millsmap``` with sudo privileges.
- From the ```millsmap``` user account, clone this repo. Step into it with ```cd MillsMap```.
- You'll need a file called ```secret_tokens.json``` that contains a keys "email" and "password" that contain the username and password for an ODK Central server containing your mill map data.
  - Yes, we know that's not really the best way to do it. But it's reasonably secure for now, and we'll get around to hashing and salting the password later.
- Run the installation script with ```script/setup.sh```.
  - Follow instructions. It needs the domain name, and your email so that LetsEncrypt can inform you when your certificate is expiring.
