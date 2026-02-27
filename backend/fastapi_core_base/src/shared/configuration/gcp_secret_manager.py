from google.cloud import secretmanager

import logging
logger = logging.getLogger(__name__)


class GoogleSecretManagerLoader:
    def __init__(
        self,
        project_id,
        project_number,
        secret_name,
        secret_version,
        env,
    ):
        self.secret_client = secretmanager.SecretManagerServiceAsyncClient()
        self.project_id = project_id
        self.project_number = project_number
        self.secret_name = secret_name
        self.secret_version = secret_version
        self.env = env

    async def fetch_secrets_from_gcp(self):
        secret_name = f"{self.secret_name}_{self.env}"
        secret_manager_resource_id = self.secret_client.secret_version_path(
            self.project_id,
            secret_name,
            self.secret_version,
        )
        try:
            logger.info(f"Fetching secret from GCP: {secret_manager_resource_id}")
            response = await self.secret_client.access_secret_version(
                request={"name": secret_manager_resource_id},
            )
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            if "403" in str(e) or "Forbidden" in str(e) or "Permission" in str(e):
                logger.warning(
                    f"Permission denied while fetching GCP secret (expected in local dev): {e}",
                )
            else:
                logger.error(
                    f"Error fetching GCP secret - {secret_manager_resource_id}: {e}",
                )
            return ""
