import json
from pathlib import Path

import pyvgc

regulation_mc_doubles = pyvgc.load_regulation(
    "M-C",
    battle_logic=pyvgc.CARTRIDGE_CHAMPIONS_RELEASE_2026,
)

tyranitar = regulation_mc_doubles.load_pokemon("Tyranitar",
                                                      nature="Jolly",
                                                      moveset=["Rock Slide", "Knock Off", "Protect", "Dragon Dance"],
                                                      item="Tyranitarite",
                                                      ability="Sand Stream",)
print(tyranitar.info())

gholdengo = regulation_mc_doubles.load_pokemon("Gholdengo",
                                                    nature="Modest",
                                                    moveset=["Make It Rain", "Shadow Ball",
                                                             "Protect", "Nasty Plot"],
                                                    item="Life Orb",
                                                    ability="Good as Gold",)

sinistcha = regulation_mc_doubles.load_pokemon("Sinistcha",
                                                      nature="Bold",
                                                      moveset=["Matcha Gotcha", "Rage Powder", "Strength Sap",
                                                               "Protect"],
                                                    item="Rocky Helmet",
                                                    ability="Hospitality",)

staraptor = regulation_mc_doubles.load_pokemon("Staraptor",
                                                    nature="Jolly",
                                                    moveset=["Brave Bird", "Close Combat",
                                                             "Tailwind", "Protect"],
                                                    item="Staraptite",
                                                    ability="Intimidate",)

milotic = regulation_mc_doubles.load_pokemon("Milotic",
                                                nature="Calm",
                                                moveset=["Scald", "Icy Wind", "Ice Beam", "Protect"],
                                                item="Leftovers",
                                                ability="Competitive",)

excadrill = regulation_mc_doubles.load_pokemon("Excadrill",
                                                nature="Adamant",
                                                moveset=["Rock slide", "High Horsepower", "Iron Head", "Protect"],
                                                item="Focus Sash",
                                                ability="Sand Rush",)

mega_tyranitar = regulation_mc_doubles.load_pokemon("Tyranitar-Mega",
                                                      nature="Jolly",
                                                      moveset=["Rock Slide", "Knock Off", "Protect", "Dragon Dance"],
                                                      item="Tyranitarite",
                                                      ability="Sand Stream",)

mega_staraptor = regulation_mc_doubles.load_pokemon("Staraptor-Mega",
                                                    nature="Jolly",
                                                    moveset=["Brave Bird", "Close Combat",
                                                             "Tailwind", "Protect"],
                                                    item="Staraptite",
                                                    ability="Contrary",)

print(mega_staraptor.info())
javier_varela_gdansk = [tyranitar, gholdengo, sinistcha, staraptor, milotic, excadrill,
                        mega_tyranitar, mega_staraptor]
team_to_analyze = javier_varela_gdansk

for pokemon in javier_varela_gdansk:
    print(pokemon.name,"-----",pokemon.info()['stats']['attack'])
    #print("\n")

for pokemon in javier_varela_gdansk:
    print(pyvgc.export_showdown_pokemon(pokemon))
    print("\n")

dummy_incineroar = regulation_mc_doubles.load_pokemon(
    "Incineroar",
    stat_training={"hp": 32, "attack": 2, "defense": 16,
                   "special_attack": 0, "special_defense": 15, "speed": 1},
    nature="Calm",
    ability="Blaze",
)

