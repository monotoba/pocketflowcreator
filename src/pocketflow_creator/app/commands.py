from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any

try:
    from PySide6.QtGui import QUndoCommand
except ImportError:  # pragma: no cover
    QUndoCommand = object  # type: ignore[assignment,misc]

if TYPE_CHECKING:
    from pocketflow_creator.app.canvas import GraphScene
    from pocketflow_creator.model.graph_model import GraphModel


class GraphSnapshotCommand(QUndoCommand):
    """Snapshot-based undo/redo for a single graph mutation.

    Stores deep-copies of the graph model before and after a mutation.
    undo() restores the before state; redo() restores the after state and
    skips the first call (since the mutation was already applied live).
    """

    def __init__(
        self,
        text: str,
        graphs: dict[str, Any],
        rel: str,
        before: GraphModel,
        after: GraphModel,
        scene: GraphScene,
        first_redo_is_noop: bool = True,
    ) -> None:
        super().__init__(text)
        self._graphs = graphs
        self._rel = rel
        self._before = before
        self._after = after
        self._scene = scene
        self._first_redo = first_redo_is_noop

    def undo(self) -> None:
        self._graphs[self._rel] = copy.deepcopy(self._before)
        self._scene.load_graph(self._graphs[self._rel])

    def redo(self) -> None:
        if self._first_redo:
            self._first_redo = False
            return
        self._graphs[self._rel] = copy.deepcopy(self._after)
        self._scene.load_graph(self._graphs[self._rel])
