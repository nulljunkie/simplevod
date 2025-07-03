from typing import Any, Dict, List, Optional, Tuple
import motor.motor_asyncio
import beanie
from models.models import StoredVideo
from .config import logger, mongo_config

class MongoDBClient:
    """A client for interacting with MongoDB using Motor's async driver."""

    def __init__(self, url: str = mongo_config.url, db_name: str = mongo_config.db_name) -> None:
        """
        Initialize MongoDB client and connect to the specified database.

        Args:
            url: MongoDB connection URL.
            db_name: Name of the database to use.

        Raises:
            RuntimeError: If connection to MongoDB fails.
        """
        self._client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self._db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
        self._connect(url, db_name)

    def _connect(self, url: str, db_name: str) -> None:
        """Establish connection to MongoDB and set up database."""
        try:
            self._client = motor.motor_asyncio.AsyncIOMotorClient(url)
            self._db = self._client[db_name]
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise RuntimeError(f"MongoDB connection failed: {str(e)}")

    async def ping(self) -> bool:
        """Check if MongoDB is responsive.

        Returns:
            bool: True if ping succeeds, False otherwise.
        """
        try:
            await self._db.command("ping")
            logger.debug("MongoDB ping successful")
            return True
        except Exception as e:
            logger.error(f"MongoDB ping failed: {str(e)}")
            return False

    async def insert_one(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a single document into a collection.

        Args:
            collection: Name of the collection.
            document: Document to insert.

        Returns:
            str: ID of the inserted document.

        Raises:
            RuntimeError: If insertion fails.
        """
        try:
            result = await self._db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document into '{collection}': {str(e)}")
            raise RuntimeError(f"Insert into '{collection}' failed: {str(e)}")

    async def find(
        self,
        collection: str,
        query: Dict[str, Any],
        sort: Optional[List[Tuple[str, Any]]] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Find documents in a collection based on a query.

        Args:
            collection: Name of the collection.
            query: Query filter for documents.
            sort: List of (field, direction) tuples for sorting (optional).
            skip: Number of documents to skip (default: 0).
            limit: Maximum number of documents to return (default: 100).

        Returns:
            List[Dict[str, Any]]: List of matching documents.

        Raises:
            RuntimeError: If query execution fails.
        """
        try:
            cursor = self._db[collection].find(query)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to find documents in '{collection}': {str(e)}")
            raise RuntimeError(f"Find in '{collection}' failed: {str(e)}")
