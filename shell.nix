{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  name = "shell-dev";
  buildInputs = [ (import ./default.nix { inherit pkgs; }) ];
  shellHook = ''
    yarn global add @vue/cli
    yarn global add @vue/cli-service-global
    export PATH="$(yarn global bin):$PATH"
  '';
}
