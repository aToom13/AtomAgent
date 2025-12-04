# AtomAgent Sandbox - Ubuntu with XFCE Desktop
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV USER=agent
ENV PASSWORD=agent123
ENV DISPLAY=:99

# Temel sistem paketleri + XFCE Masaüstü
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
    # X11 & VNC
    xvfb \
    x11vnc \
    novnc \
    websockify \
    # XFCE Masaüstü Ortamı
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    # GUI kütüphaneleri
    python3-tk \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    # Dosya yöneticisi ve uygulamalar
    thunar \
    mousepad \
    && rm -rf /var/lib/apt/lists/*

# Python symlink (python -> python3)
RUN ln -sf /usr/bin/python3 /usr/bin/python

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

# VNC başlatma scripti
COPY --chown=$USER:$USER start-vnc.sh /home/$USER/start-vnc.sh
RUN chmod +x /home/$USER/start-vnc.sh

WORKDIR /home/$USER/shared
USER $USER

# VNC portları
EXPOSE 5900 6080

# Container açık kalsın
CMD ["tail", "-f", "/dev/null"]
