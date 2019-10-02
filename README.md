# driptools

## How to set up environment
1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Setup redis server

1) linux
```bash
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```
OR
```bash
sudo apt-get install redis-server
```
2) [MacOs](
https://medium.com/@petehouston/install-and-config-redis-on-mac-os-x-via-homebrew-eb8df9a4f298)

3. Set up RabitMQ server

1) Installing RabbitMQ on Ubuntu 16.04
To install it on a newer Ubuntu version is very straightforward:
```bash
apt-get install -y erlang
apt-get install rabbitmq-server
```
Then enable and start the RabbitMQ service:

```bash
systemctl enable rabbitmq-server
systemctl start rabbitmq-server
```

check status the RabbitMQ service:

```bash
systemctl status rabbitmq-server
```

2) Installing RabbitMQ on Mac
Homebrew is the most straightforward option:

```bash
brew install rabbitmq
```

The RabbitMQ scripts are installed into /usr/local/sbin. You can add it to your .bash_profile or .profile.

```bash
vim ~/.bash_profile
```

Then add it to the bottom of the file:
```bash
export PATH=$PATH:/usr/local/sbin
```

Start server:
```bash
rabbitmq-server
```

3) Installing RabbitMQ on Windows and Other OSs
Unfortunately I don’t have access to a Windows computer to try things out, but you can find the [installation guide for Windows on RabbitMQ’s Website](https://www.rabbitmq.com/install-windows.html).

For other operating systems, check the [Downloading and Installing RabbitMQ on their Website](https://www.rabbitmq.com/download.html).

4) Install RabitMQ on CentOS/Fedora
```bash
sudo yum install -y erlang
sudo vim /etc/yum.repos.d/rabbitmq_rabbitmq-server.repo

[rabbitmq_rabbitmq-server]
name=rabbitmq_rabbitmq-server
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/7/$basearch
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300

[rabbitmq_rabbitmq-server-source]
name=rabbitmq_rabbitmq-server-source
baseurl=https://packagecloud.io/rabbitmq/rabbitmq-server/el/7/SRPMS
repo_gpgcheck=1
gpgcheck=0
enabled=1
gpgkey=https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
metadata_expire=300
```
```bash
sudo yum makecache -y --disablerepo='*' --enablerepo='rabbitmq_rabbitmq-server'
sudo yum -y install rabbitmq-server
```

4. [Install nltk library](https://nltk.readthedocs.io/en/latest/install.html)


## How to run app
1. Run the django app
```bash
python3 manage.py runserver
```
2. Open new tab in terminal and Run celery brokers
```bash
celery -A driptools worker -l info
```