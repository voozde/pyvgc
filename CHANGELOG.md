# Pokémon Champions Data Science Package

# Dates use the YYYY-MM-DD format.

- 2026-11-03 (0.0.3, current release)
    - Enable importing and exporting regulation-legal Pokémon Showdown sets.

- 2026-11-03 (0.0.2.6, current release)
    - Renamed regulation learnsets to movepools and added Pokémon movesets of up
      to four regulation-legal moves.
    - Allowed equipped moves to be passed directly into damage calculations.

- 2026-11-02 (0.0.2.5)
    - Bind loaded Pokémon to their regulation for move lookups.
    - Consolidate regulation movepool indexes and avoid eager circular imports.

- 2026-11-02 (0.0.2.4, current release)
    - Updated package version metadata.

- 2026-11-02 (0.0.2.3, current release)
    - Updated the package version metadata.

- 2026-11-02 (0.0.2.1 release)
    - Added separate `CHAMPIONS_SINGLES` battle logic with singles screen
      modifiers; Cartridge and Simulator remain doubles defaults.
    - Added Pokémon movepool and move-user lookup utility functions.
    - Fixed various code issues and improved documentation.

- 2026-11-01 (0.0.1, first pypi test release)
    - Basic Python package functionality and structure established.
        - Pending reviews and improvements; 0.1 should be the first stable release.
        - Future versions are planned to be open source with a stable github implementation
    - Documented all functions and added explicit validation for missing type
      charts.
    - Initial damage formula added
        -> Does not currently consider abilities or items in damage calculation (immunities and others)
        -> All around, extremely basic and needs to be improved.
    - Support for stat boosts.
    - Added move, movepool, and Pokémon-for-move lookups.
    - Added independent `Cartridge-Champions-Release-2026` and
      `Simulator-Champions-Release-2026` battle logics.
    - Added named `BattleLogic` versions and regulation-scoped loaders.
    - Added validated Pokémon type getters/setters for in-battle type changes.
    - Added held-item getters/setters; item effects remain descriptive only.
    - Added concise Serebii-sourced battle item descriptions to the master
      item table and every regulation item snapshot
        
