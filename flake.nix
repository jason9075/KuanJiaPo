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
        mysql-connector
        pillow
        requests
      ];
      python = let
        packageOverrides = self: super: {
          opencv4 = super.opencv4.override {
            enableGtk2 = true;
            gtk2 = pkgs.gtk2;
            enableFfmpeg = true;
            ffmpeg_3 = pkgs.ffmpeg-full;
          };
        };
      in pkgs.python312.override {
        inherit packageOverrides;
        self = python;
      };
    in {
      devShells.x86_64-linux.default = pkgs.mkShell {
        nativeBuildInputs = with pkgs; [ pythonEnv entr ffmpeg_6-full ];

        shellHook = ''
          echo "KuanJiaPo Nix environment activated."
        '';
      };
    };
}
