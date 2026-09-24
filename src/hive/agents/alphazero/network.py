"""network.py: the policy+value architecture. Forward pass only — no training loop here (Phase 4).

Input: encoding.encode(game), shape (encoding.NUM_CHANNELS, WINDOW_SIZE, WINDOW_SIZE).
Output: raw policy logits shaped like action_space.ACTION_SHAPE, plus a scalar value in
[-1, 1] (from the current Player's own perspective: +1 = certain win, -1 = certain loss).

The policy head emits logits over the *whole* factored action space, including
indices that are illegal in the current position — evaluate_position() masks
those out before turning logits into a probability distribution, the same
"never trust an unmasked output" discipline the rest of this engine already
follows (Game.legal_moves() is the only source of truth for what's legal).
"""

from __future__ import annotations

import torch
from torch import nn

from hive.agents.alphazero import action_space, encoding
from hive.agents.alphazero.config import NetworkConfig
from hive.game import Game
from hive.moves import Move


class _ResidualBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        residual = x
        out = torch.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return torch.relu(out + residual)


class HiveNet(nn.Module):
    """A small ResNet-style trunk with a policy head and a value head."""

    def __init__(self, config: NetworkConfig | None = None) -> None:
        super().__init__()
        self.config = config or NetworkConfig()
        channels = self.config.residual_channels

        self.stem_conv = nn.Conv2d(encoding.NUM_CHANNELS, channels, kernel_size=3, padding=1)
        self.stem_bn = nn.BatchNorm2d(channels)
        self.residual_blocks = nn.ModuleList(
            [_ResidualBlock(channels) for _ in range(self.config.num_residual_blocks)]
        )

        self.policy_conv = nn.Conv2d(channels, action_space.NUM_PIECE_SLOTS, kernel_size=1)

        board_cells = encoding.WINDOW_SIZE * encoding.WINDOW_SIZE
        self.value_conv = nn.Conv2d(channels, 1, kernel_size=1)
        self.value_fc1 = nn.Linear(board_cells, self.config.value_head_hidden_units)
        self.value_fc2 = nn.Linear(self.config.value_head_hidden_units, 1)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """`x`: (batch, NUM_CHANNELS, WINDOW_SIZE, WINDOW_SIZE) -> (policy_logits, value).

        policy_logits: (batch, *action_space.ACTION_SHAPE). value: (batch,), in [-1, 1].
        """
        trunk = torch.relu(self.stem_bn(self.stem_conv(x)))
        for block in self.residual_blocks:
            trunk = block(trunk)

        policy_logits = self.policy_conv(trunk)

        value = torch.relu(self.value_conv(trunk))
        value = value.flatten(start_dim=1)
        value = torch.relu(self.value_fc1(value))
        value = torch.tanh(self.value_fc2(value)).squeeze(-1)

        return policy_logits, value


def evaluate_position(net: HiveNet, game: Game) -> tuple[dict[Move, float], float]:
    """Runs `net` on `game`'s current position; returns (legal-move probabilities, value).

    The returned dict covers every legal Move, softmax-normalized over *only*
    the legal ones (everything else the network output is discarded, never
    sampled from). When more than one legal Move shares an action index —
    a Piece reachable by both its own Movement and a Pillbug's Throw to the
    same Cell, which end up in the same board state either way, see
    action_space.legal_action_map's docstring — each gets an equal share of
    that index's probability mass rather than picking one arbitrarily.
    """
    net.eval()
    with torch.no_grad():
        tensor = torch.from_numpy(encoding.encode(game)).unsqueeze(0)
        policy_logits, value = net(tensor)
        policy_logits = policy_logits.squeeze(0)
        value = value.item()

    action_map = action_space.legal_action_map(game)

    if None in action_map:
        # Pass only ever appears as the sole legal Move — Game.legal_moves()
        # falls back to it solely when nothing else is legal — so it's
        # never mixed with spatial moves and always just gets probability 1.
        pass_moves = action_map[None]
        return {move: 1.0 / len(pass_moves) for move in pass_moves}, value

    legal_logits = torch.stack([policy_logits[slot, row, col] for slot, row, col in action_map])
    probabilities = torch.softmax(legal_logits, dim=0)

    move_probabilities: dict[Move, float] = {}
    for index, probability in zip(action_map, probabilities.tolist(), strict=True):
        moves_at_index = action_map[index]
        share = probability / len(moves_at_index)
        for move in moves_at_index:
            move_probabilities[move] = share

    return move_probabilities, value
