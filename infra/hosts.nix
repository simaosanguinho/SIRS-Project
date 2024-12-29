{ lib, inputs, self }:
let
  # inherit
  #   (config.lib.topology)
  #   mkInternet
  #   mkRouter
  #   mkSwitch
  #   mkConnection
  #   ;
  # config.lib.topology helper functions are not easy to access here;
  # just transcribe them here instead.
  projectDir = lib.trim (builtins.readFile "${self}/.pwd");
  mkConnectionRev = node: interface: {
    inherit node interface;
    renderer.reverse = true;
  };
  # Source: https://github.com/oddlama/nix-topology/blob/d6edd49bac68dc70e19b5e91617b9f04e8ac1c43/topology/helpers.nix 

  # End of transcribe
  makeHost = extraModule:

    inputs.nixpkgs.lib.nixosSystem {
      specialArgs = { rootDir = self; };
      modules = [
        # Include the microvm module
        inputs.microvm.nixosModules.microvm
        inputs.nix-topology.nixosModules.default
        extraModule
        ./modules/ssh-server.nix
        # Add more modules here
        {
          nixpkgs.hostPlatform = "x86_64-linux";
          system.stateVersion = "24.11";
          # Note: in a real-world scenario, a secure administrative password would be set.
          users.users.root.password = "sirs";
          microvm = {
            shares = [
              {
                proto = "9p";
                tag = "ro-store";
                # a host's /nix/store will be picked up so that no
                # squashfs/erofs will be built for it.
                source = "/nix/store";
                mountPoint = "/nix/.ro-store";
              }
              {
                proto = "9p";
                tag = "key_store";
                # Source path can be absolute or relative
                # to /var/lib/microvms/$hostName
                source = "${projectDir}/key_store";
                mountPoint = "/var/key_store";
              }
            ];

            hypervisor = "qemu";
          };

          # Networking
          boot.kernelParams = [ "ipv6.disable=1" ];
          networking.firewall.enable = true;
          networking.usePredictableInterfaceNames = false;
          # Network interfaces from systemd are detected automatically:
          systemd.network.enable = true;
          systemd.network.wait-online.enable = false;

          # Ensure our VMs trust our CA.
          security.pki.certificateFiles = [ "${self}/key_store/ca/ca.crt" ];
        }
      ];
    };
in
{
  car1-web = makeHost {
    networking.hostName = "car1-web";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-car1-dmz";
        mac = "02:00:00:00:00:01";
      }
      {
        type = "tap";
        # interface name on the host
        id = "vm-car1-wan";
        mac = "02:00:00:00:00:01";
      }
    ];
    systemd.network.networks."10-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.10.0.1/24" ];
    };
    systemd.network.networks."10-wan" = {
      matchConfig.Name = "eth1";
      networkConfig.DHCP = "no";
      address = [ "193.135.1.1/24" ];
    };
    topology.self = {
      interfaces.eth0.network = "car1-dmz";
      interfaces.eth1.physicalConnections = [ (mkConnectionRev "internet" "*") ];
    };



  };
  car1-db = makeHost {
    imports = [ ./modules/postgresql.nix ];
    networking.hostName = "car1-db";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-car1-db";
        mac = "02:00:00:00:00:02";
      }
    ];
    systemd.network.networks."10-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.10.0.2/24" ];
    };
    topology.self = {
      interfaces.eth0.network = "car1-dmz";
    };
    # services.postgresql = {
    #     
    #
    # };
  };
  user = makeHost {
    networking.hostName = "user";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-user";
        mac = "02:00:00:00:00:03";
      }
    ];
    systemd.network.networks."10-wan".address = [ "10.20.0.1/24" ];
    systemd.network.networks."10-wan" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
    };
    # topology.self = {
    # interfaces.eth0.physicalConnections = [(mkConnection "internet" "*")];
    # };
  };
  mechanic = makeHost {
    networking.hostName = "mechanic";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-mechanic";
        mac = "02:00:00:00:00:04";
      }
    ];
    systemd.network.networks."10-wan".address = [ "10.30.0.1/24" ];
    systemd.network.networks."10-wan" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
    };
    # topology.self = {
    # interfaces.eth0.physicalConnections = [(mkConnection "internet" "*")];
    # };
  };
  manufacturer-web = makeHost {
    networking.hostName = "manufacturer-web";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-manuf-web";
        mac = "02:00:00:00:00:05";
      }
    ];
    systemd.network.networks."10-wan".address = [ "10.40.0.1/24" ];
    systemd.network.networks."10-wan" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
    };
    # topology.self = {
    # interfaces.eth0.physicalConnections = [(mkConnection "internet" "*")];
    # };
  };
  manufacturer-db = makeHost {
    networking.hostName = "manufacturer-db";
    imports = [ ./modules/postgresql.nix ];
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-manuf-db";
        mac = "02:00:00:00:00:06";
      }
    ];
    systemd.network.networks."10-wan".address = [ "10.40.0.2/24" ];
    systemd.network.networks."10-wan" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
    };
    # topology.self = {
    # interfaces.eth0.physicalConnections = [(mkConnection "internet" "*")];
    # };
  };

}
