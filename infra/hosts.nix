{ lib, inputs }:
let
  makeHost = extraModule:

    inputs.nixpkgs.lib.nixosSystem {
      modules = [
        # Include the microvm module
        inputs.microvm.nixosModules.microvm
        extraModule
        # Add more modules here
        {
          nixpkgs.hostPlatform = "x86_64-linux";
          system.stateVersion = "24.11";
          users.users.root.password = "";
          microvm = {
            shares = [{
              # use proto = "virtiofs" for MicroVMs that are started by systemd
              proto = "9p";
              tag = "ro-store";
              # a host's /nix/store will be picked up so that no
              # squashfs/erofs will be built for it.
              source = "/nix/store";
              mountPoint = "/nix/.ro-store";
            }];

            hypervisor = "qemu";
          };
          networking.firewall.enable = true;
          networking.defaultGateway = {
            interface = "enp0s3";
            address = "10.10.0.1";
          };
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
        id = "vm-car1-web";

        # Ethernet address of the MicroVM's interface, not the host's
        #
        # Locally administered have one of 2/6/A/E in the second nibble.
        mac = "02:00:00:00:00:01";
      }
    ];

  };
  car1-db = makeHost {
    networking.hostName = "car1-db";
    microvm.interfaces = [
      {
        type = "tap";
        # interface name on the host
        id = "vm-car1-db";

        # Ethernet address of the MicroVM's interface, not the host's
        #
        # Locally administered have one of 2/6/A/E in the second nibble.
        mac = "02:00:00:00:00:02";
      }
    ];

  };

}
