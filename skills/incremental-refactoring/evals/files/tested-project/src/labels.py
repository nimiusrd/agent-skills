def format_label(label, uppercase=False):
    if label is None:
        return ""
    if uppercase:
        normalized = " ".join(label.split())
        return normalized.upper()
    else:
        normalized = " ".join(label.split())
        return normalized.lower()