print("dummy_incineroar stats:",dummy_incineroar.info()['stats'])
for pokemon in team_to_analyze:
    #print("\n-------")
    for move in pokemon.moveset:
        if move.base_power is None or move.category == "Status":
            continue
        damage = regulation_mc_doubles.battle_logic.calculate_damage(
            pokemon,
            dummy_incineroar,
            move=move,
        )
        #Ohko threats
        print(move.name, "damage against Incineroar:", damage)
        ohko = [x for x in damage["normal_percentage"] if x >= 100.0]
        if len(ohko) > 0:
            print(pokemon.name, "shows kill pressure on Incineroar with", move.name)
            print("%ko = ", len(ohko)/16*100,"%")

        ohko_crit = [x for x in damage["critical_percentage"] if x >= 100.0]
        if len(ohko_crit) > 0:
            print(pokemon.name, "shows crit-OHKO  pressure on Incineroar with", move.name)
            print("%ko = ", len(ohko_crit)/16*100,"%")

        normal_rolls = damage["normal"]
        two_hit_ko_outcomes = sum(
            first_hit + second_hit >= dummy_incineroar.hp
            for first_hit in normal_rolls
            for second_hit in normal_rolls
        )
        two_hit_ko_chance = (
            two_hit_ko_outcomes / len(normal_rolls) ** 2 * 100
        )
        if two_hit_ko_outcomes:
            print(
                pokemon.name,
                "shows 2HKO pressure on", dummy_incineroar.name, "with",
                move.name,
            )
            print(
                f"%2HKO (assuming both hits land) = {two_hit_ko_chance:.2f}%"
            )
#--------------------------------------------------------------------------------

# Team from https://limitlessvgc.com/teams/7473
# Items are transcribed from the item icons and their displayed names on the
# team page; they are not included in its copy-to-clipboard text.
kingambit = regulation_mc_doubles.load_pokemon(
    "Kingambit",
    nature="Adamant",
    moveset=["Kowtow Cleave", "Iron Head", "Sucker Punch", "Low Kick"],
    item="Chople Berry",
    ability="Defiant",
)

sneasler = regulation_mc_doubles.load_pokemon(
    "Sneasler",
    nature="Adamant",
    moveset=["Close Combat", "Gunk Shot", "Rock Slide", "Protect"],
    item="White Herb",
    ability="Unburden",
)

salamence = regulation_mc_doubles.load_pokemon(
    "Salamence",
    nature="Modest",
    moveset=["Hyper Voice", "Draco Meteor", "Flamethrower", "Protect"],
    item="Salamencite",
    ability="Intimidate",
)

basculegion = regulation_mc_doubles.load_pokemon(
    "Basculegion",
    nature="Jolly",
    moveset=["Wave Crash", "Last Respects", "Aqua Jet", "Protect"],
    item="Life Orb",
    ability="Adaptability",
)

charizard = regulation_mc_doubles.load_pokemon(
    "Charizard",
    nature="Modest",
    moveset=["Heat Wave", "Weather Ball", "Solar Beam", "Protect"],
    item="Charizardite Y",
    ability="Blaze",
)

whimsicott = regulation_mc_doubles.load_pokemon(
    "Whimsicott",
    nature="Timid",
    moveset=["Moonblast", "Tailwind", "Encore", "Protect"],
    item="Focus Sash",
    ability="Prankster",
)

charizard_mega_y = regulation_mc_doubles.load_pokemon(
    "Charizard-Mega-Y",
    nature="Modest",
    moveset=["Heat Wave", "Weather Ball", "Solar Beam", "Protect"],
    item="Charizardite Y",
    ability="Drought",
)

salamence_mega = regulation_mc_doubles.load_pokemon(
    "Salamence-Mega",
    nature="Modest",
    moveset=["Hyper Voice", "Draco Meteor", "Flamethrower", "Protect"],
    item="Salamencite",
    ability="Aerilate",
)

derbeste_gdansk_2026 = [
    kingambit,
    sneasler,
    salamence,
    salamence_mega,
    basculegion,
    charizard,
    charizard_mega_y,
    whimsicott,
]

for pokemon in derbeste_gdansk_2026:
    print(pokemon.name, "-----", pokemon.info()["stats"]["attack"])

for pokemon in derbeste_gdansk_2026:
    print(pyvgc.export_showdown_pokemon(pokemon))
    print()

