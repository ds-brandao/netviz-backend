# Setting up Fluent Bit on Ubuntu Server and sending logs to OpenSearch

```bash
# Update system packages
sudo apt-get update

# Install Fluent Bit using the official script
curl https://raw.githubusercontent.com/fluent/fluent-bit/master/install.sh | sh
```

```bash
# Configure Fluent Bit
sudo nano /etc/fluent-bit/fluent-bit.conf
```

## Example Fluent Bit Configuration

```ini
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info

[INPUT]
    Name              tail
    Path              /var/log/syslog
    Tag               syslog
    Skip_Long_Lines   On
    Refresh_Interval  10

[INPUT]
    Name              tail
    Path              /var/log/*.log
    Tag               logs.*
    Skip_Long_Lines   On
    Refresh_Interval  10

[OUTPUT]
    Name              opensearch
    Match             *
    Host              192.168.0.132
    Port              9200
    Index             ansible-logs
    Type              _doc
    Suppress_Type_Name On
    HTTP_User         admin
    HTTP_Passwd       xuwzuc-rExzo3-hotjed
    tls               On
    tls.verify        Off
```

## Start and enable Fluent Bit

```bash
sudo systemctl start fluent-bit
sudo systemctl enable fluent-bit
sudo systemctl status fluent-bit
```