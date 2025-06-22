# Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Update package list and install basic dependencies
RUN apt update && \
    apt install -y \
    curl \
    gnupg \
    lsb-release \
    ca-certificates \
    openssh-server \
    sudo \
    ansible \
    iproute2 \
    iputils-ping \
    net-tools \
    tcpdump \
    vim \
    iptables \
    traceroute \
    && mkdir /var/run/sshd

# Add FRR GPG key and repository
RUN curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add - && \
    echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) frr-stable | tee -a /etc/apt/sources.list.d/frr.list

# Install FRR
RUN apt update && \
    apt install -y frr frr-pythontools && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Create Ansible user
RUN useradd -ms /bin/bash frruser && \
    echo 'frruser ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Create .ssh directory and set permissions
RUN mkdir -p /home/frruser/.ssh && \
    chown -R frruser:frruser /home/frruser/.ssh && \
    chmod 700 /home/frruser/.ssh

# Enable SSH password + pubkey auth
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'PubkeyAuthentication yes' >> /etc/ssh/sshd_config

# Configure FRR - Enable commonly used routing protocols
RUN sed -i 's/bgpd=no/bgpd=yes/' /etc/frr/daemons && \
    sed -i 's/ospfd=no/ospfd=yes/' /etc/frr/daemons && \
    sed -i 's/ospf6d=no/ospf6d=yes/' /etc/frr/daemons && \
    sed -i 's/staticd=no/staticd=yes/' /etc/frr/daemons

# Add FRR daemon options to reduce FD limit warnings and optimize performance
RUN echo '' >> /etc/frr/daemons && \
    echo '# Daemon options' >> /etc/frr/daemons && \
    echo 'MAX_FDS=1024' >> /etc/frr/daemons && \
    echo 'watchfrr_options="--log-level=warning"' >> /etc/frr/daemons

# Copy FRR configuration
COPY frr.conf /etc/frr/frr.conf

# Set proper permissions for FRR
RUN chown -R frr:frr /etc/frr && \
    chmod 640 /etc/frr/daemons && \
    chmod 640 /etc/frr/frr.conf

# Expose SSH
EXPOSE 22

# Use entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
CMD ["/entrypoint.sh"]
