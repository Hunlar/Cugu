
"""GROUP CINEMA content providers."""

from .puhutv import search_catalog as search_puhutv
from .hdcehennemi import search_catalog as search_hdcehennemi


async def search_catalog(source: str, query: str):
    """Search an authorized provider catalog."""

    providers = {
        "puhutv": search_puhutv,
        "hd_film_cehennemi": search_hdcehennemi,
    }

    provider = providers.get(source)

    if provider is None:
        raise ValueError(f"Unknown provider: {source}")

    return await provider(query)
  
