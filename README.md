# PYVGC

PYVGC is a Python package for basic Pokémon Champions-based data science.
It is currently meant for Python 3.9 and newer, without runtime dependencies.

You can install it with pip
  -  `pip install pyvgc`

You may consult its official pypi page at [https://pypi.org/project/pyvgc/](https://pypi.org/project/pyvgc/)

It requires only a Python3.9+ environment and the standard library. It is currently in alpha development, but it can be used for basic Pokémon data science and damage calculations.

The current version supports the current Pokémon Champions regulations (m-a, m-b and m-c)

For some examples of what you can currently do, please check examples.py or the pyvgc_tutorial.ipynb notebook.

## Pokémon Showdown import and export

Import and export regulation-bound level-50 Pokémon using the official
Pokémon Showdown set format. The item is optional.

```python
from pyvgc import export_showdown_pokemon, import_showdown_pokemon

pokemon = import_showdown_pokemon(
    """dummy (Incineroar) @ Sitrus Berry
Ability: Intimidate
Level: 50
EVs: 32 HP / 32 Atk / 2 SpD
Adamant Nature
- Fake Out
- Parting Shot
- Flare Blitz
- Helping Hand""",
    regulation="M-C",
)
print(pokemon.info())
print(export_showdown_pokemon(pokemon))
```

Only fields represented by the package are supported. Pokémon are fixed at
the selected battle logic's level (50 for the current regulations). Ability
is retained as set metadata and is not currently applied in battle calculations.

## Custom base stats

Load a roster Pokémon as usual, then use `set_bases` to change one or more of
its six base stats. Each supplied value must be a positive integer. The
corresponding battle stat is recalculated using the selected battle logic,
existing stat training, nature, and stat stage. Custom
base stats do not make a species legal.

For example, this creates a customized Incineroar with a base value of 100 in
every stat. At the default settings, its HP becomes 175 and each other battle
stat becomes 120:

```python
from pyvgc import load_regulation

incineroar = load_regulation("M-C").load_pokemon(
    "Incineroar",
    nickname="SylvallyIncineroar",
)
incineroar.set_bases({
    "hp": 100,
    "attack": 100,
    "defense": 100,
    "special_attack": 100,
    "special_defense": 100,
    "speed": 100,
})
print(incineroar.base_stats)
print(incineroar.info())
```

## Spread moves in doubles

Each bundled move records whether it targets multiple Pokémon in doubles.
When a damaging `Move` is passed to a damage calculation, its spread
classification is used automatically. Use `spread=True` or `spread=False` to
override it. Calculations using only raw power and type parameters are
single-target unless `spread=True` is supplied. Singles battle logic has no
spread modifier, so move metadata `spread` values are ignored.

## Known discrepancy

A damage calculation for a 32-HP-trained Incineroar hit by an Adamant,
untrained Excadrill's Rock Slide has differed from the nerd-of-now calculator:
this package reported `66, 66, 66, 68, 68, 70, 70, 70, 72, 72, 74, 74, 74,
76, 76, 78`, while that calculator reported `68, 68, 68, 70, 70, 72, 72, 72,
74, 74, 76, 76, 76, 78, 78, 80`. The cause has not yet been established.

## Team similarity analysis

Compare six-Pokémon teams represented as `Pokemon` objects or as mappings
containing `name`, `ability`, `item`, `nature`, and `moves`. The score is a
similarity score (higher means more similar), with 102 for identical teams.

`pairwise_score_matrix` builds a matrix from teams keyed by an identifier;
`find_team_pairs_by_score` finds exact-score pairs, and
`group_identical_teamplayers` groups players whose teams score 102, the maximum
score for identical teams.

You can check an example of this in the "showcases" folder.

## AI / Additional Sources Disclaimer

Current development is assisted by the VSCode Copilot Plugin, which settled on GPT-5.6-Luna.

Bundled battle-item reference data with effect descriptions crawled from [Serebii's ItemDex](https://www.serebii.net/itemdex/).

Damage calculations are contrasted against the nerd of now calculator:
 - [https://nerd-of-now.github.io/NCP-VGC-Damage-Calculator/](https://nerd-of-now.github.io/NCP-VGC-Damage-Calculator/)