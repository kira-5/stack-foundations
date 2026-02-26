from google.cloud import bigquery

from src.shared.configuration.config import env_config_manager


class BigQueryConnection:
    """Manages BigQuery connections."""

    _big_query_client = None
    dataset: str = env_config_manager.environment_settings.BIQUERY_DATASET

    @classmethod
    def get_big_query_connection(cls):
        """Creates or retrieves a BigQuery client connection.

        :return: BigQuery client
        """
        if cls._big_query_client is None:
            project_id = env_config_manager.get_dynamic_setting(
                "PROJECT_ID",
                "default-project",
            )
            dataset = cls.dataset
            print(
                f"Creating BigQuery client with project id: {project_id} and dataset {dataset}",
            )
            cls._big_query_client = bigquery.Client(
                project=project_id,
            )
        return cls._big_query_client
