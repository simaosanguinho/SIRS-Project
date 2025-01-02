#!/usr/bin/env bash

# Make shell script panic when using unset variables.
set -u

ifaces=(vmmechanic0 vmuser0
  vmcar1-db0 vmcar1-web0 vmcar1-web1
  vmmanuf-db0 vmmanuf-web0 vmmanuf-web1)

bridges=(brcar1-dmz brmanuf-dmz brwww)

function create_bridge() {
  BRIDGE_NAME=$1
  if ! ip link show "$BRIDGE_NAME" &>/dev/null; then
    echo "Creating bridge $BRIDGE_NAME..."
    sudo ip link add "$BRIDGE_NAME" type bridge
  fi
  sudo ip link set dev $BRIDGE_NAME up
}

function bridge_addiface() {
  BRIDGE_NAME=$1
  IFACE_NAME="$2"
  echo "Adding iface $IFACE_NAME to bridge $BRIDGE_NAME"
  sudo ip link set "$IFACE_NAME" master "$BRIDGE_NAME"
  # if ! ip link show "$BRIDGE_NAME" &>/dev/null; then
  #   echo "Creating bridge $BRIDGE_NAME..."
  #   sudo ip link add "$BRIDGE_NAME" type bridge
  # fi
  # sudo ip link set dev $BRIDGE_NAME up
}

function create_vm_iface() {
  IFACE_NAME="$1"
  if ! ip link show "$IFACE_NAME" &>/dev/null; then
    echo "Creating iface ${IFACE_NAME}..."
    sudo ip tuntap add "${IFACE_NAME}" mode tap user $USER
  fi
  sudo ip link set "$IFACE_NAME" up
}

function cleanup() {
  for iface in "${ifaces[@]}"; do
    echo "Deleting iface ${iface}..."
    sudo ip link delete "$iface"
  done

  for bridge in "${bridges[@]}"; do
    echo "Deleting bridge ${bridge}..."
    sudo ip link delete "$bridge"
  done
}

function bootstrap() {
  # Ensure all ifaces are created
  for iface in "${ifaces[@]}"; do
    create_vm_iface $iface
  done

  # Bridge brcar1-dmz
  create_bridge brcar1-dmz
  bridge_addiface brcar1-dmz vmcar1-db0
  bridge_addiface brcar1-dmz vmcar1-web0
  sudo ip address add dev brcar1-dmz 10.10.0.254/24

  # Bridge brmanuf-dmz
  create_bridge brmanuf-dmz
  bridge_addiface brmanuf-dmz vmmanuf-db0
  bridge_addiface brmanuf-dmz vmmanuf-web0
  sudo ip address add dev brmanuf-dmz 10.20.0.254/24

  # Bridge 'brwww' - represents the internet
  create_bridge brwww
  bridge_addiface brwww vmcar1-web1
  bridge_addiface brwww vmmanuf-web1
  bridge_addiface brwww vmuser0
  bridge_addiface brwww vmmechanic0
  sudo ip address add dev brwww 193.135.1.254/24

  # Enable IP Forwarding on the host
  sudo sysctl net.ipv4.ip_forward=1
}

if [ "$1" == "cleanup" ]; then
  echo "Cleaning up host networking..."
  cleanup
  exit 0
fi
if [ "$1" == "bootstrap" ]; then
  echo "Bootstraping host networking..."
  bootstrap
  exit 0
fi
echo "Usage: $0 <boostrap | cleanup>"
