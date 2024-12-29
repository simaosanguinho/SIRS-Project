_: {
  # NOTE: SSH server is only used for development purposes.
  # It wouldn't be enabled in a real-world scenario.
  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "yes";
    };
  };
}
