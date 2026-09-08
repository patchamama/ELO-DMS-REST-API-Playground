"""The single error type raised by the teaching client."""
from __future__ import annotations


class EloError(RuntimeError):
    """Any ELO IX call that did not succeed.

    Three very different failures are wrapped behind one type so example code
    can ``try / except EloError`` and catch nothing else:

    * transport problems  - host unreachable, DNS, TLS, timeout
    * an HTTP error status from the IX endpoint - 401, 403, 500, ...
    * a handled error returned by IX itself as a ``{"exception": ...}`` body
      (HTTP 200, but the call still failed: bad parameters, object not found,
      no permission, ...)
    """