print("dummy_incineroar stats:", dummy_incineroar.info()["stats"])
for pokemon in derbeste_gdansk_2026:
    for move in pokemon.moveset:
        if move.base_power is None or move.category == "Status":
            continue
        damage = regulation_mc_doubles.battle_logic.calculate_damage(
            pokemon,
            dummy_incineroar,
            move=move,
        )
        print(move.name, "damage against Incineroar:", damage)
        ohko = [roll for roll in damage["normal_percentage"] if roll >= 100.0]
        if ohko:
            print(pokemon.name, "shows kill pressure on Incineroar with", move.name)
            print("%ko = ", len(ohko) / 16 * 100, "%")

        ohko_crit = [
            roll for roll in damage["critical_percentage"] if roll >= 100.0
        ]
        if ohko_crit:
            print(
                pokemon.name,
                "shows crit-OHKO pressure on Incineroar with",
                move.name,
            )
            print("%ko = ", len(ohko_crit) / 16 * 100, "%")

        normal_rolls = damage["normal"]
        two_hit_ko_outcomes = sum(
            first_hit + second_hit >= dummy_incineroar.hp
            for first_hit in normal_rolls
            for second_hit in normal_rolls
        )
        if two_hit_ko_outcomes:
            two_hit_ko_chance = (
                two_hit_ko_outcomes / len(normal_rolls) ** 2 * 100
            )
            print(
                pokemon.name,
                "shows 2HKO pressure on",
                dummy_incineroar.name,
                "with",
                move.name,
            )
            print(
                f"%2HKO (assuming both hits land) = {two_hit_ko_chance:.2f}%"
            )

pyvgc.compare_team_distance(
    javier_varela_gdansk[0:6],
    derbeste_gdansk_2026[0:6],
)

# Every player above the standings page's "Day 2 end" divider (ranks 1-110).
# https://standings.limitlessvgc.com/0044/standings
# Team sets are transcribed from the linked player team-list pages.
_GDANSK_DAY_2_DATA = json.loads(
    (Path(__file__).parent / "showcases" / "gdansk_day_2.json").read_text(
        encoding="utf-8"
    )
)

gdansk_day_2_top20 = {
    entry["rank"]: {"player": entry["player"], "team": entry["team"]}
    for entry in _GDANSK_DAY_2_DATA[0:]
}

print("\nPairwise distance scores for all Gdańsk Day 2 teams")
print("The standings page marks rank 110 as the end of Day 2.")
print("Ranks and players:")
for rank, entry in gdansk_day_2_top20.items():
    print(f"{rank:>3}: {entry['player']}")

score_matrix = pyvgc.pairwise_score_matrix(gdansk_day_2_top20)
team_ranks = list(gdansk_day_2_top20)
column_width = max(4, len(str(max(team_ranks))) + 1)
print("\nDistance matrix (rows/columns use the ranks above):")
print(" " * column_width + "".join(
    f"{rank:>{column_width}}" for rank in team_ranks
))

for rank, scores in score_matrix.items():
    print(f"{rank:>{column_width}}" + "".join(
        f"{scores[other_rank]:>{column_width}}" for other_rank in team_ranks
    ))

score_102_pairs = pyvgc.find_team_pairs_by_score(score_matrix, 102)
print("\nDistinct team pairs scoring 102:")
for rank, other_rank, score in score_102_pairs:
    print(
        f"{rank} ({gdansk_day_2_top20[rank]['player']}) - "
        f"{other_rank} ({gdansk_day_2_top20[other_rank]['player']}): {score}"
    )

score_101_pairs = pyvgc.find_team_pairs_by_score(score_matrix, 101)
print("\nDistinct team pairs scoring 101:")
for rank, other_rank, score in score_101_pairs:
    print(
        f"{rank} ({gdansk_day_2_top20[rank]['player']}) - "
        f"{other_rank} ({gdansk_day_2_top20[other_rank]['player']}): {score}"
    )


score_102_groups = pyvgc.group_identical_teamplayers(score_matrix)
print("\nGroups of players with identical teams (score 102):")
for group in score_102_groups:
    players = ", ".join(
        f"{rank} ({gdansk_day_2_top20[rank]['player']})" for rank in group
    )
    print(players)
