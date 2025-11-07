from sophie_bot.config import CONFIG
from sophie_bot.db.models.federations import Federation


class FederationPermissionService:
    """Service for checking federation permissions."""

    @staticmethod
    def is_federation_owner(federation: Federation, user_id: int) -> bool:
        """Check if user is the federation owner."""
        return federation.creator == user_id or user_id == CONFIG.owner_id

    @staticmethod
    def is_federation_admin(federation: Federation, user_id: int) -> bool:
        """Check if user is a federation admin."""
        if FederationPermissionService.is_federation_owner(federation, user_id):
            return True
        return user_id in (federation.admins or [])

    @staticmethod
    def can_manage_federation(federation: Federation, user_id: int) -> bool:
        """Check if user can manage federation (owner or admin)."""
        return FederationPermissionService.is_federation_admin(federation, user_id)

    @staticmethod
    def can_ban_in_federation(federation: Federation, user_id: int) -> bool:
        """Check if user can ban in federation."""
        return FederationPermissionService.is_federation_admin(federation, user_id)

    @staticmethod
    def validate_federation_owner(federation: Federation, user_id: int) -> bool:
        """Validate that user is federation owner."""
        return FederationPermissionService.is_federation_owner(federation, user_id)

    @staticmethod
    def validate_federation_admin(federation: Federation, user_id: int) -> bool:
        """Validate that user is federation admin."""
        return FederationPermissionService.is_federation_admin(federation, user_id)
