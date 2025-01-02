#!/usr/bin/env bash
VM_NAME=$1
sudo nix run path:.#nixosConfigurations.$VM_NAME.config.microvm.declaredRunner
