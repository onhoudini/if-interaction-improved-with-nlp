import re
from typing import List


def tokenize(text: str) -> List[str]:
    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", cleaned)
    return [token for token in cleaned.split() if token]