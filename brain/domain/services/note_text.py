class NoteTextService:
    def chain_with_newline(self, texts: list[str | None]) -> str | None:
        chunks = [text for text in texts if text not in (None, "")]
        if not chunks:
            return None
        return "\n".join(chunks)

    def append_with_newline(self, base: str | None, suffix: str | None) -> str | None:
        if suffix in (None, ""):
            return base
        if base in (None, ""):
            return suffix
        return f"{base}\n{suffix}"
