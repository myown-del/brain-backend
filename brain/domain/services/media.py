def get_file_extension(filename: str | None, default: str = "bin") -> str:
    if not filename or "." not in filename:
        return default
    return filename.rsplit(".", 1)[-1].lower()


def guess_image_content_type(file_path: str | None) -> str | None:
    """Infer the MIME type from a file path extension, returning None when unknown."""
    if not file_path:
        return None
    extension = get_file_extension(file_path, default="")
    if extension in {"jpg", "jpeg"}:
        return "image/jpeg"
    if extension == "png":
        return "image/png"
    if extension == "webp":
        return "image/webp"
    return None


def build_public_file_url(*, external_host: str, file_path: str) -> str:
    base = (external_host or "").rstrip("/")
    path = (file_path or "").lstrip("/")
    return f"{base}/{path}"
