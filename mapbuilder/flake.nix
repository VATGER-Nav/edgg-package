{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    flake-parts.url = "github:hercules-ci/flake-parts";
    poetry2nix = {
      url = "github:fpletz/poetry2nix/ruff-0.3.0";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        flake-utils.follows = "flake-utils";
      };
    };
  };

  outputs =
    inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } (
      {
        inputs,
        lib,
        withSystem,
        ...
      }:
      {
        systems = [
          "x86_64-linux"
          "aarch64-linux"
        ];

        perSystem =
          {
            pkgs,
            system,
            self',
            ...
          }:
          let
            poetry2nix = import inputs.poetry2nix { inherit pkgs; };
            overrides = poetry2nix.overrides.withDefaults (
              final: prev: {
                pygeodesy = prev.pygeodesy.overridePythonAttrs (old: {
                  nativeBuildInputs = (old.nativeBuildInputs or [ ]) ++ [ final.setuptools ];
                });
              }
            );
            devEnv = poetry2nix.mkPoetryEnv {
              inherit overrides;
              projectDir = ./.;
              editablePackageSources = {
                mapbuilder = ./.;
              };
            };
          in
          {
            packages.default = poetry2nix.mkPoetryApplication {
              inherit overrides;
              projectDir = ./.;
            };
            devShells.default = devEnv.env.overrideAttrs (attrs: {
              nativeBuildInputs = attrs.nativeBuildInputs ++ [
                pkgs.poetry
                pkgs.nil
                pkgs.pyright
              ];
              shellHook = ''
                export PYTHONPATH=${devEnv}/${devEnv.sitePackages}
              '';
            });
            formatter = pkgs.nixfmt-rfc-style;
          };
      }
    );
}
