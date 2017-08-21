apt-get install -y nodejs
apt-get install -y npm
ln -s /usr/bin/nodejs /usr/bin/node
npm install
npm install -g grunt
npm install -g bower
bower install --force --allow-root
grunt build
