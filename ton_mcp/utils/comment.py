from __future__ import annotations

import typing as t

from pytoniq_core import Cell
from tonutils.contracts.wallet.tlb import TextCommentBody


def serialize_comment(text: t.Optional[str]) -> t.Optional[Cell]:
    """Serialize optional text comment into a Cell.

    :param text: Comment text or None.
    :return: Serialized Cell or None if text is empty/None.
    """
    if not text:
        return None
    return TextCommentBody(text).serialize()
