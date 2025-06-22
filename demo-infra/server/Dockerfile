FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y \
    python3 \
    openssh-server \
    sudo \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    vim \
    iptables \
    traceroute \
    curl \
    && mkdir /var/run/sshd

# Create user
RUN useradd -ms /bin/bash serveruser && \
    echo 'serveruser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create .ssh directory
RUN mkdir -p /home/serveruser/.ssh && \
    chown -R serveruser:serveruser /home/serveruser/.ssh && \
    chmod 700 /home/serveruser/.ssh

# Configure SSH
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config

# Create web content directory
RUN mkdir -p /var/www && \
    echo "<h1>Hello from Server!</h1><p>This is the server connected to the switch.</p>" > /var/www/index.html

EXPOSE 22 8080

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"] 