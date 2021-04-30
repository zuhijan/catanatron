from collections import defaultdict
from typing import Iterable

from catanatron.models.actions import ActionType, Action
from catanatron.models.board import Board
from catanatron.models.player import Player
from catanatron.models.enums import DevelopmentCard


def longest_road(board: Board, players: Iterable[Player], actions: Iterable[Action]):
    """
    For each connected subgraph (made by single-colored roads) find
    the longest path. Take max of all these candidates.

    Returns (color, path) tuple where
        color -- color of player whose longest path belongs.
        longest -- list of edges (all from a single color)
        max_lengths_by_color -- Color => int dict of lengths
    """
    max_count = 0
    max_paths_by_player = dict()
    max_lengths_by_color = defaultdict(int)
    for player in players:
        lengths = []
        for path in board.continuous_roads_by_player(player.color):
            count = len(path)
            lengths.append(count)
            if count < 5:
                continue
            if count > max_count:
                max_count = count
                max_paths_by_player = dict()
                max_paths_by_player[player.color] = path
            elif count == max_count:
                max_paths_by_player[player.color] = path
        max_lengths_by_color[player.color] = 0 if len(lengths) == 0 else max(lengths)

    max_length = max(max_lengths_by_color.values())
    road_candidate_entries = filter(
        lambda entry: entry[1] >= 5 and entry[1] == max_length,
        max_lengths_by_color.items(),
    )
    road_candidates = dict(road_candidate_entries)
    if len(road_candidates) == 0:
        return (None, None, max_lengths_by_color)

    # There might be several tied at max_length. Take the first one that got there.
    for action in reversed(actions):
        if len(road_candidates) == 1:
            color, length = road_candidates.popitem()
            return (color, length, max_lengths_by_color)

        if action.action_type != ActionType.BUILD_ROAD:
            continue

        if action.color in road_candidates:
            del road_candidates[action.color]

    return (None, None, max_lengths_by_color)


def largest_army(players: Iterable[Player], actions: Iterable[Action]):
    num_knights_to_players = defaultdict(set)
    for player in players:
        num_knight_played = player.played_development_cards.count(
            DevelopmentCard.KNIGHT
        )
        num_knights_to_players[num_knight_played].add(player.color)

    max_count = max(num_knights_to_players.keys())
    if max_count < 3:
        return (None, None)

    candidates = num_knights_to_players[max_count]
    knight_actions = list(
        filter(
            lambda a: a.action_type == ActionType.PLAY_KNIGHT_CARD
            and a.color in candidates,
            actions,
        )
    )
    while len(candidates) > 1:
        action = knight_actions.pop()
        if action.color in candidates:
            candidates.remove(action.color)

    return candidates.pop(), max_count
