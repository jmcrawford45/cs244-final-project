sudo apt-get update
sudo apt-get install build-essentials
sudo apt-get install git
sudo apt-get install zmap
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
sudo python get-pip.py
sudo pip install wget
wget https://dl.google.com/go/go1.10.2.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.10.2.linux-amd64.tar.gz
export PATH=$PATH:/usr/sbin:/usr/local/sbin:/usr/local/go/bin
export PATH=$PATH:$(go env GOPATH)/bin
export GOPATH=$(go env GOPATH)
go get github.com/zmap/zgrab
cd $GOPATH/src/github.com/zmap/zgrab
go install
cd
git clone https://github.com/lz4/lz4
cd lz4
sudo make install
cd
git clone https://github.com/jmcrawford45/cs244-final-project
cd cs244-final-project
