{
  description = "A basic flake with a shell";
  inputs.nixpkgs = {
    type = "github";
    owner = "NixOS";
    repo = "nixpkgs";
    ref = "nixpkgs-unstable";
    # Known-stable revision:
    #rev = "f096b7122ab08e93c8b052c92461ca71b80c0cc8";
  };
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.flake-compat = {
    url = "github:edolstra/flake-compat";
    flake = false;
  };

  outputs = { self, nixpkgs, flake-utils, flake-compat }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # config.allowUnfree = true;
        };
      in
      {
        devShell = pkgs.mkShell {
          nativeBuildInputs = [
            pkgs.bashInteractive
            pkgs.gcc
            pkgs.poetry
            pkgs.python3
            pkgs.python3Packages.matplotlib
          ];
          buildInputs = [
          ];
        };
      });
}

