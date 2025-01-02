{ pkgs, pythonDeps, ... }:
let
  mkMotoristPkg = pkgName:
    pkgs.python3.pkgs.buildPythonPackage rec {
      pname = pkgName;
      version = "1.0.0";
      format = "pyproject";

      src = ./.;

      propagatedBuildInputs = pythonDeps pkgs.python3.pkgs;
    };
in
{
  motorist = mkMotoristPkg "motorist";
}
