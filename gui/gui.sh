curl -sL https://deb.nodesource.com/setup_8.x -o /tmp/nodesource_setup.sh
bash /tmp/nodesource_setup.sh
apt-get install -y nodejs
ln -s /usr/bin/nodejs /usr/bin/node
npm install
npm install -g grunt
npm install -g bower
bower install --force --allow-root
grunt build
