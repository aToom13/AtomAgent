#!/bin/bash
# VNC Server with XFCE Desktop for AtomAgent Sandbox

# Kill existing processes
pkill -f Xvfb 2>/dev/null
pkill -f x11vnc 2>/dev/null
pkill -f websockify 2>/dev/null
pkill -f xfce 2>/dev/null

# Start Xvfb (Virtual Framebuffer)
Xvfb :99 -screen 0 1280x720x24 &
sleep 2

# Export display
export DISPLAY=:99

# Start dbus
eval $(dbus-launch --sh-syntax)

# Start XFCE Desktop
startxfce4 &
sleep 3

# Start x11vnc
x11vnc -display :99 -forever -shared -rfbport 5900 -bg \
    -noxdamage -o /tmp/x11vnc.log

# Start noVNC
websockify --web=/usr/share/novnc 6080 localhost:5900 &

echo "XFCE Desktop started!"
echo "  - VNC Port: 5900"
echo "  - noVNC: http://localhost:6080/vnc.html"
