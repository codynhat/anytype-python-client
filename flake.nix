{
  description = "A Python environment for anytype-python-client";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python3 = pkgs.python312;

        # Create a simple Python package for anytype-client using buildPythonPackage
        anytype-client = python3.pkgs.buildPythonPackage rec {
          pname = "anytype-client";
          version = "0.1.0";

          src = ./.;

          # Patch pyproject.toml to update httpx version requirement
          postPatch = ''
            substituteInPlace pyproject.toml --replace 'httpx = "^0.24.0"' 'httpx = "^0.28.0"'
          '';

          # Use pyproject build system with Poetry
          format = "pyproject";

          # Add Poetry build dependencies
          nativeBuildInputs = with python3.pkgs; [
            poetry-core
          ];

          # Only include the essential dependencies that we know work
          propagatedBuildInputs = with python3.pkgs; [
            httpx
            pydantic
            python-dotenv
          ];

          # Skip tests for now
          doCheck = false;

          # Skip dependency resolution issues
          pythonImportsCheck = [ "anytype_client" ];
        };

        # Create Python environment with the custom package
        pythonEnv = python3.withPackages (ps: [ anytype-client ]);
      in {
        packages = {
          default = pythonEnv;
          anytype-client = pythonEnv;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
          ];
        };
      }
    );
}
