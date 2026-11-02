"""Supportive data-query utilities for pyvgc."""

from .moves import Move


def get_moves_for_pokemon(
    name: str,
    regulation: str,
) -> tuple[Move, ...]:
    """Return a Pokémon's legal moves for a regulation.

    Args:
        name: Pokémon form name.
        regulation: Regulation snapshot name, such as ``"M-C"``.
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Pokémon name must be a non-empty string")
    from .regulations import load_regulation

    try:
        return load_regulation(regulation).get_moves_for_pokemon(name)
    except KeyError:
        raise KeyError(
            f"Pokémon not found in Pokémon Champions learnsets: {name!r}"
        ) from None


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

    snapshot = load_regulation(regulation)
    move_name = snapshot.move(name).name
    return snapshot._pokemon_by_move.get(move_name.casefold(), ())


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
    return snapshot._signature_move_index
