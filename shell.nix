let
  pkgs = import <nixpkgs> { };
  smopy = pkgs.python311Packages.buildPythonPackage rec {
    pname = "smopy";
    version = "latest";
    src = pkgs.fetchFromGitHub {
      owner = "rossant";
      repo = "smopy";
      rev = "v${version}";
      sha256 = "sha256-ds3BQryv9uwJYfpqbFOT7Cxm2HkHhfVqvu8eeyaAET0=";
    };
    propagatedBuildInputs = with pkgs.python311Packages; [
      ipython
      matplotlib
      numpy
      pillow
    ];
  };
  python-packages = ps: with ps; [
    folium
    geopy
    matplotlib
    networkx
    overpy
    smopy
  ];
in
pkgs.mkShell {
  buildInputs = [
    (pkgs.python311.withPackages python-packages)
  ];
}
