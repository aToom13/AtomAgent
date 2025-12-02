# AtomAgent Sandbox - Headless Ubuntu for Agent
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=agent
ENV PASSWORD=agent123

# Temel sistem paketleri (agent sudo ile istediğini kurabilir)
RUN apt-get update && apt-get install -y \
    # Python & Node
    python3 python3-pip python3-venv \
    nodejs npm \
    # Temel araçlar
    git curl wget \
    vim nano \
    build-essential \
    # Ağ
    net-tools iputils-ping openssh-client \
    # Yardımcı
    htop tree jq unzip \
    sudo \
    # apt-get clean yapmıyoruz - agent paket kurabilsin
    && rm -rf /var/lib/apt/lists/*

# Kullanıcı oluştur (NOPASSWD sudo yetkili - her şeyi kurabilir)
RUN useradd -m -s /bin/bash $USER \
    && echo "$USER:$PASSWORD" | chpasswd \
    && echo "$USER ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Sadece temel Python paketleri (agent pip ile istediğini kurabilir)
RUN pip3 install --no-cache-dir \
    requests \
    beautifulsoup4

# Çalışma dizini
RUN mkdir -p /home/$USER/workspace /home/$USER/shared \
    && chown -R $USER:$USER /home/$USER

WORKDIR /home/$USER/shared
USER $USER

# Container açık kalsın
CMD ["tail", "-f", "/dev/null"]
