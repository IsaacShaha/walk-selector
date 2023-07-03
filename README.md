# Work In Progress

`walk-selector` is currently a work in progress.

# Terminology

**walk** does not refer to a [walk](https://mathworld.wolfram.com/Walk.html) in the traditional graph theory sense -- it refers to using your 2 legs and unfaltering enthusiasm to get out into the world and smell some (hopefully) fresh air. A walk in this sense, using graph theory terminology, is a **closed walk**, but with many custom exceptions because our neighborhoods unfortunately weren't designed by [Euler](https://en.wikipedia.org/wiki/Leonhard_Euler#Graph_theory). Shame.

# walk-selector

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

# To-Do

1. The walk selector no longer backtracks through paths it has **just** took, but it still backtracks through paths it took before. I need to mark these paths as no longer traceable, with certain exceptions. For example, there are a few nodes near the target that should be revisitable so that a longer path to return to the target from the other side is not necessary.
1. The walk selector currently only finds 1 route. It needs to find k routes. These are not guaranteed to be the k shortest routes and I am okay with that.
1. Allow filtering walks to a certain range.
1. List all exceptions to formally define a `walk` in this case in the [terminology](#terminology) section.
1. Remake this whole thing in Haskell (because I <3 functional programming).
