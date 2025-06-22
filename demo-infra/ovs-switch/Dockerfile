FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y \
    openvswitch-switch \
    openssh-server \
    sudo \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    vim \
    iptables \
    traceroute \
    && mkdir /var/run/sshd

# Create user
RUN useradd -ms /bin/bash ovsuser && \
    echo 'ovsuser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create .ssh directory
RUN mkdir -p /home/ovsuser/.ssh && \
    chown -R ovsuser:ovsuser /home/ovsuser/.ssh && \
    chmod 700 /home/ovsuser/.ssh

# Configure SSH
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config

EXPOSE 22

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"] 