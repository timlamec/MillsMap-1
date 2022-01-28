# MillsMapping

This repo queries odk central server and updates a webmap automatically. Currently specific to a project in Tanzania mapping mills. Could be generalized in the future, but that's out of scope for the current project!

# Install instructions

## Cloud deployment
- Create a Digital Ocean droplet (or other server on whatever infrastructure you prefer), and associate a domain name with it. Either disable the UFW firewall or poke the appropriate holes in it for nginx and ssh.
- Create a user called ```millsmap``` with sudo privileges.
- From the ```millsmap``` user account, clone this repo. Step into it with ```cd MillsMap```.
- You'll need a file called ```secret_tokens.json``` that contains a keys "email" and "password" that contain the username and password for an ODK Central server containing your mill map data.
  - Yes, we know that's not really the best way to do it. But it's reasonably secure for now, and we'll get around to hashing and salting the password later.
- Run the installation script with ```script/setup.sh```.
  - Follow instructions. It needs the domain name, and your email so that LetsEncrypt can inform you when your certificate is expiring.

## Local dev setup
For now, these instructions are specific to GNU/Linux. If you are working on Windows they definitely won't work, and on Mac they will require some tweaking.

- First install some Python infrastructure using your package manager. On Debian-derived distros such as Ubuntu, it'll look like this (if you're on another distro family, replace ```apt``` with the relevant package manager):

```
sudo apt install -y build-essential libssl-dev libffi-dev python3-setuptools python3-venv python3-dev
```

- Now create a VirtualEnv and populate it with the libraries needed for MillsMap:

```
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install flask
pip install flask-wtf
pip install requests
pip install pandas
pip install matplotlib
pip install uwsgi
```

__(Soon we'll [set this up with a requirements file so that Pip can manage this automatically](https://note.nkmk.me/en/python-pip-install-requirements/), but as of this writing we're still developing and it's not a priority)__

- At this point you're still in the venv (to the left of your terminal prompt you'll see ```(venv)```). If you want to get out of it for some reason, type ```deactivate``` (presumably that's not what you want to do right now, you want to start developing). To launch the local dev server, type ```python wsgi.py```. That'll launch a local webserver serving the Millsmap application on port 5000. Open your browser and visit [localhost:5000](http://localhost:5000/), which should display the application.

Another way to get a solid test webserver running to look for errors is with ```uwsgi --socket 0.0.0.0:5000 --protocol=http -w wsgi:app --enable-threads``` (with venv activated).

Note: It's convenient to develop from a local server. However, it can be deceptive; because there is almost no bandwidth constraint or delay between your server and client (both the Flask app and the browser are on the same computer), you will not notice problems that come from depending on fast communication between server and client. You may get a nasty surprise when you deploy to the cloud and find that things are unacceptably slow, perhaps even to the point of requests timing out so nothing works at all. There are lots of reasons to have a cloud instance that you can use to test while developing; this is only one of them!