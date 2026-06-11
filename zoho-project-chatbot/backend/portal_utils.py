"""Portal slug helpers for Zoho Projects API URLs.

Zoho API paths use the portal NAME/slug (e.g. nithishish285gmaildotcom),
not the numeric portal ID (e.g. 60073890034).
"""

DEFAULT_PORTAL_SLUG = "nithishish285gmaildotcom"


def is_numeric_portal_id(value: str | None) -> bool:
    if not value:
        return False
    return str(value).strip().isdigit()


def slug_from_portal_dict(portal: dict) -> str:
    """Extract URL slug from a Zoho portal API object."""
    for key in ("link_name", "name", "portal_name"):
        val = portal.get(key)
        if val and not is_numeric_portal_id(str(val)):
            return str(val)
    # Fallback: if only numeric id is present, use default slug
    return DEFAULT_PORTAL_SLUG


def resolve_portal_slug(
    portal_id: str | None = None,
    portal_name: str | None = None,
) -> str:
    """Return portal NAME/slug for /portal/{slug}/... URLs (never numeric ID)."""
    if portal_name and not is_numeric_portal_id(str(portal_name)):
        return str(portal_name)
    if portal_id and not is_numeric_portal_id(str(portal_id)):
        return str(portal_id)
    return DEFAULT_PORTAL_SLUG
