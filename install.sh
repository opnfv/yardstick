# install tools
apt-get update && apt-get install -y \
    wget \
    expect \
    curl \
    git \
    sshpass \
    qemu-utils \
    kpartx \
    libffi-dev \
    libssl-dev \
    python \
    python-dev \
    libxml2-dev \
    libxslt1-dev \
    python-setuptools && \
    easy_install -U setuptools

apt-get -y autoremove && apt-get clean

source_file=/etc/apt/sources.list.d/yardstick.list
touch $source_file

# fit for arm64
echo -e "\n"
echo -e "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty main universe multiverse restricted" >> $source_file
echo -e "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-updates main universe multiverse restricted" >> $source_file
echo -e "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-security main universe multiverse restricted" >> $source_file
echo -e "deb [arch=arm64] http://ports.ubuntu.com/ubuntu-ports/ trusty-proposed main universe multiverse restricted" >> $source_file
echo "vm.mmap_min_addr = 0" > /etc/sysctl.d/mmap_min_addr.conf
dpkg --add-architecture arm64
apt-get install -y qemu-user-static libc6:arm64

# install yardstick + dependencies
easy_install -U pip
pip install -r tests/ci/requirements.txt
pip install .

rm $source_file
