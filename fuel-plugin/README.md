plugin-yardstick
================

Plugin description
Installs Yardstick on base-os node via a fuel plugin.

1) install vagrant fuel plugin builder (fpb)
    sudo apt-get install -y ruby-dev rubygems-integration python-pip rpm createrepo dpkg-dev
    sudo gem install fpm
    sudo pip install fuel-plugin-builder
2) build plugin
    fpb --build <plugin-dir>
    e.g.: fpb --build yardstick/fuel-plugin

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
    source /var/lib/yardstick.openrc
    source /var/lib/yardstick/bin/activate
    export EXTERNAL_NETWORK="admin_floating_net"
    yardstick task start /opt/yardstick/fuel-plugin/fuel_ping.yaml
