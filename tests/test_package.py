import csv
import sys
import unittest
from fractions import Fraction
from importlib import resources
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from pyvgc import (
    BattleLogic,
    CHAMPIONS_SINGLES,
    Pokemon,
    __version__,
    calculate_damage,
    damage_rolls,
    get_battle_logic,
    get_item,
    get_move,
    get_moves_for_pokemon,
    get_pokemon_for_move,
    load_regulation,
    pokemon_with_ability,
    regulation_description,
    signature_moves,
)


class DamageCalculationTests(unittest.TestCase):
    def test_package_exposes_current_version(self):
        """The package exposes the declared distribution version."""
        self.assertEqual(__version__, "0.0.2.5")

    def test_regulation_representation_is_concise(self):
        """Loaded regulations do not print their complete data mappings."""
        regulation = load_regulation("M-C")

        self.assertEqual(
            str(regulation),
            "RegulationData(name='M-C', platform='Cartridge', "
            "pokemon=403, items=166, moves=507)",
        )
        self.assertEqual(repr(regulation), str(regulation))

    @classmethod
    def setUpClass(cls):
        """Load reusable attacker and defender fixtures once."""
        cls.incineroar_base = Pokemon.load("Incineroar")
        cls.venusaur_base = Pokemon.load("Venusaur")



    def test_various_random_rolls_from_nerdofnow(self):
        """Some sanity check rolls directly from the nerdofnow damage calculator."""
        enemy = Pokemon.load("Gengar-Mega",nature="Bold")
        rolls = calculate_damage(
            self.incineroar_base,
            enemy, power=120, move_type="Fire", percentage=False,
        )
        self.assertEqual(rolls["normal"], 
                         [84, 84, 85, 87, 87, 88, 90, 90, 91, 93, 93, 94, 96, 96, 97, 99])

    def test_physical_normal_rolls(self):
        """Physical Fire damage returns the expected 16 normal rolls."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )

        self.assertEqual(rolls["normal"], [
            62, 62, 62, 66, 66, 66, 66, 68,
            68, 68, 68, 72, 72, 72, 72, 74,
        ])

    def test_physical_critical_rolls(self):
        """Physical Fire critical damage returns the expected 16 rolls."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )

        self.assertEqual(rolls["critical"], [
            92, 92, 96, 96, 96, 98, 98, 102,
            102, 102, 104, 104, 104, 108, 108, 110,
        ])

    def test_special_rolls_use_special_stats(self):
        """Special damage uses Special Attack and Special Defense."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", special=True,
            percentage=False,
        )

        self.assertEqual(rolls, {
            "normal": [
                38, 38, 38, 42, 42, 42, 42, 42,
                42, 44, 44, 44, 44, 44, 44, 48,
            ],
            "critical": [
                60, 60, 60, 62, 62, 62, 62, 66,
                66, 66, 66, 68, 68, 68, 68, 72,
            ],
        })

    def test_damage_percentage_rolls_are_returned_by_default(self):
        """Damage percentages are included unless explicitly disabled."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire",
        )

        self.assertEqual(rolls["normal_percentage"], [
            40.0, 40.0, 40.0, 42.58, 42.58, 42.58, 42.58, 43.87,
            43.87, 43.87, 43.87, 46.45, 46.45, 46.45, 46.45, 47.74,
        ])
        self.assertEqual(rolls["critical_percentage"], [
            59.35, 59.35, 61.94, 61.94, 61.94, 63.23, 63.23, 65.81,
            65.81, 65.81, 67.1, 67.1, 67.1, 69.68, 69.68, 70.97,
        ])

    def test_damage_percentages_can_be_disabled(self):
        """Damage-only output omits percentage fields when requested."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )

        self.assertNotIn("normal_percentage", rolls)
        self.assertNotIn("critical_percentage", rolls)

    def test_damage_modifiers_are_disabled_by_default(self):
        """Modifier flags preserve the existing damage results by default."""
        baseline = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            percentage=False,
        )
        explicit = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            percentage=False,
            light_screen=False,
            reflect=False,
            aurora_veil=False,
            helping_hand=False,
            spread=False,
        )

        self.assertEqual(explicit, baseline)

    def test_reflect_reduces_physical_normal_damage(self):
        """Default doubles logic applies the 2/3 screen modifier."""
        self.assertEqual(
            self.incineroar_base.battle_logic.screen_multiplier,
            Fraction(2, 3),
        )
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            percentage=False,
            reflect=True,
        )

        self.assertEqual(rolls["normal"], [41, 41, 41, 44, 44, 44, 44, 45,
                                           45, 45, 45, 48, 48, 48, 48, 49])
        self.assertEqual(rolls["critical"], [
            92, 92, 96, 96, 96, 98, 98, 102,
            102, 102, 104, 104, 104, 108, 108, 110,
        ])

    def test_light_screen_reduces_special_normal_damage(self):
        """Default doubles logic applies the 2/3 Light Screen modifier."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            special=True,
            percentage=False,
            light_screen=True,
        )

        self.assertEqual(rolls["normal"], [25, 25, 25, 28, 28, 28, 28, 28,
                                           28, 29, 29, 29, 29, 29, 29, 32])
        self.assertEqual(rolls["critical"], [
            60, 60, 60, 62, 62, 62, 62, 66,
            66, 66, 66, 68, 68, 68, 68, 72,
        ])

    def test_aurora_veil_reduces_normal_damage(self):
        """Default doubles logic applies the 2/3 Aurora Veil modifier."""
        rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            percentage=False,
            aurora_veil=True,
        )

        self.assertEqual(rolls["normal"], [41, 41, 41, 44, 44, 44, 44, 45,
                                           45, 45, 45, 48, 48, 48, 48, 49])
        self.assertEqual(rolls["critical"], [
            92, 92, 96, 96, 96, 98, 98, 102,
            102, 102, 104, 104, 104, 108, 108, 110,
        ])

        special_rolls = calculate_damage(
            self.incineroar_base,
            self.venusaur_base,
            power=40,
            move_type="Fire",
            special=True,
            percentage=False,
            aurora_veil=True,
        )
        self.assertEqual(special_rolls["normal"], [
            25, 25, 25, 28, 28, 28, 28, 28,
            28, 29, 29, 29, 29, 29, 29, 32,
        ])
        self.assertEqual(special_rolls["critical"], [
            60, 60, 60, 62, 62, 62, 62, 66,
            66, 66, 66, 68, 68, 68, 68, 72,
        ])

    def test_wrong_screen_type_does_not_modify_damage(self):
        """Reflect does not affect special damage or Light Screen physical damage."""
        physical = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", percentage=False, light_screen=True,
        )
        special = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", special=True, percentage=False, reflect=True,
        )

        self.assertEqual(physical["normal"], [62, 62, 62, 66, 66, 66, 66, 68,
                                              68, 68, 68, 72, 72, 72, 72, 74])
        self.assertEqual(special["normal"], [
            38, 38, 38, 42, 42, 42, 42, 42,
            42, 44, 44, 44, 44, 44, 44, 48,
        ])

    def test_helping_hand_increases_damage(self):
        """Helping Hand applies a 1.5x modifier to normal and critical rolls."""
        rolls = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", percentage=False, helping_hand=True,
        )

        self.assertEqual(rolls["normal"], [
            90, 90, 92, 92, 96, 96, 96, 98,
            98, 98, 102, 102, 102, 104, 104, 108,
        ])
        self.assertEqual(rolls["critical"], [
            134, 138, 138, 140, 144, 144, 146, 146,
            150, 150, 152, 152, 156, 156, 158, 162,
        ])

    def test_spread_reduces_damage(self):
        """Spread damage applies a 0.75x modifier to normal and critical rolls."""
        rolls = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", special=True, percentage=False, spread=True,
        )

        self.assertEqual(rolls["normal"], [
            30, 30, 30, 30, 30, 30, 30, 32,
            32, 32, 32, 32, 32, 32, 32, 36,
        ])
        self.assertEqual(rolls["critical"], [
            44, 44, 44, 44, 48, 48, 48, 48,
            48, 48, 50, 50, 50, 50, 50, 54,
        ])

    def test_screens_do_not_stack(self):
        """Multiple applicable screen flags still apply one doubles modifier."""
        combined = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", percentage=False,
            reflect=True, aurora_veil=True,
        )
        reflect_only = calculate_damage(
            self.incineroar_base, self.venusaur_base, power=40,
            move_type="Fire", percentage=False, reflect=True,
        )

        self.assertEqual(combined, reflect_only)

    def test_low_level_damage_rolls_support_modifiers(self):
        """The stat-based damage function supports the same modifiers."""
        rolls = damage_rolls(
            power=40,
            attack=self.incineroar_base.attack,
            defense=self.venusaur_base.defense,
            move_type="Fire",
            attacker_types=self.incineroar_base.types,
            defender_types=self.venusaur_base.types,
            logic=self.incineroar_base.battle_logic,
            helping_hand=True,
            spread=True,
        )

        self.assertEqual(rolls["normal"], [
            66, 68, 68, 68, 72, 72, 72, 72,
            74, 74, 74, 74, 78, 78, 78, 80,
        ])

        screened = damage_rolls(
            power=40,
            attack=self.incineroar_base.attack,
            defense=self.venusaur_base.defense,
            move_type="Fire",
            attacker_types=self.incineroar_base.types,
            defender_types=self.venusaur_base.types,
            logic=self.incineroar_base.battle_logic,
            reflect=True,
        )
        self.assertEqual(screened["normal"], [
            41, 41, 41, 44, 44, 44, 44, 45,
            45, 45, 45, 48, 48, 48, 48, 49,
        ])

    def test_non_immune_damage_rolls_have_a_minimum_of_one(self):
        """Resisted damage is floored at one while type immunity stays zero."""
        logic = self.incineroar_base.battle_logic
        resisted = damage_rolls(
            power=1,
            attack=1,
            defense=10**9,
            move_type="Normal",
            attacker_types=("Normal",),
            defender_types=("Rock", "Steel"),
            logic=logic,
        )
        immune = damage_rolls(
            power=1,
            attack=1,
            defense=10**9,
            move_type="Normal",
            attacker_types=("Normal",),
            defender_types=("Ghost",),
            logic=logic,
        )

        self.assertEqual(resisted["normal"], [1] * 16)
        self.assertEqual(resisted["critical"], [1] * 16)
        self.assertEqual(immune["normal"], [0] * 16)
        self.assertEqual(immune["critical"], [0] * 16)

    def test_singles_logic_uses_half_screen_modifier(self):
        """Singles logic keeps the 1/2 screen modifier."""
        attacker = Pokemon.load("Incineroar", logic=CHAMPIONS_SINGLES)
        defender = Pokemon.load("Venusaur", logic=CHAMPIONS_SINGLES)

        self.assertEqual(CHAMPIONS_SINGLES.screen_multiplier, Fraction(1, 2))
        rolls = CHAMPIONS_SINGLES.calculate_damage(
            attacker,
            defender,
            power=40,
            move_type="Fire",
            percentage=False,
            reflect=True,
        )

        self.assertEqual(rolls["normal"], [
            31, 31, 31, 33, 33, 33, 33, 34,
            34, 34, 34, 36, 36, 36, 36, 37,
        ])

    def test_stat_training_is_applied_when_loaded(self):
        """Training points are applied to loaded level-50 stats."""
        trained = Pokemon.load(
            "Incineroar",
            stat_training={"hp": 32, "attack": 32, "speed": 2},
        )

        self.assertEqual(trained.hp, 202)
        self.assertEqual(trained.attack, 167)
        self.assertEqual(trained.speed, 82)

    def test_stat_training_limits_are_enforced(self):
        """Training rejects per-stat and total allocation violations."""
        with self.assertRaises(ValueError):
            Pokemon.load("Incineroar", stat_training={"attack": 33})

        with self.assertRaises(ValueError):
            Pokemon.load(
                "Incineroar",
                stat_training={"hp": 32, "attack": 32, "speed": 3},
            )

    def test_stats_can_be_set_to_exact_values(self):
        """Direct stat assignments replace current values exactly."""
        pokemon = Pokemon.load("Incineroar", stat_stages={"attack": -1})

        pokemon.set_stats({"attack": 400, "hp": 250})

        self.assertEqual(pokemon.attack, 400)
        self.assertEqual(pokemon.hp, 250)
        self.assertNotIn("attack", pokemon.stat_stages)

    def test_direct_stat_assignments_validate_input(self):
        """Direct stat assignments reject malformed values and names."""
        pokemon = Pokemon.load("Incineroar")

        with self.assertRaises(ValueError):
            pokemon.set_stats({})
        with self.assertRaises(ValueError):
            pokemon.set_stats({"accuracy": 400})
        with self.assertRaises(ValueError):
            pokemon.set_stats({"attack": 0})

    def test_nature_is_applied_after_training(self):
        """Nature modifiers are applied after stat training."""
        trained = Pokemon.load(
            "Incineroar",
            stat_training={"attack": 32, "speed": 2},
            nature="Adamant",
        )

        self.assertEqual(trained.attack, 183)
        self.assertEqual(trained.special_attack, 90)

    def test_nature_does_not_affect_hp(self):
        """Nature modifiers never change HP."""
        neutral = Pokemon.load("Incineroar", nature="Bold")

        self.assertEqual(neutral.hp, 170)

    def test_neutral_nature_does_not_change_stat(self):
        """Neutral natures leave their shared stat unchanged."""
        neutral = Pokemon.load("Incineroar", nature="Hardy")

        self.assertEqual(neutral.attack, 135)

    def test_unknown_nature_is_rejected(self):
        """Unknown nature names are rejected."""
        with self.assertRaises(ValueError):
            Pokemon.load("Incineroar", nature="Champion")

    def test_pokemon_types_can_be_read_and_changed(self):
        """Battle type changes are validated and affect the Pokémon state."""
        pokemon = Pokemon.load("Incineroar")

        self.assertEqual(pokemon.get_types(), ("Fire", "Dark"))
        pokemon.set_types(("Water",))
        self.assertEqual(pokemon.types, ("Water",))
        pokemon.types = ("Grass", "Poison")
        self.assertEqual(pokemon.get_types(), ("Grass", "Poison"))

        with self.assertRaises(ValueError):
            pokemon.set_types(("Unknown",))
        with self.assertRaises(ValueError):
            pokemon.set_types(("Fire", "Fire"))

    def test_pokemon_info_returns_current_battle_state(self):
        """Info reports current stats and mutable battle attributes."""
        pokemon = Pokemon.load("Incineroar", nature="Adamant")
        pokemon.set_types(("Water",))
        pokemon.set_item("Leftovers")

        info = pokemon.info()

        self.assertEqual(info["name"], "Incineroar")
        self.assertEqual(info["types"], ("Water",))
        self.assertEqual(info["item"], "Leftovers")
        self.assertEqual(info["nature"], "Adamant")
        self.assertEqual(info["stats"]["hp"], pokemon.hp)
        self.assertEqual(info["stats"]["attack"], pokemon.attack)

    def test_pokemon_moves_requires_an_explicit_regulation(self):
        """A Pokémon without a regulation cannot implicitly select its moves."""
        pokemon = Pokemon.load("Incineroar")

        with self.assertRaisesRegex(ValueError, "regulation is required"):
            pokemon.moves

        explicitly_bound = Pokemon.load("Incineroar", regulation="M-B")
        self.assertEqual(explicitly_bound.regulation, "M-B")
        self.assertEqual(
            explicitly_bound.moves,
            get_moves_for_pokemon("Incineroar", "M-B"),
        )

        regulation_bound = load_regulation("M-A").load_pokemon("Incineroar")
        self.assertEqual(regulation_bound.regulation, "M-A")
        self.assertEqual(
            regulation_bound.moves,
            get_moves_for_pokemon("Incineroar", "M-A"),
        )

    def test_pokemon_items_can_be_read_and_changed(self):
        """A held item can be assigned, read, and removed."""
        pokemon = Pokemon.load("Incineroar")

        self.assertIsNone(pokemon.get_item())
        pokemon.set_item(" Leftovers ")
        self.assertEqual(pokemon.get_item(), "Leftovers")
        pokemon.set_item(None)
        self.assertIsNone(pokemon.get_item())

        with self.assertRaises(ValueError):
            pokemon.set_item("")
        with self.assertRaises(KeyError):
            pokemon.set_item("Definitely Not An Item")
        with self.assertRaises(KeyError):
            pokemon.set_item(type(get_item("Leftovers"))("Fake", ""))

    def test_pokemon_can_be_initialized_with_an_item(self):
        """Pokémon constructors and loaders accept canonical items."""
        loaded = Pokemon.load("Incineroar", item=" Leftovers ")

        self.assertEqual(loaded.get_item(), "Leftovers")

        with self.assertRaises(KeyError):
            Pokemon.load("Incineroar", item="Not An Item")

        regulation = load_regulation("M-C")
        self.assertEqual(
            regulation.load_pokemon("Incineroar", item="Charcoal").get_item(),
            "Charcoal",
        )

    def test_cartridge_and_simulator_battle_logics_are_registered(self):
        """Cartridge and Simulator expose independent named rule sets."""
        cartridge = get_battle_logic("Cartridge-Champions-Release-2026")
        simulator = get_battle_logic("Simulator-Champions-Release-2026")

        self.assertEqual(cartridge.name, "Cartridge-Champions-Release-2026")
        self.assertEqual(simulator.name, "Simulator-Champions-Release-2026")
        self.assertEqual(simulator.type_chart, cartridge.type_chart)

    def test_battle_logics_use_the_initial_type_chart(self):
        """Registered logics load type effectiveness from the packaged CSV."""
        chart = resources.files("pyvgc.data").joinpath(
            "initial_type_chart.csv"
        )
        with chart.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 18)
        self.assertEqual(
            get_battle_logic(
                "Cartridge-Champions-Release-2026"
            ).type_chart["Fire"]["Grass"],
            2,
        )

    def test_simulator_damage_matches_cartridge_rules(self):
        """Simulator currently matches Cartridge damage rules."""
        cartridge_attacker = Pokemon.load(
            "Incineroar",
            logic=get_battle_logic("Cartridge-Champions-Release-2026"),
        )
        cartridge_defender = Pokemon.load(
            "Venusaur",
            logic=get_battle_logic("Cartridge-Champions-Release-2026"),
        )
        simulator_attacker = Pokemon.load(
            "Incineroar",
            logic=get_battle_logic("Simulator-Champions-Release-2026"),
        )
        simulator_defender = Pokemon.load(
            "Venusaur",
            logic=get_battle_logic("Simulator-Champions-Release-2026"),
        )

        cartridge = calculate_damage(
            cartridge_attacker,
            cartridge_defender,
            power=40,
            move_type="Fire",
            percentage=False,
        )
        simulator = calculate_damage(
            simulator_attacker,
            simulator_defender,
            power=40,
            move_type="Fire",
            percentage=False,
        )

        self.assertEqual(simulator, cartridge)

    def test_battle_logic_calculates_damage_for_its_pokemon(self):
        """Battle logic owns calculations for Pokémon using that logic."""
        logic = get_battle_logic("Cartridge-Champions-Release-2026")
        attacker = Pokemon.load("Incineroar", logic=logic)
        defender = Pokemon.load("Venusaur", logic=logic)

        expected = calculate_damage(
            attacker,
            defender,
            power=40,
            move_type="Fire",
            percentage=False,
        )

        self.assertEqual(
            logic.calculate_damage(
                attacker,
                defender,
                power=40,
                move_type="Fire",
                percentage=False,
            ),
            expected,
        )

    def test_battle_logic_rejects_pokemon_from_another_logic(self):
        """Battle logic rejects Pokémon assigned to a different ruleset."""
        cartridge = get_battle_logic("Cartridge-Champions-Release-2026")
        other_logic = BattleLogic(name="Other")
        attacker = Pokemon.load("Incineroar", logic=other_logic)
        defender = Pokemon.load("Venusaur", logic=other_logic)

        with self.assertRaises(ValueError):
            cartridge.calculate_damage(
                attacker,
                defender,
                power=40,
                move_type="Fire",
            )

    def test_damage_rejects_mixed_battle_logics(self):
        """Damage cannot silently combine stats from different rule sets."""
        attacker = Pokemon.load(
            "Incineroar",
            logic=get_battle_logic("Cartridge-Champions-Release-2026"),
        )
        defender = Pokemon.load(
            "Venusaur",
            logic=BattleLogic(name="Other"),
        )

        with self.assertRaises(ValueError):
            calculate_damage(attacker, defender, power=40, move_type="Fire")

    def test_damage_rejects_equivalent_but_distinct_battle_logics(self):
        """Damage requires the same registered logic instance on both Pokémon."""
        cartridge = get_battle_logic("Cartridge-Champions-Release-2026")
        attacker = Pokemon.load("Incineroar", logic=cartridge)
        defender = Pokemon.load(
            "Venusaur",
            logic=BattleLogic(
                name=cartridge.name,
                type_chart=cartridge.type_chart,
            ),
        )

        with self.assertRaises(ValueError):
            calculate_damage(attacker, defender, power=40, move_type="Fire")

    def test_stat_stages_are_applied_after_nature(self):
        """Positive stages multiply the final trained and natured stat."""
        boosted = Pokemon.load(
            "Incineroar",
            nature="Adamant",
            stat_stages={"attack": 1},
        )

        self.assertEqual(boosted.attack, 222)

    def test_negative_stat_stages_reduce_stats(self):
        """Negative stages reduce stats with the correct floored fraction."""
        lowered = Pokemon.load(
            "Incineroar",
            stat_stages={"speed": -1},
        )

        self.assertEqual(lowered.speed, 53)

    def test_stat_stage_boundaries_are_supported(self):
        """The maximum positive and negative stages use the correct ratios."""
        maximized = Pokemon.load(
            "Incineroar",
            stat_stages={"speed": 6},
        )
        minimized = Pokemon.load(
            "Incineroar",
            stat_stages={"speed": -6},
        )

        self.assertEqual(maximized.speed, 320)
        self.assertEqual(minimized.speed, 20)

    def test_critical_hits_ignore_attacker_stat_decreases(self):
        """Critical damage ignores a negative attacking stat stage."""
        attacker = Pokemon.load("Incineroar", stat_stages={"attack": -1})
        normal = calculate_damage(
            attacker,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )
        unlowered = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )

        self.assertEqual(normal["normal"], [
            42, 42, 42, 42, 44, 44, 44, 44,
            44, 44, 48, 48, 48, 48, 48, 50,
        ])
        self.assertEqual(normal["critical"], unlowered["critical"])

    def test_critical_hits_ignore_defender_stat_increases(self):
        """Critical damage ignores a positive defending stat stage."""
        defender = Pokemon.load("Venusaur", stat_stages={"defense": 1})
        normal = calculate_damage(
            self.incineroar_base,
            defender, power=40, move_type="Fire", percentage=False,
        )
        unboosted = calculate_damage(
            self.incineroar_base,
            self.venusaur_base, power=40, move_type="Fire", percentage=False,
        )

        self.assertEqual(normal["normal"], [
            42, 42, 42, 42, 44, 44, 44, 44,
            44, 44, 48, 48, 48, 48, 48, 50,
        ])
        self.assertEqual(normal["critical"], unboosted["critical"])

    def test_hp_cannot_have_a_stat_stage(self):
        """HP is rejected as a stat-stage target."""
        with self.assertRaises(ValueError):
            Pokemon.load("Incineroar", stat_stages={"hp": 1})

    def test_stat_stage_limits_are_enforced(self):
        """Stat stages outside the -6 to +6 range are rejected."""
        with self.assertRaises(ValueError):
            Pokemon.load("Incineroar", stat_stages={"attack": 7})

        with self.assertRaises(ValueError):
            Pokemon.load("Incineroar", stat_stages={"attack": -7})

    def test_move_lookup_returns_required_attributes(self):
        """Move lookup returns category, accuracy, power, type, and PP."""
        move = get_move("Acid Spray")

        self.assertEqual(move.category, "Special")
        self.assertEqual(move.accuracy, 100)
        self.assertEqual(move.base_power, 40)
        self.assertEqual(move.type, "Poison")
        self.assertEqual(move.pp, 20)

    def test_move_database_matches_current_champions_snapshot(self):
        """The move CSV includes the complete current Champions move list."""
        move_csv = resources.files("pyvgc.data").joinpath(
            "move_templates.csv"
        )
        with move_csv.open("r", encoding="utf-8", newline="") as file:
            rows = list(csv.DictReader(file))

        self.assertEqual(len(rows), 512)
        self.assertEqual(
            len({row["MoveName"].casefold() for row in rows}),
            len(rows),
        )
        self.assertIn("Revival Blessing", {row["MoveName"] for row in rows})
        self.assertEqual(get_move("Revival Blessing").category, "Status")
        self.assertIsNone(get_move("Revival Blessing").base_power)
        self.assertIsNone(get_move("Revival Blessing").accuracy)
        self.assertEqual(get_move("Revival Blessing").pp, 1)

        learnsets = resources.files("pyvgc.data").joinpath(
            "regulations", "m_c", "learnsets.csv"
        )
        with learnsets.open("r", encoding="utf-8", newline="") as file:
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

    def test_move_learnset_lookups_are_alphabetical_and_bidirectional(self):
        """Pokémon-to-move and move-to-Pokémon lookups use cached indexes."""
        moves = get_moves_for_pokemon("Venusaur", regulation="M-C")
        users = get_pokemon_for_move("Acid Spray", regulation="M-C")

        self.assertEqual([move.name for move in moves], sorted(
            (move.name for move in moves), key=str.casefold
        ))
        self.assertIn("Acid Spray", {move.name for move in moves})
        self.assertIn("Venusaur", users)

        older_moves = get_moves_for_pokemon("Venusaur", regulation="M-A")
        older_users = get_pokemon_for_move("Acid Spray", regulation="M-A")
        self.assertEqual(
            {move.name for move in older_moves},
            {move.name for move in moves},
        )
        self.assertNotEqual(older_users, users)

    def test_regular_typhlosion_does_not_learn_infernal_parade(self):
        """Infernal Parade is restricted to Hisuian Typhlosion."""
        for regulation_name in ("M-A", "M-B", "M-C"):
            regulation = load_regulation(regulation_name)
            self.assertNotIn(
                "Infernal Parade",
                {move.name for move in regulation.learnsets["Typhlosion"]},
                regulation_name,
            )
            self.assertIn(
                "Infernal Parade",
                {
                    move.name
                    for move in regulation.learnsets["Typhlosion-Hisuian"]
                },
                regulation_name,
            )

    def test_mr_mime_does_not_learn_follow_me(self):
        """Follow Me is not in Mr. Mime's learnset."""
        for regulation_name in ("M-A", "M-B", "M-C"):
            regulation = load_regulation(regulation_name)
            if "Mr.Mime" in regulation.learnsets:
                self.assertNotIn(
                    "Follow Me",
                    {
                        move.name
                        for move in regulation.learnsets["Mr.Mime"]
                    },
                    regulation_name,
                )

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
        self.assertTrue(regulation.get_moves_for_pokemon("Incineroar"))

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
            regulation._learnsets_by_pokemon,
            singles._learnsets_by_pokemon,
        )
        self.assertIs(regulation._pokemon_by_move, singles._pokemon_by_move)
        self.assertIs(
            regulation._signature_move_index,
            singles._signature_move_index,
        )
        self.assertIs(regulation.move("pRoTeCt"), regulation._move_index["protect"])
        self.assertIs(
            regulation.get_moves_for_pokemon("incineroar"),
            get_moves_for_pokemon("Incineroar", "M-C"),
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
        with self.assertRaises(TypeError):
            get_moves_for_pokemon("")
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
