from pyvgc import (
    load_regulation,
    pokemon_with_ability,
    pokemon_with_single_ability,
    regulation_description,
    signature_moves,
    get_pokemon_for_move,
    get_movepool_for_pokemon,
)


if __name__ == "__main__":

    # To initialice a Pokémon, you can do it like this:
    regulation_ma = load_regulation("M-A") #m-a, m-b and m-c currently supported.
    print(regulation_ma)

    # You can specify a Pokémon's nature and stat training, which is a dict of EVs for each stat. 
    # The sum of the values must be <= 66 due to how Pokémon Champions works.
    # You can initialize it without any of these values, just specify the pokémons name
    # You can add a held item but it currently has no effect on any damage calcs.

    # Abilities can be specified but are not yet applied in damage calculations.
    # Their effects can be represented manually through modifiers.

    # You will find some exceptions if you define an "illegal" Pokémon, but they're self-explanatory for the most part.

    dummy = regulation_ma.load_pokemon(
        "Incineroar",
        nature="Modest",
        stat_training={"hp": 32, 
                       "attack": 2, 
                       "defense": 16, 
                       "special_attack": 0, 
                       "special_defense": 3, 
                       "speed": 0}, 
        item="Sitrus Berry",
    )
    dummy.moveset = ("Fake Out", "Flare Blitz", "Darkest Lariat", "Protect")
    # You can specify a moveset of up to 4 moves, but it is not required.
    # If you don't specify it, the Pokémon will have an empty moveset.

    # Print information about the Pokémon, including its stats and moveset.
    print("GaoGaen")
    print("------------------------------------------")
    print(dummy.info())

    print("Moveset:")
    for move in dummy.moveset:
        print(f"Move: {move.name}, Type: {move.type}, Power: {move.base_power}")

    print("Movepool:")
    for move in dummy.movepool:
        print(f"Move: {move.name}, Type: {move.type}, Power: {move.base_power}")

    # Let's initialize a second Pokémon and calculate damage from one to the other.
    target = regulation_ma.load_pokemon(
        "Venusaur",
        nature="Bold",
        stat_training={"hp": 32,
                       "attack": 0,
                       "defense": 32,
                       "special_attack": 0,
                       "special_defense": 2,
                       "speed": 0},
        item="Leftovers"
    )
    print("Venusaur")
    print("------------------------------------------")
    print(target.info())

    print("Damage from Incineroar to Venusaur:")

    # Currently you can specify the power, type of the move, and whether it is a special move or not. 
    # The damage calculation will use the Pokémon's current stats and types

    damage = regulation_ma.battle_logic.calculate_damage(
        dummy,
        target,
        power=120,
        move_type="Fairy",
        special=False,
    )

    for move in dummy.moveset:
        print(f"Move: {move.name}, Type: {move.type}, Power: {move.base_power}")
        if move.base_power is None:
            continue
        damage = regulation_ma.battle_logic.calculate_damage(
            dummy,
            target,
            move=move,
        )
        print(f"Damage from {dummy.name} using {move.name} to {target.name}: {damage}")
    
    # These are examples of some utility functions that can be used to look on the regulation data.
    print("Single-ability Pokémon:", pokemon_with_single_ability("M-B"))
    print("Intimidate users:", pokemon_with_ability("M-C", "Intimidate"))
    print("Regulation M-A contents:", regulation_description("M-A"))
    print("Regulation M-B contents:", regulation_description("M-B"))
    print("Regulation M-C contents:", regulation_description("M-C"))
    print("Signature moves:", signature_moves("M-C"))
    print("Pokémon that learn 'Follow Me' in reg M-C:", get_pokemon_for_move("Follow Me", regulation="M-C"))
    print("Movepool for 'Venusaur' in reg M-C:", get_movepool_for_pokemon("Venusaur", regulation="M-C"))

    # You can also set the Pokémon's stats directly. Currently, this will clear any stat stage increases.
    dummy.set_stats({"attack": 400})
    print(dummy.info())
    

    # You can also set the Pokémon's types directly (supports only 2 types on each Pokémon)
    target.set_types(("Water",))
    print("Attacker:", dummy.info())
    print("Defender:", target.info())
    
    #print("Damage:", damage)
    print("--\n\n\n\n\n-------")
    #print(regulation)

    # In the current version there are three types of logics:
    # Cartridge-Champions-Release-2026: This is the logic used in the official Pokémon Champions game. It is the most accurate representation of the game mechanics.
    # Simulator-Champions-Release-2026: This is a logic that is used in the simulator. It is the same as Catridge but the idea is to support simulator-only logics.
    # Champions-Singles-2026: 
    #  -> The only difference between the Releases and Singles is the Screen Implementation
    #  -> 1/2 in singles and 2/3 in doubles.  
    # There could be more logics in the future, but for now this is the basic template.
    #  -> By keeping logics separate we can keep up with future releases or balance changes.
    #  -> It could be possible to retroactively fit older logics but it is currently out of the scope of the project.

    regulation_mb_doubles = load_regulation("M-A",battle_logic="Cartridge-Champions-Release-2026")
    regulation_mb_singles = load_regulation("M-A",battle_logic="Champions-Singles-2026")

    #print(regulation)
    dummy_singles = regulation_mb_singles.load_pokemon("Incineroar")
    dummy_doubles = regulation_mb_doubles.load_pokemon("Incineroar")
    target_singles = regulation_mb_singles.load_pokemon("Venusaur")
    target_doubles = regulation_mb_doubles.load_pokemon("Venusaur")

    # A Practical Example of the logics implementation
    damage_singles_noscreen = regulation_mb_singles.battle_logic.calculate_damage(
            dummy_singles,
            target_singles,
            power=40,
            move_type="Fire",
            special=False,
            percentage=False,
    )

    damage_singles = regulation_mb_singles.battle_logic.calculate_damage(
            dummy_singles,
            target_singles,
            power=40,
            move_type="Fire",
            special=False,
            reflect=True,
        )
    
    damage_doubles = regulation_mb_doubles.battle_logic.calculate_damage(
            dummy_doubles,
            target_doubles,
            power=40,
            move_type="Fire",
            special=False,
            reflect=True,
    )

    print(damage_singles_noscreen)
    print(damage_singles)
    print(damage_doubles)

    # Lastly, for illustration purposes you could make up your own fake-pokémon and use it, 
    # but you currently need to be roundabout to do it.

    dummy_zacian = regulation_mb_doubles.load_pokemon(
        "Incineroar")
    dummy_zacian.name = "Zacian"
    dummy_zacian.types = ("Fairy", "Steel")
    print(dummy_zacian.info())
    
    #set stats only sets the actual values, not the "base_values". 
    #That is, you set your attack to X, not the base that later on gets added +20
    dummy_zacian.set_stats({
        "hp": 167,
        "attack": 170,
        "defense": 135,
        "special_attack": 100,
        "special_defense": 135,
        "speed": 168
    })

    damage_zacian = regulation_mb_doubles.battle_logic.calculate_damage(
        dummy_zacian,
        target_doubles,
        power=40,
        move_type="Steel",
    )
    print("Madeup Zacian damage rolls",damage_zacian)