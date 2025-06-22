FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y \
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
    wget \
    && mkdir /var/run/sshd

# Create user
RUN useradd -ms /bin/bash clientuser && \
    echo 'clientuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create .ssh directory
RUN mkdir -p /home/clientuser/.ssh && \
    chown -R clientuser:clientuser /home/clientuser/.ssh && \
    chmod 700 /home/clientuser/.ssh

# Configure SSH
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config

EXPOSE 22

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"] 