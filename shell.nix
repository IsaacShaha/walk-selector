let
  pkgs = import <nixpkgs> { };

  # Python setup.
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
  python = pkgs.python311.withPackages (ps: with ps; [
    folium
    geopy
    matplotlib
    networkx
    overpy
    smopy
  ]);
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    haskell-language-server
    python
    stack
  ];
}
