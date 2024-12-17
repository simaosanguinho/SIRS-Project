{
  description = "SIRS Project flake";

  inputs = {
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
    git-hooks-nix = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.nixpkgs-stable.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        # To import a flake module
        # 1. Add foo to inputs
        # 2. Add foo as a parameter to the outputs function
        # 3. Add here: foo.flakeModule
        inputs.git-hooks-nix.flakeModule
        inputs.treefmt-nix.flakeModule
      ];
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];
      perSystem =
        { config
        , pkgs
        , ...
        }:
        rec {
          # Per-system attributes can be defined here. The self' and inputs'
          # module parameters provide easy access to attributes of the same
          # system.

          # Equivalent to  inputs'.nixpkgs.legacyPackages.hello;
          # packages.default = pkgs.hello;

          devShells.default = pkgs.mkShell {
            packages = [
              (pkgs.python3.withPackages (python-pkgs: with python-pkgs; [
                click
                cryptography
                psycopg
                textual
                textual-dev # For developing Textual apps
                rich # For development/pretty print
                flask
              ]))
              pkgs.openssl
              pkgs.step-ca
              pkgs.step-cli
            ];
            shellHook = ''
              # export DEBUG=1
              ${config.pre-commit.installationScript}
            '';

          };

          pre-commit = {
            check.enable = true;
            settings.hooks = {
              actionlint.enable = true;
              treefmt.enable = true;
              commitizen = {
                enable = false;
                description = "Check whether the current commit message follows commiting rules. Allow empty commit messages by default, because they typically indicate to Git that the commit should be aborted.";
                entry = "${pkgs.commitizen}/bin/cz check --allow-abort --commit-msg-file";
                stages = [ "commit-msg" ];
              };
              gitleaks = {
                enable = true;
                name = "gitleaks";
                description = "Prevents commiting secrets";
                entry = "${pkgs.gitleaks}/bin/gitleaks protect --verbose --redact --staged";
                pass_filenames = false;
              };
            };
          };
          treefmt.programs = {
            nixpkgs-fmt.enable = true;
            shfmt.enable = true;
            mdformat.enable = true;
            deadnix.enable = true;
            statix.enable = true;
            ruff-check.enable = true;
            ruff-format.enable = true;
          };
        };



      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
