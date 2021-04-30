import json
from enum import Enum

from catanatron.game import Game
from catanatron.models.map import Water, Port, Tile
from catanatron.models.player import Color, Player
from catanatron.models.decks import Deck
from catanatron.models.actions import Action, ActionType
from catanatron.models.enums import Resource


def longest_roads_by_player(state):
    return {player.color.value: player.longest_road_length for player in state.players}


def action_from_json(data):
    color = Color[data[0]]
    action_type = ActionType[data[1]]
    if (
        action_type == ActionType.BUILD_INITIAL_ROAD
        or action_type == ActionType.BUILD_ROAD
    ):
        action = Action(color, action_type, tuple(data[2]))
    elif action_type == ActionType.MARITIME_TRADE:
        action = Action(
            color,
            action_type,
            tuple([None if i is None else Resource[i] for i in data[2]]),
        )
    else:
        action = Action(color, action_type, data[2])
    return action


class GameEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return None
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, tuple):
            return obj
        if isinstance(obj, Game):
            nodes = {}
            edges = {}
            for coordinate, tile in obj.state.board.map.tiles.items():
                for direction, node_id in tile.nodes.items():
                    building = obj.state.board.buildings.get(node_id, None)
                    color = None if building is None else building[0]
                    building_type = None if building is None else building[1]
                    nodes[node_id] = {
                        "id": node_id,
                        "tile_coordinate": coordinate,
                        "direction": self.default(direction),
                        "building": self.default(building_type),
                        "color": self.default(color),
                    }
                for direction, edge in tile.edges.items():
                    color = obj.state.board.roads.get(edge, None)
                    edge_id = tuple(sorted(edge))
                    edges[edge_id] = {
                        "id": edge_id,
                        "tile_coordinate": coordinate,
                        "direction": self.default(direction),
                        "color": self.default(color),
                    }
            return {
                "tiles": [
                    {"coordinate": coordinate, "tile": self.default(tile)}
                    for coordinate, tile in obj.state.board.map.tiles.items()
                ],
                "nodes": nodes,
                "edges": list(edges.values()),
                "actions": [self.default(a) for a in obj.state.actions],
                "players": [self.default(p) for p in obj.state.players],
                "robber_coordinate": obj.state.board.robber_coordinate,
                "current_color": obj.state.current_player().color,
                "current_prompt": obj.state.current_prompt,
                "current_playable_actions": obj.state.playable_actions,
                "longest_roads_by_player": longest_roads_by_player(obj.state),
                "winning_color": obj.winning_color(),
            }
        if isinstance(obj, Deck):
            return {resource.value: count for resource, count in obj.cards.items()}
        if isinstance(obj, Player):
            return {k: v for k, v in obj.__dict__.items() if k != "buildings"}
        if isinstance(obj, Water):
            return {"type": "WATER"}
        if isinstance(obj, Port):
            return {
                "id": obj.id,
                "type": "PORT",
                "direction": self.default(obj.direction),
                "resource": self.default(obj.resource),
            }
        if isinstance(obj, Tile):
            if obj.resource is None:
                return {"id": obj.id, "type": "DESERT"}
            return {
                "id": obj.id,
                "type": "RESOURCE_TILE",
                "resource": self.default(obj.resource),
                "number": obj.number,
            }
        return json.JSONEncoder.default(self, obj)
