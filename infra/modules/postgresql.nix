{ lib, config, pkgs, ... }:
let
  inherit (config.networking) hostName;
  inherit (config.services.motorist-server) dbuser;
in

{
  services.postgresql = {
    enable = true;
    ensureDatabases = [ "db" ];
    ensureUsers = [{
      name = "${dbuser}";
    }];
    enableTCPIP = true;
    settings = {
      log_connections = true; # For debugging
      port = 5432;
      ssl = true; # might be "on"
      ssl_ca_file = "/var/key_store/ca.crt";
      ssl_cert_file = "/var/lib/postgresql/keys/entity.crt";
      ssl_key_file = "/var/lib/postgresql/keys/key.priv";
      listen_addresses = lib.mkForce "0.0.0.0";
    };
    # authentication = pkgs.lib.mkOverride 10 ''
    #   #type database DBuser origin-address auth-method
    #   # local all      all     trust
    #   # ... other auth rules ...
    #
    #   # ipv4
    #   host  all      all     127.0.0.1/32   trust
    # '';
    authentication = pkgs.lib.mkForce ''
      # Schema:
      #type database DBuser origin-address auth-method

      # For debugging purposes, all connections from localhost are trusted.
      # This would not be true in production.
      local all      all     trust

      hostssl all    all     all           cert
    '';
    initialScript = pkgs.writeText "backend-initScript" ''
      CREATE ROLE "${dbuser}" LOGIN; -- user/role
      CREATE DATABASE db;
      GRANT ALL PRIVILEGES ON DATABASE db TO "${dbuser}";
    '';
    # CREATE ROLE ${dbuser} WITH LOGIN PASSWORD 'nixcloud' CREATEDB;
    # CREATE DATABASE nixcloud;
    # GRANT ALL PRIVILEGES ON DATABASE nixcloud TO nixcloud;
    # GRANT motorist_db TO "${dbuser}"; -- Add the user to the role
  };
  topology.self.services.postgresql = {
    name = "PostgreSQL";
    icon = ../media/postgresql-logo.svg;
  };

  networking.firewall.allowedTCPPorts = [
    5432
  ];

  # Copy keys to postgres directory and adjust permissions so postgres can read them
  systemd.tmpfiles.rules = [
    "C+ /var/lib/postgresql/keys - - - - /var/key_store/${hostName}"
    "z /var/lib/postgresql/keys 0550 postgres postgres -"
  ];
  # Allow postgresql to read keys directory
  systemd.services.postgresql.serviceConfig.ReadWritePaths = [
    "/var/lib/postgresql"
    "/var/key_store"
  ];
}
