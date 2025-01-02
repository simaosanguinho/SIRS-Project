{ lib, inputs, self }:
let
  # psql reference:
  #       psql "hostaddr=10.10.0.2 host=car1-db.motorist.lan port=5432 user=car1-web dbname=dbcar sslmode=verify-full sslcert=car1-web/entity.crt sslkey=car1-web/key.priv sslrootcert=ca/ca.crt"
  # inherit
  #   (config.lib.topology)
  #   mkInternet
  #   mkRouter
  #   mkSwitch
  #   mkConnection
  #   ;
  # config.lib.topology helper functions are not easy to access here;
  # just transcribe them here instead.
  projectRoot = lib.trim (builtins.readFile "${self}/.pwd");
  keyStore = "/var/key_store";
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
        ./modules/motorist-server.nix
        # Add more modules here
        {
          networking.hosts = {
            # Databases don't need to access web servers:
            # Thus, despite web servers having two IP addresses, we compromise and say that web DNS names only point to their public IP address.
            "193.135.1.1" = [ "car1-web.motorist.lan" ];
            "193.135.1.2" = [ "manufacturer-web.motorist.lan" ];
            "193.135.1.3" = [ "user.motorist.lan" ];
            "193.135.1.4" = [ "mechanic.motorist.lan" ];

            "10.10.0.2" = [ "car1-db.motorist.lan" ];
            "10.20.0.2" = [ "manufacturer-db.motorist.lan" ];
          };
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
                securityModel = "passthrough";
                source = "${projectRoot}/key_store";
                mountPoint = "/var/key_store-shared";
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
        ({ config, pkgs, ... }: {

          systemd.tmpfiles.rules = [
            "C+ /var/key_store - - - - /var/key_store-shared"
            "Z /var/key_store 0770 motorist root -"
            "z /var/key_store 0777 motorist root -"
            "z /var/key_store/ca/ca.crt 0777 motorist root -"
            "z /var/key_store/manufacturer/entity.crt 0777 motorist root -"
            "z /var/key_store/${config.networking.hostName}/key.priv 0600 motorist root -"
          ];

          microvm.socket = "/tmp/motorist-a17/${config.networking.hostName}.sock";

          environment.systemPackages = with pkgs; [
            htop
          ];
        })
        {
          # Optional module to minimize the size of each VM.
          imports = [
            (inputs.nixpkgs + "/nixos/modules/profiles/minimal.nix")
          ];

          # strip unneeded software to make VM lighter.
          environment.defaultPackages = [ ];
          xdg.icons.enable = false;
          xdg.mime.enable = false;
          xdg.sounds.enable = false;
          xdg.menus.enable = false;
          xdg.autostart.enable = false;

          nixpkgs.overlays = builtins.attrValues self.overlays;
        }
      ];
    };
in
{
  car1-web = makeHost ({ pkgs, ... }: {
    networking.hostName = "car1-web";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vmcar1-web0";
        mac = "02:00:00:01:00:01";
      }
      {
        type = "tap";
        # interface name on the host
        id = "vmcar1-web1";
        mac = "02:00:00:01:00:02";
      }
    ];
    systemd.network.networks."10-car1-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.10.0.1/24" ];
    };
    systemd.network.networks."10-www" = {
      matchConfig.Name = "eth1";
      networkConfig.DHCP = "no";
      address = [ "193.135.1.1/24" ];
    };
    services.motorist-server = {
      enable = true;
      #TODO: do we need these arguments??? @pereira0x
      #TODO: hostnames
      entrypoint = "${pkgs.mypkgs.motorist}/bin/car 1 1";
      environment = {
        # "PG_CONNSTRING" = "host=localhost port=5432 dbname=motorist-car-db user=postgres password=password";
        "PG_CONNSTRING" = "host=car1-db.motorist.lan port=5432 user=car1-web dbname=db sslmode=verify-full sslcert=${keyStore}/car1-web/entity.crt sslkey=${keyStore}/car1-web/key.priv sslrootcert=${keyStore}/ca/ca.crt";
      };
    };
    topology.self = {
      #FIXME
      # interfaces.eth0.network = "car1-dmz";
      # interfaces.eth1.physicalConnections = [ (mkConnectionRev "internet" "*") ];
    };
  });
  car1-db = makeHost {
    imports = [ ./modules/postgresql.nix ];
    networking.hostName = "car1-db";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vmcar1-db0";
        mac = "02:00:00:02:00:01";
      }
    ];
    systemd.network.networks."10-car1-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.10.0.2/24" ];
    };
    services.motorist-server.dbuser = "car1-web";
    topology.self = {
      #FIXME
      # interfaces.eth0.network = "car1-dmz";
    };
  };

  manufacturer-web = makeHost ({ pkgs, ... }: {
    networking.hostName = "manufacturer-web";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vmmanuf-web0";
        mac = "02:00:00:03:00:01";
      }
      {
        type = "tap";
        # interface name on the host
        id = "vmmanuf-web1";
        mac = "02:00:00:03:00:02";
      }
    ];
    systemd.network.networks."10-manuf-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.20.0.1/24" ];
    };
    systemd.network.networks."10-www" = {
      matchConfig.Name = "eth1";
      networkConfig.DHCP = "no";
      address = [ "193.135.1.2/24" ];
    };
    topology.self = {
      #FIXME
      # interfaces.eth0.network = "car1-dmz";
      # interfaces.eth1.physicalConnections = [ (mkConnectionRev "internet" "*") ];
    };

    services.motorist-server = {
      enable = true;
      entrypoint = "${pkgs.mypkgs.motorist}/bin/manufacturer";
    };
  });


  manufacturer-db = makeHost {
    imports = [ ./modules/postgresql.nix ];
    networking.hostName = "manufacturer-db";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vmmanuf-db0";
        mac = "02:00:00:04:00:01";
      }
    ];
    systemd.network.networks."10-manuf-dmz" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "10.20.0.2/24" ];
    };
    services.motorist-server.dbuser = "manufacturer-web";
    topology.self = {
      #FIXME
      # interfaces.eth0.network = "car1-dmz";
    };
  };

  user = makeHost {
    networking.hostName = "user";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vmuser0";
        mac = "02:00:00:05:00:01";
      }
    ];
    systemd.network.networks."10-www" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "193.135.1.3/24" ];
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
        id = "vmmechanic0";
        mac = "02:00:00:06:00:01";
      }
    ];
    systemd.network.networks."10-www" = {
      matchConfig.Name = "eth0";
      networkConfig.DHCP = "no";
      address = [ "193.135.1.4/24" ];
    };
    # topology.self = {
    # interfaces.eth0.physicalConnections = [(mkConnection "internet" "*")];
    # };
  };

}
