"""Shared constants and packaged data paths for pyvgc."""

from fractions import Fraction

LEVEL_DOUBLES = 50

BASE_HP_INCREASE = 75
BASE_STAT_INCREASE = 20

MAX_TRAINING_PER_STAT = 32
MAX_TOTAL_TRAINING = 66
MIN_STAT_STAGE = -6
MAX_STAT_STAGE = 6

STAT_STAGE_MULTIPLIERS = {
    stage: (2 + stage, 2) if stage >= 0 else (2, 2 - stage)
    for stage in range(MIN_STAT_STAGE, MAX_STAT_STAGE + 1)
}
DAMAGE_LEVEL_DIVISOR = 5
DAMAGE_DIVISOR = 50

RANDOM_PERCENTAGES = range(85, 101)
STAB_MULTIPLIER = Fraction(3, 2)
CRITICAL_MULTIPLIER = Fraction(3, 2)
SCREEN_MULTIPLIER = Fraction(1, 2)
DOUBLES_SCREEN_MULTIPLIER = Fraction(2, 3)
STAT_NAMES = (
    "hp", "attack", "defense", "special_attack", "special_defense", "speed"
)
TYPES = frozenset((
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting",
    "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost",
    "Dragon", "Dark", "Steel", "Fairy",
))

ALWAYS_HIT_VALUE = "always-hit"

NATURES = {
    "Hardy": ("attack", "attack"), "Lonely": ("attack", "defense"),
    "Brave": ("attack", "speed"), "Adamant": ("attack", "special_attack"),
    "Naughty": ("attack", "special_defense"),
    "Bold": ("defense", "attack"), "Docile": ("defense", "defense"),
    "Impish": ("defense", "special_attack"), "Lax": ("defense", "special_defense"),
    "Relaxed": ("defense", "speed"),
    "Modest": ("special_attack", "attack"), "Mild": ("special_attack", "defense"),
    "Bashful": ("special_attack", "special_attack"),
    "Rash": ("special_attack", "special_defense"), "Quiet": ("special_attack", "speed"),
    "Calm": ("special_defense", "attack"), "Gentle": ("special_defense", "defense"),
    "Careful": ("special_defense", "special_attack"),
    "Quirky": ("special_defense", "special_defense"),
    "Sassy": ("special_defense", "speed"),
    "Timid": ("speed", "attack"), "Hasty": ("speed", "defense"),
    "Jolly": ("speed", "special_attack"), "Naive": ("speed", "special_defense"),
    "Serious": ("speed", "speed"),
}
