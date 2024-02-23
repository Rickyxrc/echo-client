{
    description = "a simple text based server for Echo.";

    inputs = {
        nixpkgs.url = "github:nixos/nixpkgs/nixos-23.11";
        poetry2nix.url = "github:nix-community/poetry2nix";
    };

    outputs = { nixpkgs, poetry2nix, ...}: let
        system = "x86_64-linux";
        pkgs = import nixpkgs {
            inherit system;
            overlays = [ poetry2nix.overlays.default ];
        };
        app = pkgs.poetry2nix.mkPoetryApplication {
            projectDir = pkgs.stdenv.mkDerivation {
                name = "echo-client-core";
                # TODO: This is DIRTY, fix it.
                src = pkgs.nix-gitignore.gitignoreSource (pkgs.lib.cleanSource ./.) (pkgs.lib.cleanSource ./.);
                buildInputs = [];
                buildPhase = ''
                    source $stdenv/setup
                    mkdir -p $out
                    cp . $out -r
                    # execute more script here
                '';
            };
        };
    in {
        devShells."${system}" = {
            default = pkgs.mkShell {
                packages = with pkgs; [ poetry ];
            };
        };

        packages."${system}".default = pkgs.writeShellApplication {
            name = "echo-client";
            runtimeInputs = [ app.dependencyEnv ];
            text = ''
                python -m echo_client "$@"
            '';
        };
    };
}
