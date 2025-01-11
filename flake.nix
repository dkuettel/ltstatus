{
  description = "ltstatus";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    in
    {
      packages.x86_64-linux.default = pkgs.buildEnv {
        name = "ltstatus-env";
        # TODO in theory should set env here so that uv never tries do manage a python version
        paths = with pkgs; [ uv python313 ];
      };
      packages.x86_64-linux.app = pkgs.writeScriptBin "ltstatus" ''
        #!${pkgs.zsh}/bin/zsh
        set -eu -o pipefail
        ${pkgs.uv}/bin/uv run --python=${pkgs.python313}/bin/python --no-python-downloads --project ${self} --isolated --quiet python $@
      '';
    };
}
