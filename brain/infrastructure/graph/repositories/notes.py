from uuid import UUID

from neo4j import AsyncDriver

from brain.application.abstractions.repositories.notes_graph import INotesGraphRepository
from brain.domain.entities.graph import GraphData, GraphNode, GraphConnection
from brain.domain.entities.note import Note
from brain.infrastructure.graph.tx_accessor import Neo4jTxAccessor


class NotesGraphRepository(INotesGraphRepository):
    def __init__(self, driver: AsyncDriver, database: str, tx_accessor: Neo4jTxAccessor):
        self._driver = driver
        self._database = database
        self._tx_accessor = tx_accessor

    async def _run_write(self, query: str, **params: str | bool | list[str] | None) -> None:
        tx = await self._tx_accessor.get_tx()
        await tx.run(query, **params)

    async def upsert_note(self, note: Note):
        query = """
            MERGE (n:Note {id: $id})
            SET
                n.user_id = $user_id,
                n.title = $title,
                n.text = $text,
                n.represents_keyword_id = $represents_keyword_id,
                n.is_archived = $is_archived
        """
        await self._run_write(
            query,
            id=str(note.id),
            user_id=str(note.user_id),
            title=note.title,
            text=note.text,
            represents_keyword_id=str(note.represents_keyword_id),
            is_archived=note.is_archived,
        )

    async def sync_connections(
        self,
        note: Note,
        link_targets: list[str],
        previous_title: str | None = None,
        previous_represents_keyword_id: UUID | None = None,
    ):
        await self._run_write(
            """
            MATCH (n:Note {id: $id})
            OPTIONAL MATCH (n)-[r]->()
            WHERE type(r) IN ["LINKS_TO", "HAS_KEYWORD"]
            DELETE r
            """,
            id=str(note.id),
        )

        if previous_represents_keyword_id and previous_title != note.title:
            await self._run_write(
                """
                MATCH (source:Note)-[r]->(target:Note {id: $id})
                WHERE type(r) = "LINKS_TO"
                MATCH (source)-[:HAS_KEYWORD]->(:Keyword {
                    user_id: $user_id,
                    name: $prev_title
                })
                DELETE r
                """,
                id=str(note.id),
                user_id=str(note.user_id),
                prev_title=previous_title,
            )

        if link_targets:
            await self._run_write(
                """
                MATCH (source:Note {id: $id})
                UNWIND $targets AS target
                MERGE (k:Keyword {user_id: $user_id, name: target})
                MERGE (source)-[:HAS_KEYWORD]->(k)
                """,
                id=str(note.id),
                user_id=str(note.user_id),
                targets=link_targets,
            )

            await self._run_write(
                """
                MATCH (source:Note {id: $id})
                UNWIND $targets AS target
                MATCH (target_note:Note {user_id: $user_id, title: target})
                WHERE
                    target_note.represents_keyword_id IS NOT NULL
                    AND (target_note.is_archived IS NULL OR target_note.is_archived = false)
                    AND target_note.id <> $id
                MERGE (source)-[:LINKS_TO]->(target_note)
                """,
                id=str(note.id),
                user_id=str(note.user_id),
                targets=link_targets,
            )

        await self._run_write(
            """
            MATCH (target:Note {id: $id})
            MATCH (k:Keyword {user_id: $user_id, name: $title})
            MATCH (source:Note)-[:HAS_KEYWORD]->(k)
            WHERE
                source.id <> target.id
                AND (source.is_archived IS NULL OR source.is_archived = false)
            MERGE (source)-[:LINKS_TO]->(target)
            """,
            id=str(note.id),
            user_id=str(note.user_id),
            title=note.title,
        )

    async def delete_note(self, note_id: UUID):
        await self._run_write(
            """
            MATCH (n:Note {id: $id})
            WITH n, n.user_id AS user_id
            DETACH DELETE n
            WITH user_id
            MATCH (k:Keyword {user_id: user_id})
            WHERE NOT EXISTS {
                MATCH (:Note)-[:HAS_KEYWORD]->(k)
            }
            AND NOT EXISTS {
                MATCH (m:Note {user_id: user_id, title: k.name})
                WHERE m.represents_keyword_id IS NOT NULL
            }
            DETACH DELETE k
            """,
            id=str(note_id),
        )

    async def count_notes_by_user_and_title(self, user_id: UUID, title: str) -> int:
        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                """
                RETURN CASE WHEN
                    EXISTS {
                        MATCH (n:Note {user_id: $user_id, title: $title})
                    }
                    OR EXISTS {
                        MATCH (k:Keyword {user_id: $user_id, name: $title})
                    }
                THEN 1 ELSE 0 END AS c
                """,
                user_id=str(user_id),
                title=title,
            )
            record = await result.single()
            return record["c"] if record else 0

    async def count_links_between_notes(self, user_id: UUID, from_title: str, to_title: str) -> int:
        async with self._driver.session(database=self._database) as session:
            result = await session.run(
                """
                MATCH (from:Note {user_id: $user_id, title: $from_title})
                OPTIONAL MATCH (from)-[:HAS_KEYWORD]->(direct:Keyword {
                    user_id: $user_id,
                    name: $to_title
                })
                WITH from, count(DISTINCT direct) AS direct_count
                OPTIONAL MATCH (from)-[:HAS_KEYWORD]->(shared:Keyword)<-[:HAS_KEYWORD]-(
                    to:Note {user_id: $user_id, title: $to_title}
                )
                WITH direct_count, count(DISTINCT shared) AS shared_count
                RETURN direct_count + shared_count AS c
                """,
                user_id=str(user_id),
                from_title=from_title,
                to_title=to_title,
            )
            record = await result.single()
            return record["c"] if record else 0

    async def get_graph(
        self,
        user_id: UUID,
        query: str | None = None,
        depth: int = 1,
    ) -> GraphData:
        nodes_query = """
            CALL {
                MATCH (k:Keyword {user_id: $user_id})
                RETURN DISTINCT
                    'keyword' AS kind,
                    'keyword:' + k.name AS id,
                    k.name AS title,
                    EXISTS {
                        MATCH (n:Note {user_id: $user_id, title: k.name})
                        WHERE
                            n.represents_keyword_id IS NOT NULL
                            AND (n.is_archived IS NULL OR n.is_archived = false)
                    } AS has_keyword_note,
                    NULL AS represents_keyword,
                    k.name AS keyword_name,
                    NULL AS note_id
                UNION
                MATCH (n:Note {user_id: $user_id})
                WHERE
                    n.title IS NOT NULL
                    AND (n.is_archived IS NULL OR n.is_archived = false)
                RETURN DISTINCT
                    'note' AS kind,
                    'note:' + toString(n.id) AS id,
                    n.title AS title,
                    NULL AS has_keyword_note,
                    (n.represents_keyword_id IS NOT NULL) AS represents_keyword,
                    NULL AS keyword_name,
                    toString(n.id) AS note_id
            }
            RETURN
                kind,
                id,
                title,
                has_keyword_note,
                represents_keyword,
                keyword_name,
                note_id
        """

        nodes_filtered_query = (
            "WITH $user_id AS user_id, $search_query AS search_query "
            "CALL { "
            "    WITH user_id, search_query "
            "    MATCH (k:Keyword {user_id: user_id}) "
            "    WHERE toLower(k.name) CONTAINS toLower(search_query) "
            "    RETURN k AS seed "
            "    UNION "
            "    WITH user_id, search_query "
            "    MATCH (n:Note {user_id: user_id}) "
            "    WHERE n.title IS NOT NULL "
            "    AND (n.is_archived IS NULL OR n.is_archived = false) "
            "    AND toLower(n.title) CONTAINS toLower(search_query) "
            "    RETURN n AS seed "
            "} "
            "WITH DISTINCT seed, user_id "
            f"MATCH p=(seed)-[*0..{depth}]-(node) "
            "WHERE all(r IN relationships(p) WHERE "
            "    type(r) IN ['HAS_KEYWORD', 'LINKS_TO']"
            ") AND all(n IN nodes(p) WHERE "
            "    (n:Keyword AND n.user_id = user_id) "
            "    OR (n:Note AND n.user_id = user_id AND n.title IS NOT NULL) "
            "    AND (n.is_archived IS NULL OR n.is_archived = false) "
            ") "
            "WITH DISTINCT node, user_id "
            "RETURN "
            "    CASE WHEN node:Keyword THEN 'keyword' ELSE 'note' END AS kind, "
            "    CASE WHEN node:Keyword "
            "        THEN 'keyword:' + node.name "
            "        ELSE 'note:' + toString(node.id) END AS id, "
            "    CASE WHEN node:Keyword THEN node.name ELSE node.title END AS title, "
            "    CASE WHEN node:Keyword THEN EXISTS { "
            "        MATCH (n:Note {user_id: user_id, title: node.name}) "
            "        WHERE n.represents_keyword_id IS NOT NULL "
            "        AND (n.is_archived IS NULL OR n.is_archived = false) "
            "    } ELSE NULL END AS has_keyword_note, "
            "    CASE WHEN node:Note "
            "        THEN (node.represents_keyword_id IS NOT NULL) "
            "        ELSE NULL END AS represents_keyword, "
            "    CASE WHEN node:Keyword THEN node.name ELSE NULL END AS keyword_name, "
            "    CASE WHEN node:Note THEN toString(node.id) ELSE NULL END AS note_id"
        )

        async with self._driver.session(database=self._database) as session:
            if query:
                result = await session.run(
                    nodes_filtered_query,
                    user_id=str(user_id),
                    search_query=query,
                )
            else:
                result = await session.run(
                    nodes_query,
                    user_id=str(user_id),
                )

            nodes: list[GraphNode] = []
            keyword_names: list[str] = []
            note_ids: list[str] = []

            async for record in result:
                if record["kind"] == "keyword" and record["has_keyword_note"]:
                    # Hide keyword nodes when a note represents that keyword.
                    continue
                node = GraphNode(
                    id=record["id"],
                    title=record["title"],
                    kind=record["kind"],
                    represents_keyword=record["represents_keyword"],
                    has_keyword_note=record["has_keyword_note"],
                )
                nodes.append(node)
                if record["keyword_name"]:
                    keyword_names.append(record["keyword_name"])
                if record["note_id"]:
                    note_ids.append(record["note_id"])

            if not nodes:
                return GraphData(nodes=[], connections=[])

            connections_query = """
                MATCH (n:Note)-[:HAS_KEYWORD]->(k:Keyword)
                WHERE
                    n.user_id = $user_id
                    AND n.id IN $note_ids
                    AND (n.is_archived IS NULL OR n.is_archived = false)
                    AND k.user_id = $user_id
                    AND k.name IN $keyword_names
                RETURN DISTINCT
                    toString(n.id) AS from_note_id,
                    k.name AS to_keyword,
                    'has_keyword' AS kind,
                    NULL AS to_note_id
                UNION
                MATCH (a:Note)-[r]->(b:Note)
                WHERE
                    type(r) = 'LINKS_TO'
                    AND
                    a.user_id = $user_id
                    AND (a.is_archived IS NULL OR a.is_archived = false)
                    AND b.user_id = $user_id
                    AND (b.is_archived IS NULL OR b.is_archived = false)
                    AND a.id IN $note_ids
                    AND b.id IN $note_ids
                RETURN DISTINCT
                    toString(a.id) AS from_note_id,
                    NULL AS to_keyword,
                    'links_to' AS kind,
                    toString(b.id) AS to_note_id
            """

            result = await session.run(
                connections_query,
                user_id=str(user_id),
                note_ids=note_ids,
                keyword_names=keyword_names,
            )

            connections: list[GraphConnection] = []
            async for record in result:
                if record["kind"] == "has_keyword":
                    to_id = f"keyword:{record['to_keyword']}"
                else:
                    to_id = f"note:{record['to_note_id']}"

                connections.append(
                    GraphConnection(
                        from_id=f"note:{record['from_note_id']}",
                        to_id=to_id,
                        kind=record["kind"],
                    )
                )

            return GraphData(nodes=nodes, connections=connections)
