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
python walk-selector.py
```

## Non-Nix

Sorry ~~losers~~ non-nix users, I haven't gotten this far yet.

# Usage

To use `walk selector`, first create a `walk.ini` file that contains the following configurations under the default configuration header:

- **HomeNode:** The node from which you will depart/return. You can find your node on [OpenStreetMap](https://www.openstreetmap.org/).
- **MaxDistance:** The maximum distance you are willing to walk in meters.

Here's an example `walk.ini`:

```
[DEFAULT]
HomeNode = 9837865171
MaxDistance = 1000
```

# To-Do

1. Combine sequences of nodes n_1, n_2, ..., n\_(k-1), n_k with distances d\_(1,2), d\_(2,3), ..., d\_(k-2,k-1), d\_(k-1,k) where:

   - n_0 does not have exactly 2 neighbors.
   - n_k does not have exactly 2 neighbors.
   - nodes n_2, n_3, ..., n\_(k-2), n\_(k-1) each have exactly 2 neighbors

   with only nodes n_1, n_k with distance d\_(1,2) + d\_(2,3) + ... + d\_(k-2,k-1) + d\_(k-1,k)

1. The walk selector currently finds all possible routes within the given maximum distance. Make it find only k routes. It's okay if they aren't the k shortest routes, as long as they are within the maximum distance.
1. Allow adding a minimum distance for walks.
1. List all exceptions to formally define a `walk` in this case in the [terminology](#terminology) section.
1. Remake this whole thing in Haskell (because I <3 functional programming).
