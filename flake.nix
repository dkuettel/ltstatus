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
      packages.x86_64-linux.default = pkgs.writeScriptBin "ltstatus" ''
        #!${pkgs.zsh}/bin/zsh
        set -eu -o pipefail
        ${pkgs.uv}/bin/uv run --project ${self} --isolated --quiet python $@
      '';
    };
}
