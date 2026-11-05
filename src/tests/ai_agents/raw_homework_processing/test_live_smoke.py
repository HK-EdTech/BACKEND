"""Live smoke testing is deferred until raw processing is implemented."""

import pytest


@pytest.mark.skip(
    reason="Raw homework processing is currently a dummy subgraph."
)
def test_live_smoke():
    pass
