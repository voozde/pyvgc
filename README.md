# PYVGC

PYVGC is a Python package for basic Pokémon Champions-based data science.
It is currently meant for Python 3.9 and newer, without runtime dependencies.

You can install it with pip
  -  `pip install pyvgc`

You may consult its official pypi page at [https://pypi.org/project/pyvgc/](https://pypi.org/project/pyvgc/)

It requires only a Python3.9+ environment and the standard library. It is currently in alpha development, but it can be used for basic Pokémon data science and damage calculations.

The current version supports the current Pokémon Champions regulations (m-a,m-b and m-c)

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

# AI / Additional Sources Disclaimer

Current development is assisted by the VSCode Copilot Plugin, which settled on GPT-5.6-Luna.

Bundled battle-item reference data with effect descriptions crawled from [Serebii's ItemDex](https://www.serebii.net/itemdex/).

Current development is contrasted against the nerd of now calculator:
 - [https://nerd-of-now.github.io/NCP-VGC-Damage-Calculator/](https://nerd-of-now.github.io/NCP-VGC-Damage-Calculator/)