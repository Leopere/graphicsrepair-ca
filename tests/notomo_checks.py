"""Shared Notomo embed assertions for the Graphics Repair production artifact."""

NOTOMO_INTEGRITY = "sha384-NBbFxiYXSJk326gDu3z2Ak3usWitZIBpVRhbqjBxVynTBnvrnFnHlG+AcLKZf8te"
HOME_CONNECT_SRC = (
    "connect-src 'self' https://forms.motherboardrepair.ca "
    "https://notomo.colinknapp.com/collect https://notomo.colinknapp.com/replay "
    "https://notomo.colinknapp.com/n-config/graphicsrepair.ca "
    "https://notomo.colinknapp.com/n-config/graphicsrepair.com"
)
LEGAL_CONNECT_SRC = (
    "connect-src https://notomo.colinknapp.com/collect "
    "https://notomo.colinknapp.com/replay "
    "https://notomo.colinknapp.com/n-config/graphicsrepair.ca "
    "https://notomo.colinknapp.com/n-config/graphicsrepair.com"
)


def assert_notomo_embed(source: str, connect_src: str) -> None:
    assert source.count('src="/assets/notomo-loader.js"') == 1
    assert 'data-tracker-src="https://notomo.colinknapp.com/n.js"' in source
    assert f'data-tracker-integrity="{NOTOMO_INTEGRITY}"' in source
    assert 'data-site-id="2"' not in source
    assert 'src="https://notomo.colinknapp.com/n.js"' not in source.replace(
        'data-tracker-src="https://notomo.colinknapp.com/n.js"', ""
    )
    assert "script-src 'self' 'wasm-unsafe-eval'" in source
    assert "https://notomo.colinknapp.com/n.js" in source
    assert "https://notomo.colinknapp.com/n-rrweb.js" in source
    assert connect_src in source
