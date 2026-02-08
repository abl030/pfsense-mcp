{
  description = "AI-generated MCP server for the pfSense REST API v2 — 599 tools";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    forAllSystems = nixpkgs.lib.genAttrs [
      "x86_64-linux"
      "aarch64-linux"
    ];
  in {
    packages = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python3.withPackages (ps: [
        ps.fastmcp
        ps.httpx
      ]);
    in {
      default = pkgs.writeShellApplication {
        name = "pfsense-mcp";
        runtimeInputs = [pythonEnv];
        text = ''
          exec fastmcp run ${./generated/server.py}
        '';
      };
    });

    devShells = forAllSystems (system: let
      pkgs = nixpkgs.legacyPackages.${system};
      pythonEnv = pkgs.python3.withPackages (ps: [
        ps.fastmcp
        ps.httpx
        ps.jinja2
        ps.pytest
      ]);
    in {
      default = pkgs.mkShell {
        packages = [pythonEnv pkgs.qemu pkgs.curl];
      };
    });
  };
}
