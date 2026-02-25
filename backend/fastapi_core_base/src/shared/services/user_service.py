from src.shared.services.logging_service import LoggingService
from src.shared.services.database_service import database_service

logger = LoggingService.get_logger(__name__)

class UserService:
    """Service for user-related operations."""

    @staticmethod
    async def get_email_by_user_id(user_id: int | str) -> dict | None:
        """Fetch user email performance by ID.
        
        Note: Currently mapped to base_pricing.bp_user_master.
        Adjust schema/table as per system evolution.
        """
        logger.info(f"🔍 Fetching email for user_id: {user_id}")
        query = f"""
            SELECT email FROM base_pricing.bp_user_master 
            WHERE user_id = '{user_id}' 
            AND is_active = TRUE
        """
        try:
            res = await database_service.execute_async_query(query=query)
            if res and isinstance(res, list) and len(res) > 0:
                return {"email": res[0].get("email")}
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching email for user {user_id}: {e}")
            return None

user_service = UserService()
