{ config, lib, ... }:
let
  inherit (lib) mkOption mkEnableOption types;
  cfg = config.services.motorist-server;
in
{
  options = {
    services.motorist-server = {
      enable = mkEnableOption "motorist";
      entrypoint = mkOption {
        type = types.str;
        default = null;
      };
      dbuser = mkOption {
        type = types.str;
        default = null;
      };
      initDBFile = mkOption {
        type = types.str;
        default = null;
      };
      environment = mkOption {
        type = types.attrs;
        default = { };
      };
    };

  };
  config = lib.mkIf cfg.enable {

    # Open port in firewall.
    networking.firewall.allowedTCPPorts = [
      443
    ];

    # networking.firewall.allowedUDPPorts = [
    #     443
    # ];
    services.motorist-server.environment = {
      "KEY_STORE" = "/var/key_store";
      "CAR_PORT" = "443";
      "CAR_URL" = "https://car1-web.motorist.lan";
      "MANUFACTURER_PORT" = "443";
      "MANUFACTURER_URL" = "https://manufacturer-web.motorist.lan";
      "DEFAULT_CONFIG_PATH" = "/var/project-src/car/default_config.json";
    };

    users.users.motorist = {
      isSystemUser = true;
      group = "motorist";
      uid = 1000;
    };
    users.groups.motorist = { };

    systemd.services.motorist-server = {
      after = [ "multi-user.target" ];
      wantedBy = [ "multi-user.target" ];
      inherit (cfg) environment;
      serviceConfig = {
        User = "motorist";
        ExecStart = cfg.entrypoint;
        Restart = "on-failure";
        RestartSec = "30s";
        restartIfChanged = true;

        ReadWritePaths = [
          "/var/key_store"
        ];
      };
      # Hardening systemd service would be nice-to-have.
    };
  };

}
