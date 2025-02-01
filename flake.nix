{
  description = "KuanJiaPo project flake";

  inputs = { nixpkgs.url = "github:nixos/nixpkgs/nixos-24.05"; };

  outputs = { nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      pythonEnv = with pkgs.python312Packages; [
        fastapi
        (opencv4.override { enableGtk3 = true; })
        uvicorn
        mysqlclient
        pillow
        requests
      ];
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [ pythonEnv stdenv.cc.cc entr ];

        shellHook = ''
          if [ ! -f ".venv" ]; then
            python -m venv .venv
            source .venv/bin/activate
            pip install -r requirements.txt
          else
            source .venv/bin/activate
          fi
          export LD_LIBRARY_PATH=${
            pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ]
          }
          echo "KuanJiaPo Nix environment activated."
        '';
      };
    };
}
