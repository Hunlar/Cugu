"""GROUP CINEMA content providers."""

from .puhutv import search_catalog as search_puhutv
from .hdcehennemi import search_catalog as search_hdcehennemi
from .internet_archive import search_catalog as search_internet_archive


async def search_catalog(source: str, query: str):
    """Search a configured catalog provider."""

    providers = {
        "puhutv": search_puhutv,
        "hd_film_cehennemi": search_hdcehennemi,
        "internet_archive": search_internet_archive,
    }

    provider = providers.get(source)
    if provider is None:
        raise ValueError(f"Unknown provider: {source}")

    return await provider(query)
