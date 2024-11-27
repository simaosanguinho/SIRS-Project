{
  description = "SIRS Project flake";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShell = pkgs.mkShell {
          packages = [
            (pkgs.python3.withPackages
              (python-pkgs: [ python-pkgs.requests python-pkgs.pwntools python-pkgs.zodbpickle ]))
          ];
        };

      }
    );
}
