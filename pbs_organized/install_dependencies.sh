#!/usr/bin/env bash

set -e

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
# the following two lines are added for travis-ci
sudo add-apt-repository -y universe
sudo apt-get -q update
sudo apt-get install -y autoconf libtool
elif [[ "$OSTYPE" == "darwin"* ]]; then
    brew list autoconf || brew install autoconf
    brew list libtool || brew install libtool
fi

cd /tmp
rm -rf minisketch
git clone https://github.com/sipa/minisketch.git
cd minisketch
./autogen.sh && ./configure
make -j$(nproc)
sudo make install
cd /tmp
rm -rf minisketch

rm -rf xxHash
git clone https://github.com/Cyan4973/xxHash.git
cd xxHash
make && sudo make install
cd /tmp 
rm -rf xxHash