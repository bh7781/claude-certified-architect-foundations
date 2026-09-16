"""
Pretty-printer for Claude API Message objects.

client.messages.create() returns a Message object. Printed directly, it
looks like a single dense line:

    Message(id='msg_011Cf6ybL26wbj72RSiiSeke', container=None,
    content=[TextBlock(citations=None, text='Paris', type='text')],
    model='claude-haiku-4-5-20251001', role='assistant', stop_details=None,
    stop_reason='end_turn', stop_sequence=None, type='message',
    usage=Usage(...))

format_message() turns that into the SAME data, every field included,
just indented so it's actually readable - but ONLY if the object actually
looks like a Message. Anything else (a plain string, a dict, etc.) is left
alone by returning None, so the caller can fall back to logging it as-is.
"""

import json

# The fields we expect on a real Message response - if any of these are
# missing, this isn't a Message and we shouldn't try to parse it.
REQUIRED_FIELDS = ("id", "content", "model", "role", "stop_reason", "usage")

DIVIDER = "-" * 60


def _is_message(obj) -> bool:
    """True if obj has every field a Claude Message response has."""
    return all(hasattr(obj, field) for field in REQUIRED_FIELDS)


def format_message(obj):
    """
    Return a readable, fully-detailed dump of a Claude Message response
    (every field - container, content, stop_details, usage, all of it),
    wrapped in divider lines so it's easy to spot in a log file. Returns
    None if `obj` isn't a Message, so the caller knows to log it as-is
    instead.
    """
    if not _is_message(obj):
        return None

    # model_dump() turns the whole object (and everything nested inside it,
    # like each content block and the usage stats) into a plain dict, with
    # nothing left out. json.dumps(..., indent=2) then lays that out
    # readably instead of Python's dense one-line repr.
    full_data = obj.model_dump()
    pretty = json.dumps(full_data, indent=2, default=str)

    return f"{DIVIDER}\nMessage:\n{pretty}\n{DIVIDER}"
