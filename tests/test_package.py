import csv
import sys
import unittest
from importlib import resources
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pyvgc import (
    CHAMPIONS_SINGLES,
    Move,
    Pokemon,
    __version__,
    calculate_damage,
    export_showdown_pokemon,
    get_battle_logic,
    get_item,
    get_move,
    get_movepool_for_pokemon,
    get_pokemon_for_move,
    import_showdown_pokemon,
    load_regulation,
    pokemon_with_ability,
    regulation_description,
    signature_moves,
)


class PackageTests(unittest.TestCase):

    def test_showdown_sets_import_and_export_supported_fields(self):
        """Showdown set fields round-trip through a regulation-bound Pokémon."""
        showdown_set = """dummy (Incineroar) @ Sitrus Berry
Ability: Intimidate
Level: 50
EVs: 32 HP / 32 Atk / 2 SpD
Adamant Nature
- Fake Out
- Parting Shot
- Flare Blitz
- Helping Hand"""

        showdown_set_2 = """Nick (Archaludon) @ Leftovers
        Ability: Stamina
        Level: 50
        EVs: 2 HP / 32 SpA / 32 Spe
        Timid Nature
        - Dragon Pulse
        - Electro Shot
        - Protect
        - Snarl"""

        pokemon2 = import_showdown_pokemon(showdown_set_2, regulation="M-C")
        print("imported", pokemon2.info())
        datarch = export_showdown_pokemon(pokemon2)
        print(datarch)

        my_archaludon = Pokemon.load("Archaludon", regulation="M-C",item="Leftovers",
                                  stat_training=
                                  {"hp": 2, "attack": 0, "defense": 0,
                                   "special_attack": 32, "special_defense": 0, "speed": 32},
                                   nature="Modest",
                                   moveset=("Dragon Pulse", "Electro Shot", "Protect", "Flash Cannon"),
                                   nickname="Nick",
                                   ability="Stalwart")
        print("--------------start-------------------")
        print(my_archaludon.info())
        print(export_showdown_pokemon(my_archaludon))
        print("--------------end-------------------")

        pokemon = import_showdown_pokemon(showdown_set, regulation="M-C")

        self.assertEqual(pokemon.name, "Incineroar")
        self.assertEqual(pokemon.nickname, "dummy")
        self.assertEqual(pokemon.ability, "Intimidate")
        self.assertEqual(pokemon.regulation, "M-C")
        self.assertEqual(pokemon.get_item(), "Sitrus Berry")
        self.assertEqual(
            dict(pokemon.stat_training),
            {
                "hp": 32,
                "attack": 32,
                "defense": 0,
                "special_attack": 0,
                "special_defense": 2,
                "speed": 0,
            },
        )
        self.assertEqual(pokemon.nature, "Adamant")
        self.assertEqual(
            tuple(move.name for move in pokemon.moveset),
            ("Fake Out", "Parting Shot", "Flare Blitz", "Helping Hand"),
        )
        self.assertEqual(export_showdown_pokemon(pokemon), showdown_set)

        sneasler = import_showdown_pokemon(
            """Sneasler @ White Herb
Ability: Unburden
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Adamant Nature
- Fake Out
- Close Combat
- Dire Claw
- Protect""",
            regulation="M-C",
        )
        self.assertEqual(sneasler.nickname, None)
        self.assertEqual(
            export_showdown_pokemon(sneasler),
            """Sneasler @ White Herb
Ability: Unburden
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Adamant Nature
- Fake Out
- Close Combat
- Dire Claw
- Protect""",
        )

    def test_showdown_item_is_optional(self):
        """A Showdown set without an item imports and exports without one."""
        showdown_set = """Sneasler
Ability: Unburden
Level: 50
EVs: 2 HP / 32 Atk / 32 Spe
Adamant Nature
- Fake Out
- Close Combat
- Dire Claw
- Protect"""

        pokemon = import_showdown_pokemon(showdown_set, regulation="M-C")

        self.assertIsNone(pokemon.get_item())
        self.assertEqual(export_showdown_pokemon(pokemon), showdown_set)

    def test_showdown_import_rejects_unsupported_or_invalid_fields(self):
        """Showdown import reports fields and values the model cannot support."""
        with self.assertRaisesRegex(ValueError, "Only level 50"):
            import_showdown_pokemon(
                "Incineroar\nLevel: 100",
                regulation="M-C",
            )
        with self.assertRaisesRegex(ValueError, "Unsupported Showdown field"):
            import_showdown_pokemon(
                "Incineroar\nTera Type: Fire",
                regulation="M-C",
            )
        with self.assertRaisesRegex(ValueError, "unavailable to Incineroar"):
            import_showdown_pokemon(
                "Incineroar\nAbility: Unburden",
                regulation="M-C",
            )
        with self.assertRaisesRegex(ValueError, "total points"):
            import_showdown_pokemon(
                "Incineroar\nEVs: 32 HP / 32 Atk / 3 Spe",
                regulation="M-C",
            )

    def test_package_exposes_current_version(self):
        """The package exposes the declared distribution version."""
        self.assertEqual(__version__, "0.0.3.1")

    def test_regulation_representation_is_concise(self):
        """Loaded regulations do not print their complete data mappings."""
        regulation = load_regulation("M-C")

        self.assertEqual(
            str(regulation),
            "RegulationData(name='M-C', platform='Cartridge', "
            "pokemon=403, items=166, moves=507)",
        )
        self.assertEqual(repr(regulation), str(regulation))

    def test_pokemon_movepool_requires_an_explicit_regulation(self):
        """A Pokémon without a regulation cannot implicitly select a movepool."""
        pokemon = Pokemon.load("Incineroar")

        with self.assertRaisesRegex(ValueError, "regulation is required"):
            pokemon.movepool

        explicitly_bound = Pokemon.load("Incineroar", regulation="M-B")
        self.assertEqual(explicitly_bound.regulation, "M-B")
        self.assertEqual(
            explicitly_bound.movepool,
            get_movepool_for_pokemon("Incineroar", "M-B"),
        )

        regulation_bound = load_regulation("M-A").load_pokemon("Incineroar")
        self.assertEqual(regulation_bound.regulation, "M-A")
        self.assertEqual(
            regulation_bound.movepool,
            get_movepool_for_pokemon("Incineroar", "M-A"),
        )

    def test_pokemon_moveset_can_be_empty_or_contain_up_to_four_moves(self):
        """A moveset is empty by default and stores legal Move objects."""
        regulation = load_regulation("M-C")
        pokemon = regulation.load_pokemon("Incineroar")
        self.assertEqual(pokemon.moveset, ())

        pokemon.moveset = (
            "Fake Out",
            "Flamethrower",
            "Darkest Lariat",
            "Protect",
        )
        self.assertEqual(
            [move.name for move in pokemon.moveset],
            ["Fake Out", "Flamethrower", "Darkest Lariat", "Protect"],
        )
        self.assertTrue(all(isinstance(move, Move) for move in pokemon.moveset))
        self.assertEqual(
            pokemon.info()["moveset"],
            ("Fake Out", "Flamethrower", "Darkest Lariat", "Protect"),
        )

        defender = regulation.load_pokemon("Venusaur")
        rolls = regulation.battle_logic.calculate_damage(
            pokemon,
            defender,
            move=pokemon.moveset[1],
            percentage=False,
        )
        self.assertEqual(len(rolls["normal"]), 16)

        pokemon.set_moveset(())
        self.assertEqual(pokemon.moveset, ())

        initialized = regulation.load_pokemon(
            "Incineroar", moveset=(get_move("Protect"),)
        )
        self.assertEqual(
            tuple(move.name for move in initialized.moveset),
            ("Protect",),
        )

    def test_pokemon_moveset_rejects_more_than_four_or_unlearnable_moves(self):
        """Movesets cannot exceed four moves or include moves outside a movepool."""
        pokemon = load_regulation("M-C").load_pokemon("Incineroar")

        with self.assertRaisesRegex(ValueError, "at most four"):
            pokemon.set_moveset((
                "Fake Out",
                "Protect",
                "Crunch",
                "Flamethrower",
                "Acrobatics",
            ))
        with self.assertRaisesRegex(ValueError, "not in .* movepool"):
            pokemon.set_moveset(("Follow Me",))
        with self.assertRaisesRegex(ValueError, "duplicate move"):
            pokemon.set_moveset(("Protect", "protect"))

    def test_move_lookup_returns_required_attributes(self):
        """Move lookup returns category, accuracy, power, type, and PP."""
        move = get_move("Acid Spray")

        self.assertEqual(move.category, "Special")
        self.assertEqual(move.accuracy, 100)
        self.assertEqual(move.base_power, 40)
        self.assertEqual(move.type, "Poison")
        self.assertEqual(move.pp, 20)

    def test_move_records_identify_spread_targets(self):
        """Bundled move models retain doubles spread-target metadata."""
        for move_name in ("Rock Slide", "Surf", "Earthquake", "Teeter Dance"):
            with self.subTest(move=move_name):
                self.assertTrue(get_move(move_name).is_spread)
        for move_name in ("Flamethrower", "Helping Hand", "Protect"):
            with self.subTest(move=move_name):
                self.assertFalse(get_move(move_name).is_spread)

        for regulation_name in ("M-A", "M-B", "M-C"):
            regulation = load_regulation(regulation_name)
            for move in regulation.moves:
                self.assertEqual(move.is_spread, get_move(move.name).is_spread)

    def test_move_database_matches_current_champions_snapshot(self):
        """The move CSV includes the complete current Champions move list."""
        move_csv = resources.files("pyvgc.data").joinpath(
            "move_templates.csv"
        )
        with move_csv.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 512)
        self.assertIn("IsSpread", rows[0])
        self.assertTrue(all(
            row["IsSpread"] in {"true", "false"} for row in rows
        ))
        self.assertEqual(
            len({row["MoveName"].casefold() for row in rows}),
            len(rows),
        )
        self.assertIn("Revival Blessing", {row["MoveName"] for row in rows})
        self.assertEqual(get_move("Revival Blessing").category, "Status")
        self.assertIsNone(get_move("Revival Blessing").base_power)
        self.assertIsNone(get_move("Revival Blessing").accuracy)
        self.assertEqual(get_move("Revival Blessing").pp, 1)

        movepool_data = resources.files("pyvgc.data").joinpath(
            "regulations", "m_c", "movepools.csv"
        )
        with movepool_data.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))
        pawmot = next(row for row in rows if row["PokemonName"] == "Pawmot")
        self.assertIn("Revival Blessing", pawmot["Moves"].split(";"))

    def test_always_hit_and_status_moves_use_none_for_unimplemented_values(self):
        """Always-hit accuracy and Status base power use explicit None values."""
        move = get_move("Aerial Ace")
        status = get_move("Protect")

        self.assertIsNone(move.accuracy)
        self.assertEqual(move.base_power, 60)
        self.assertEqual(status.category, "Status")
        self.assertIsNone(status.base_power)
        self.assertFalse(status.is_spread)

    def test_movepool_lookups_are_alphabetical_and_bidirectional(self):
        """Pokémon-to-move and move-to-Pokémon lookups use cached indexes."""
        moves = get_movepool_for_pokemon("Venusaur", regulation="M-C")
        users = get_pokemon_for_move("Acid Spray", regulation="M-C")

        self.assertEqual([move.name for move in moves], sorted(
            (move.name for move in moves), key=str.casefold
        ))
        self.assertIn("Acid Spray", {move.name for move in moves})
        self.assertIn("Venusaur", users)

        older_moves = get_movepool_for_pokemon("Venusaur", regulation="M-A")
        older_users = get_pokemon_for_move("Acid Spray", regulation="M-A")
        self.assertEqual(
            {move.name for move in older_moves},
            {move.name for move in moves},
        )
        self.assertNotEqual(older_users, users)

    def test_battle_item_descriptions_are_present_in_all_snapshots(self):
        """Item descriptions are present in master and snapshot CSV files."""
        master_items = resources.files("pyvgc.data").joinpath("battle_items.csv")
        with master_items.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        self.assertIn("Description", rows[0])
        self.assertTrue(all(row["Description"].strip() for row in rows))
        descriptions = {row["ItemName"]: row["Description"] for row in rows}
        for regulation in ("m_a", "m_b", "m_c"):
            path = resources.files("pyvgc.data").joinpath(
                "regulations", regulation, "items.csv"
            )
            with path.open("r", encoding="utf-8", newline="") as file:
                snapshot_rows = list(csv.DictReader(file))
            self.assertTrue(all(row["Description"].strip() for row in snapshot_rows))
            self.assertTrue(all(
                descriptions[row["ItemName"]] == row["Description"]
                for row in snapshot_rows
            ))

    def test_regulation_loaders_apply_the_selected_battle_logic(self):
        """Regulations scope legal content and expose their battle rules."""
        regulation = load_regulation("M-C")
        pokemon = regulation.load_pokemon("Incineroar")

        self.assertEqual(regulation.battle_logic, get_battle_logic(
            "Cartridge-Champions-Release-2026"
        ))
        self.assertEqual(pokemon.name, "Incineroar")
        self.assertEqual(regulation.get_item("Charcoal").name, "Charcoal")
        self.assertEqual(regulation.get_move("Protect").name, "Protect")
        self.assertTrue(regulation.get_movepool_for_pokemon("Incineroar"))

        with self.assertRaises(KeyError):
            regulation.load_pokemon("Not a Pokémon")

    def test_regulations_support_shared_battle_logics(self):
        """Pokémon from different regulations work with a shared battle logic."""
        regulation_names = ("M-A", "M-B", "M-C")
        logic_names = (
            "Cartridge-Champions-Release-2026",
            "Simulator-Champions-Release-2026",
            "Champions-Singles-2026",
        )

        for logic_name in logic_names:
            regulations = {
                name: load_regulation(name, battle_logic=logic_name)
                for name in regulation_names
            }
            attackers = {
                name: regulation.load_pokemon("Incineroar")
                for name, regulation in regulations.items()
            }
            defenders = {
                name: regulation.load_pokemon("Venusaur")
                for name, regulation in regulations.items()
            }

            for attacker in attackers.values():
                for defender in defenders.values():
                    rolls = calculate_damage(
                        attacker,
                        defender,
                        power=40,
                        move_type="Fire",
                    )
                    self.assertTrue(rolls["normal"])

    def test_regulation_csv_selects_simulator_logic(self):
        """A regulation can load the simulator-specific battle logic."""
        regulation = load_regulation("M-C", platform="Simulator")

        self.assertEqual(regulation.platform, "Simulator")
        self.assertEqual(
            regulation.battle_logic,
            get_battle_logic("Simulator-Champions-Release-2026"),
        )
        self.assertEqual(
            regulation.load_pokemon("Incineroar").battle_logic,
            regulation.battle_logic,
        )

    def test_regulation_can_override_battle_logic(self):
        """A regulation can bind its data to an explicit battle logic."""
        regulation = load_regulation(
            "M-C",
            battle_logic="Champions-Singles-2026",
        )
        attacker = regulation.load_pokemon("Incineroar")
        defender = regulation.load_pokemon("Venusaur")

        self.assertIs(regulation.battle_logic, CHAMPIONS_SINGLES)
        self.assertIs(attacker.battle_logic, CHAMPIONS_SINGLES)
        self.assertIs(defender.battle_logic, CHAMPIONS_SINGLES)
        self.assertEqual(
            regulation.battle_logic.calculate_damage(
                attacker,
                defender,
                power=40,
                move_type="Fire",
            )["normal"],
            calculate_damage(
                attacker,
                defender,
                power=40,
                move_type="Fire",
            )["normal"],
        )

    def test_regulation_accepts_battle_logic_instance(self):
        """A regulation preserves an explicitly supplied logic instance."""
        regulation = load_regulation("M-C", battle_logic=CHAMPIONS_SINGLES)

        self.assertIs(regulation.battle_logic, CHAMPIONS_SINGLES)
        self.assertIs(
            regulation.load_pokemon("Incineroar").battle_logic,
            CHAMPIONS_SINGLES,
        )

    def test_regulation_indexes_are_reused_for_logic_overrides(self):
        """Lookup indexes survive creation of a logic-specific snapshot."""
        regulation = load_regulation("M-C")
        singles = load_regulation("M-C", battle_logic=CHAMPIONS_SINGLES)

        self.assertIs(regulation._pokemon_index, singles._pokemon_index)
        self.assertIs(regulation._move_index, singles._move_index)
        self.assertIs(
            regulation._movepools_by_pokemon,
            singles._movepools_by_pokemon,
        )
        self.assertIs(regulation._pokemon_by_move, singles._pokemon_by_move)
        self.assertIs(
            regulation._signature_move_index,
            singles._signature_move_index,
        )
        self.assertIs(regulation.move("pRoTeCt"), regulation._move_index["protect"])
        self.assertIs(
            regulation.get_movepool_for_pokemon("incineroar"),
            get_movepool_for_pokemon("Incineroar", "M-C"),
        )
        self.assertEqual(
            regulation._pokemon_by_move["follow me"],
            get_pokemon_for_move("Follow Me", "M-C"),
        )
        self.assertEqual(
            singles.load_pokemon("  incineroar ").name,
            "Incineroar",
        )

    def test_public_lookups_reject_invalid_names(self):
        """Public name-based lookups reject empty and non-string values."""
        with self.assertRaises(ValueError):
            get_move("")
        with self.assertRaises(ValueError):
            get_move(None)
        with self.assertRaises(ValueError):
            get_movepool_for_pokemon("", "M-C")
        with self.assertRaises(ValueError):
            get_item(None)
        with self.assertRaises(ValueError):
            load_regulation("M-C", platform=None)
        with self.assertRaises(TypeError):
            load_regulation("M-C", battle_logic=object())

    def test_pokemon_with_ability_returns_case_insensitive_matches(self):
        """Ability queries return sorted forms from the selected regulation."""
        matches = pokemon_with_ability("M-B", " intimidate ")

        self.assertEqual(matches, tuple(sorted(matches, key=str.casefold)))
        self.assertIn("Arbok", matches)
        self.assertIn("Arcanine", matches)
        self.assertIn("Arcanine-Hisuian", matches)

    def test_pokemon_with_ability_rejects_empty_names(self):
        """Ability queries reject empty and non-string ability names."""
        with self.assertRaises(ValueError):
            pokemon_with_ability("M-B", "")
        with self.assertRaises(ValueError):
            pokemon_with_ability("M-B", None)

    def test_regulation_description_returns_one_summary_line(self):
        """Regulation description reports Pokémon, item, and move totals."""
        self.assertEqual(
            regulation_description("M-C"),
            "Pokémon: 403, Items: 166, Moves: 507",
        )

    def test_signature_moves_count_forms_independently(self):
        """Signature moves group variants and return every learning form."""
        signature = signature_moves("M-C")
        self.assertIs(signature, signature_moves("M-C"))

        self.assertIn(("Apple Acid", "Appletun"), signature)
        self.assertIn(("Aqua Step", "Quaquaval"), signature)
        decorate_users = {
            pokemon_name
            for move_name, pokemon_name in signature
            if move_name == "Decorate"
        }
        self.assertEqual(decorate_users, {
            "Alcremie",
            "Alcremie-Caramel-Swirl",
            "Alcremie-Lemon-Cream",
            "Alcremie-Matcha-Cream",
            "Alcremie-Mint-Cream",
            "Alcremie-Rainbow-Swirl",
            "Alcremie-Ruby-Cream",
            "Alcremie-Ruby-Swirl",
            "Alcremie-Salted-Cream",
        })
        self.assertEqual(
            signature,
            tuple(sorted(
                signature,
                key=lambda pair: (pair[0].casefold(), pair[1].casefold()),
            )),
        )

if __name__ == "__main__":
    unittest.main()
