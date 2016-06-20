plugin-yardstick
================

Plugin description
Installs Yardstick on base-os node via a fuel plugin.


To build:
1) install fuel plugin builder (fpb)
	sudo apt-get install createrepo rpm dpkg-dev
	easy_install pip
	pip install fuel-plugin-builder

2) build plugin
	fpb --build <plugin-name>
	e.g.: fpb --build plugin-yardstick

3) copy plugin rpm to fuel master
	e.g. scp plugin-yardstick-0.1-0.1.0-1.noarch.rpm <user>@<server-name>:~/

4) install plugin
	fuel plugins --install <plugin-name>.rpm

5) prepare fuel environment
	on fuel dashboard, go to settings/other
	enable yardstick plugin with checkbox
	save settings

6) add nodes to environment

7) deploy

8) run
Once deployed, SSH to deployed node. Find IP of yardstick node.
SSH to yardstick node, Activate yardstick:
	source yardstick_env/bin/activate
