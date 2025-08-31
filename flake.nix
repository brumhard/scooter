{
  # TODO: fix with https://medium.com/@daniel.garcia_57638/nix-nirvana-packaging-python-apps-with-uv2nix-c44e79ae4bc9

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    pyproject-nix,
  }: let
    supportedSystems = ["x86_64-linux" "x86_64-darwin" "aarch64-linux" "aarch64-darwin"];
    forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    project = pyproject-nix.lib.project.loadPyproject {
      # Read & unmarshal pyproject.toml relative to this project root.
      # projectRoot is also used to set `src` for renderers such as buildPythonPackage.
      projectRoot = ./.;
    };
  in {
    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShellNoCC {
        packages = with pkgs; [
          uv
        ];
      };
    });

    packages = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
      python = pkgs.python3;
      attrs = project.renderers.buildPythonPackage {inherit python;};
    in {
      default = python.pkgs.buildPythonPackage attrs;
    });
  };
}
