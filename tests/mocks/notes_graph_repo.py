from uuid import UUID
from dataclasses import dataclass
from collections import deque

from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.domain.entities.graph import GraphData, GraphNode, GraphConnection
from brain.domain.entities.note import Note


@dataclass
class DummyGraphNode:
    id: str | UUID
    user_id: UUID
    title: str
    is_note: bool = True
    represents_keyword: bool = False
    
    
class DummyNotesGraphRepository(INotesGraphRepository):
    # Global state for testing
    _notes: dict[UUID, dict[UUID, DummyGraphNode]] = {}
    _links: dict[UUID, dict[str, set[str]]] = {}

    def __init__(self):
        pass

    def _get_user_notes(self, user_id: UUID):
        if user_id not in self._notes:
            self._notes[user_id] = {}
        return self._notes[user_id]
        
    def _get_user_links(self, user_id: UUID):
        if user_id not in self._links:
            self._links[user_id] = {}
        return self._links[user_id]
    
    def _get_notes_by_title(self, user_id: UUID) -> dict[str, DummyGraphNode]:
        user_notes = self._get_user_notes(user_id)
        return {note.title: note for note in user_notes.values()}
    
    def _collect_keywords(self, user_id: UUID) -> set[str]:
        user_links = self._get_user_links(user_id)
        keywords: set[str] = set()
        for targets in user_links.values():
            keywords.update(targets)
        return keywords

    async def upsert_note(self, note: Note):
        user_notes = self._get_user_notes(note.user_id)
        
        old_title = None
        if note.id in user_notes:
            old_title = user_notes[note.id].title
            
        user_notes[note.id] = DummyGraphNode(
            id=note.id,
            user_id=note.user_id,
            title=note.title,
            is_note=True,
            represents_keyword=bool(note.represents_keyword_id),
        )
        
        if old_title and old_title != note.title:
            user_links = self._get_user_links(note.user_id)
            if old_title in user_links:
                user_links[note.title] = user_links.pop(old_title)

    async def sync_connections(
        self,
        note: Note,
        link_targets: list[str],
        previous_title: str | None = None,
        previous_represents_keyword_id: UUID | None = None,
    ):
        user_links = self._get_user_links(note.user_id)
        user_links[note.title] = set(link_targets)

    async def delete_note(self, note_id: UUID):
        for uid, notes in self._notes.items():
            if note_id in notes:
                deleted = notes.pop(note_id)
                # Remove links from this note
                if uid in self._links and deleted.title in self._links[uid]:
                    del self._links[uid][deleted.title]
                break

    async def count_notes_by_user_and_title(self, user_id: UUID, title: str) -> int:
        user_notes = self._get_user_notes(user_id)
        if any(n.title == title for n in user_notes.values()):
            return 1
        if title in self._collect_keywords(user_id):
            return 1
        return 0

    async def count_links_between_notes(
        self, user_id: UUID, from_title: str, to_title: str,
    ) -> int:
        user_links = self._get_user_links(user_id)
        targets = user_links.get(from_title)
        if not targets:
            return 0
        count = 0
        if to_title in targets:
            count += 1
        shared = targets.intersection(user_links.get(to_title, set()))
        count += len(shared)
        return count

    async def get_graph(
        self,
        user_id: UUID,
        query: str | None = None,
        depth: int = 1,
    ) -> GraphData:
        user_notes = self._get_user_notes(user_id)
        notes_by_title = self._get_notes_by_title(user_id)
        keywords = self._collect_keywords(user_id)

        node_info: dict[str, dict[str, object]] = {}
        for note in user_notes.values():
            node_info[f"note:{note.id}"] = {
                "kind": "note",
                "title": note.title,
                "represents_keyword": note.represents_keyword,
            }

        for keyword in keywords:
            note = notes_by_title.get(keyword)
            has_keyword_note = bool(note and note.represents_keyword)
            node_info[f"keyword:{keyword}"] = {
                "kind": "keyword",
                "title": keyword,
                "has_keyword_note": has_keyword_note,
            }

        if not node_info:
            return GraphData(nodes=[], connections=[])

        # Build adjacency and edge lists.
        adjacency: dict[str, set[str]] = {node_id: set() for node_id in node_info}
        has_keyword_edges: list[tuple[str, str]] = []
        links_to_edges: list[tuple[str, str]] = []
        user_links = self._get_user_links(user_id)

        for from_title, targets in user_links.items():
            source_note = notes_by_title.get(from_title)
            if not source_note:
                continue
            from_id = f"note:{source_note.id}"
            for target in targets:
                keyword_id = f"keyword:{target}"
                if keyword_id not in node_info:
                    node_info[keyword_id] = {
                        "kind": "keyword",
                        "title": target,
                        "has_keyword_note": False,
                    }
                    adjacency[keyword_id] = set()
                has_keyword_edges.append((from_id, keyword_id))
                adjacency[from_id].add(keyword_id)
                adjacency[keyword_id].add(from_id)

                target_note = notes_by_title.get(target)
                if target_note and target_note.represents_keyword:
                    to_id = f"note:{target_note.id}"
                    links_to_edges.append((from_id, to_id))
                    adjacency[from_id].add(to_id)
                    adjacency[to_id].add(from_id)

        # Determine reachable nodes by query/depth.
        if query:
            query_lower = query.lower()
            seeds = [
                node_id
                for node_id, info in node_info.items()
                if query_lower in str(info.get("title", "")).lower()
            ]
            if not seeds:
                return GraphData(nodes=[], connections=[])

            distances: dict[str, int] = {}
            queue: deque[str] = deque()
            for seed in seeds:
                distances[seed] = 0
                queue.append(seed)

            while queue:
                node_id = queue.popleft()
                current_depth = distances[node_id]
                if current_depth >= depth:
                    continue
                for neighbor in adjacency.get(node_id, set()):
                    if neighbor in distances:
                        continue
                    distances[neighbor] = current_depth + 1
                    queue.append(neighbor)

            candidate_nodes = {
                node_id for node_id, dist in distances.items() if dist <= depth
            }
        else:
            candidate_nodes = set(node_info.keys())

        visible_nodes: set[str] = set()
        for node_id in candidate_nodes:
            info = node_info[node_id]
            if info["kind"] == "keyword" and info.get("has_keyword_note"):
                continue
            visible_nodes.add(node_id)

        if not visible_nodes:
            return GraphData(nodes=[], connections=[])

        nodes: list[GraphNode] = []
        for node_id in visible_nodes:
            info = node_info[node_id]
            nodes.append(
                GraphNode(
                    id=node_id,
                    title=str(info["title"]),
                    kind=str(info["kind"]),
                    represents_keyword=(
                        info.get("represents_keyword")
                        if info["kind"] == "note"
                        else None
                    ),
                    has_keyword_note=(
                        info.get("has_keyword_note")
                        if info["kind"] == "keyword"
                        else None
                    ),
                ),
            )

        connection_set: set[tuple[str, str, str]] = set()
        for from_id, to_id in has_keyword_edges:
            if from_id in visible_nodes and to_id in visible_nodes:
                connection_set.add((from_id, to_id, "has_keyword"))

        for from_id, to_id in links_to_edges:
            if from_id in visible_nodes and to_id in visible_nodes:
                connection_set.add((from_id, to_id, "links_to"))

        connections = [
            GraphConnection(from_id=f, to_id=t, kind=k)
            for f, t, k in connection_set
        ]

        return GraphData(nodes=nodes, connections=connections)
