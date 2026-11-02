# PYVGC

PYVGC is a Python package for basic Pokémon Champions-based data science.
It is currently meant for Python 3.9 and newer, without runtime dependencies.

Readme is still in development for basic usage.

Regulations scope legal Pokémon, moves, items, and learnsets, while named
`BattleLogic` instances preserve historical and future rule sets.

Cartridge and Simulator use doubles battle logic by default. The separate `CHAMPIONS_SINGLES` battle logic is available when singles screen behavior is equired, including through `load_regulation("M-C",battle_logic="Champions-Singles-2026")`. 

Loaded Pokémon inherit the regulation's selected battle logic for damage calculations.

In the current version there are three types of logics:
- Cartridge-Champions-Release-2026: This is the logic used in the official Pokémon Champions game. It is the most accurate representation of the game mechanics.
- Simulator-Champions-Release-2026: This is a logic that is used in the simulator. It is the same as Catridge but the idea is to support simulator-only logics.
- Champions-Singles-2026: 
    -> The only difference between the Releases and Singles is the Screen Implementation
    -> 1/2 in singles and 2/3 in doubles.  
- There could be more logics in the future, but for now this is the basic template.
    -> By keeping logics separate we can keep up with future releases or balance changes.
    -> It could be possible to retroactively fit older logics but it is currently out of the scope of the project.

All current development is meant for early implementation. Until 0.1 this package is on alpha development, but it can currently be used for basic Pokémon data science and damage calculations.

Current (Alpha) version provides a basic template for Pokémon data calculations based on Pokémon Champions.

Item effects and regulation item membership are descriptive data only

-> item mechanics are not implemented in damage calculations. 

-> Teams, weather, terrain, and KO-target searches are not part of this MVP. 

-> Regulation snapshots and the single-ability query are available as data utilities; they do not affect damage calculations.

The package is maintained by Voozde. It is currently in development for a Python Package full release.

AI / Additional Sources Disclaimer

-> Current development is assisted by the VSCode Copilot Plugin, which settled on GPT-5.6-Luna.

-> Bundled battle-item reference data with effect descriptions crawled from [Serebii's ItemDex](https://www.serebii.net/itemdex/).