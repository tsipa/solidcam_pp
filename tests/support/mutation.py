"""Source-mutation helpers for regression tests.

A regression test proves it guards a behaviour by running its own check on a
mutated GPP (in memory) and requiring an AssertionError. Anything else (an
UnsupportedGPPL, KeyError, ...) means the mutant broke the harness rather than
the behaviour, so it propagates as a test error instead of counting as a kill.
With match=<regex>, the AssertionError must also carry the targeted message;
a kill by an unrelated assertion raises UnrelatedKill (a test error), so a
guard cannot claim a mutant that some other property happened to catch.
"""
import re

from .paths import pp_source


class StaleAnchor(LookupError):
    """The text a mutation targets is no longer in the GPP (test needs updating)."""


class UnrelatedKill(Exception):
    """A mutant was killed by a different assertion than the one it targets."""


def mutate(old, new, *, source=None, count=1):
    """Return source (default: the tested GPP) with old replaced by new.

    old must occur exactly `count` times; otherwise StaleAnchor is raised so a
    rewritten GPP cannot silently turn a mutation into a no-op.
    """
    text = pp_source() if source is None else source
    found = text.count(old)
    if found != count:
        raise StaleAnchor(f'mutation anchor occurs {found} times, expected {count}: {old!r}')
    return text.replace(old, new)


def assert_detected(testcase, check, mutant, label='', match=None):
    """Run check(mutant) and require that it fails with AssertionError.

    match: optional regex the AssertionError message must contain; any other
    AssertionError raises UnrelatedKill instead of counting as a kill.
    """
    try:
        check(mutant)
    except AssertionError as exc:
        if match is not None and not re.search(match, str(exc)):
            raise UnrelatedKill(f'{label or "unnamed mutant"}: killed by an unrelated assertion: {exc}') from exc
        return
    testcase.fail(f'mutation survived: {label or "unnamed mutant"}')
