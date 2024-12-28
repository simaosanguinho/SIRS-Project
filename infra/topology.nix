{ config, ... }:
let
  inherit
    (config.lib.topology)
    mkInternet
    mkConnection
    ;
in
{
  networks.car1-dmz = {
    name = "Car1 DMZ";
    cidrv4 = "10.10.0.0/24";
  };
  networks.manufacturer-dmz = {
    name = "Manufacturer DMZ";
    cidrv4 = "10.50.0.0/24";
  };
  nodes.internet = mkInternet {
    connections = [
      (mkConnection "user" "eth0")
      (mkConnection "mechanic" "eth0")
    ];
  };

}
