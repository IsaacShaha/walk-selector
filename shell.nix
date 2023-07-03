let
  pkgs = import <nixpkgs> { };
  python-packages = ps: with ps; [
    folium
    geopy
    matplotlib
    networkx
    overpy
  ];
in
pkgs.mkShell {
  buildInputs = [
    (pkgs.python311.withPackages python-packages)
  ];
}
