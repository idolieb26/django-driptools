# driptools

## How to set up environment
1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup redis server

```bash
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
```
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

## How to run app
1. Run the django app
```bash
python manage.py runserver
```
2. Run celery brokers
```bash
celery -A driptools worker -l info
```