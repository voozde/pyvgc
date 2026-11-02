"""Supportive data-query utilities for pyvgc."""

from functools import lru_cache

from .moves import Move


@lru_cache(maxsize=None)
def _learnset_indexes(
    regulation: str,
) -> tuple[
    dict[str, tuple[Move, ...]],
    dict[str, tuple[str, ...]],
]:
    """Load and cache Pokémon and move-to-Pokémon learnset indexes."""
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    by_pokemon = {}
    by_move = {}
    for pokemon_name, moves in snapshot.learnsets.items():
        by_pokemon[pokemon_name.casefold()] = moves
        for move in moves:
            by_move.setdefault(move.name.casefold(), []).append(pokemon_name)
    return (
        by_pokemon,
        {
            move: tuple(sorted(users, key=str.casefold))
            for move, users in by_move.items()
        },
    )


def get_moves_for_pokemon(
    name: str,
    regulation: str = "M-C",
) -> tuple[Move, ...]:
    """Return a Pokémon's legal moves for a regulation.

    Args:
        name: Pokémon form name.
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Pokémon name must be a non-empty string")
    try:
        moves = _learnset_indexes(regulation)[0][name.strip().casefold()]
    except KeyError:
        raise KeyError(
            f"Pokémon not found in Pokémon Champions learnsets: {name!r}"
        ) from None
    return moves


def get_pokemon_for_move(
    name: str,
    regulation: str = "M-C",
) -> tuple[str, ...]:
    """Return all forms that learn a move in a regulation.

    Args:
        name: Move name.
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("move name must be a non-empty string")
    from .regulations import load_regulation

    move_name = load_regulation(regulation).move(name).name
    return _learnset_indexes(regulation)[1].get(move_name.casefold(), ())


def pokemon_with_single_ability(regulation: str) -> tuple[str, ...]:
    """Return forms with exactly one recorded ability.

    Args:
        regulation: Regulation snapshot name, such as ``"M-B"``.

    Returns:
        Canonically named forms sorted case-insensitively.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return tuple(sorted(
        (
            pokemon_name
            for pokemon_name, abilities in snapshot.abilities.items()
            if len(abilities) == 1
        ),
        key=str.casefold,
    ))


def pokemon_with_ability(
    regulation: str,
    ability: str,
) -> tuple[str, ...]:
    """Return forms that have a named ability in a regulation.

    Args:
        regulation: Regulation snapshot name, such as ``"M-B"``.
        ability: Ability name to match, case-insensitively.

    Returns:
        Canonically named forms sorted case-insensitively.

    Raises:
        ValueError: If ``ability`` is not a non-empty string.
    """
    if not isinstance(ability, str) or not ability.strip():
        raise ValueError("ability name must be a non-empty string")

    target = ability.strip().casefold()
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return tuple(sorted(
        (
            pokemon_name
            for pokemon_name, abilities in snapshot.abilities.items()
            if any(recorded.casefold() == target for recorded in abilities)
        ),
        key=str.casefold,
    ))


def regulation_description(regulation: str) -> str:
    """Return one line containing the content counts for a regulation.

    The returned format is ``"Pokémon: X, Items: Y, Moves: Z"``.

    Args:
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    return (
        f"Pokémon: {len(snapshot.pokemon_names)}, "
        f"Items: {len(snapshot.items)}, "
        f"Moves: {len(snapshot.moves)}"
    )


def signature_moves(regulation: str) -> tuple[tuple[str, str], ...]:
    """Return moves learned by exactly one Pokémon species.

    Each result is a ``(move_name, pokemon_name)`` pair. Pokémon forms are
    grouped by their shared roster number, so a move learned by a base form
    and its Mega or alternate forms is still signature to that species. Every
    form that learns the signature move is included in the result.

    Args:
        regulation: Regulation snapshot name, such as ``"M-C"``.

    Returns:
        Signature move and Pokémon-form pairs sorted by move and form name.
    """
    from .regulations import load_regulation

    snapshot = load_regulation(regulation)
    form_numbers = {
        row["PokemonName"]: row["PokemonNumber"]
        for row in snapshot.pokemon
    }
    users: dict[str, list[tuple[str, str]]] = {}
    for pokemon_name, moves in snapshot.learnsets.items():
        for move in moves:
            users.setdefault(move.name.casefold(), []).append(
                (pokemon_name, form_numbers[pokemon_name])
            )

    signature = []
    for move_key, move_users in users.items():
        species_numbers = {number for _, number in move_users}
        if len(species_numbers) == 1:
            move_name = next(
                move.name
                for move in snapshot.moves
                if move.name.casefold() == move_key
            )
            signature.extend(
                (move_name, pokemon_name)
                for pokemon_name, _ in move_users
            )
    return tuple(sorted(
        signature,
        key=lambda pair: (pair[0].casefold(), pair[1].casefold()),
    ))
