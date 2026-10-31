"""Document canonical API once; the frontend alias has identical URL contracts."""
def canonical_api(endpoints):
    return [entry for entry in endpoints if not entry[0].startswith('/paypoint/api/')]
