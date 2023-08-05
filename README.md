# Work In Progress

`walk-selector` is currently a work in progress.

# Terminology

**walk** does not refer to a [walk](https://mathworld.wolfram.com/Walk.html) in the traditional graph theory sense -- it refers to using your 2 legs and unfaltering enthusiasm to get out into the world and smell some (hopefully) fresh air. A walk in this sense, using graph theory terminology, is a **closed walk**, but with many custom exceptions because our neighborhoods unfortunately weren't designed by [Euler](https://en.wikipedia.org/wiki/Leonhard_Euler#Graph_theory). Shame.

# Motivation

I like going for walks. I don't like when my walks are too long, or too short. I don't like planning routes, but old routes get... old. I hereby present _walk selector_!
Is this necessary? Absolutely not. Is anything necessary?

With walk selector, you can find k routes from your home to... your home! (Feel free to replace home with grandma's home, local ice cream shop, or similar. No, there's nothing wrong with grabbing ice cream twice.)

# Installation

## Nix

```
git clone git@github.com:IsaacShaha/walk-selector.git
cd walk-selector
nix-shell
```

## Non-Nix

```
git clone git@github.com:IsaacShaha/walk-selector.git
cd walk-selector
pip install -r requirements.txt
```

# Usage

To use `walk selector`, first create a `config.ini` file that contains the following configurations under the default configuration header:

- **HomeNode:** The node from which you will depart/return. You can find your node on [OpenStreetMap](https://www.openstreetmap.org/).
- **MaxDistance:** The maximum distance you are willing to walk in meters. Significantly affects performance.
- **NumWalks:** The number of walks you would like to generate. Has no effect on performance.

Here's an example `config.ini`:

```
[DEFAULT]
HomeNode = 25840120
MaxDistance = 1000
NumWalks = 23
```

Then, run `python walk-selector.py` with any of the following options:

    follow = "--follow" in args or "-f" in args
    gallery = "--gallery" in args or "-g" in args
    overpass = "--overpass" in args or "-o" in args
    save = "--save" in args or "-s" in args

- `-f`, `--follow`: Follow the walk as it plots. Mostly useful for debugging -- you will never finish your plotting this way unless your graph is extremely small.
- `-g`, `--gallery`: View each walk in `matplotlib`.
- `-o`, `--overpass`: Generate overpass queries for each map. You can run these queries at `https://overpass-turbo.eu/`. For nerds only.
- `-s`, `--save`: Save maps for each walk in the `maps` directory. You can open these interactive maps on your browser.

# To-Do

1. Remove mini detours (e.g. deviate from a path for for 10 meters only to immediately return to it)
1. Take the back side off folium arrows.
1. Allow adding a minimum distance for walks.
1. List all exceptions to formally define a `walk` in this case in the [terminology](#terminology) section.
1. Remake this whole thing in Haskell (because I <3 functional programming).
