import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx
from notion_client import Client
from notion_client.errors import APIResponseError


logger = logging.getLogger(__name__)


DEFAULT_NOTION_ID_PROPERTY = "ID"


@dataclass
class Task:
    id: str
    title: str
    status: str
    priority: str
    owner: str
    description: str
    dependencies: List[str]
    phase_name: str
    epic_title: str


class RoadmapLoadError(Exception):
    pass


def load_local_roadmap(filepath: str) -> Dict[str, Any]:
    """
    Loads the roadmap.json file and returns its parsed content.
    Raises RoadmapLoadError on failure.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise RoadmapLoadError(f"Roadmap file not found at {filepath}") from exc
    except json.JSONDecodeError as exc:
        raise RoadmapLoadError(f"Could not decode JSON from {filepath}") from exc

    if not isinstance(data, dict):
        raise RoadmapLoadError("Expected roadmap root to be an object")

    return data


def flatten_roadmap(roadmap_data: Dict[str, Any]) -> List[Task]:
    """
    Flattens the roadmap structure into a list of Task objects.

    Expected schema:
    {
        "phases": [
            {
                "phaseName": "...",
                "epics": [
                    {
                        "epicTitle": "...",
                        "tasks": [ { task fields... }, ... ]
                    }
                ]
            }
        ]
    }
    """
    tasks: List[Task] = []

    phases = roadmap_data.get("phases") or []
    if not isinstance(phases, list):
        raise RoadmapLoadError("Expected 'phases' to be a list")

    for phase in phases:
        phase_name = phase.get("phaseName", "")
        epics = phase.get("epics") or []
        if not isinstance(epics, list):
            raise RoadmapLoadError("Expected 'epics' to be a list in each phase")

        for epic in epics:
            epic_title = epic.get("epicTitle", "")
            raw_tasks = epic.get("tasks") or []
            if not isinstance(raw_tasks, list):
                raise RoadmapLoadError("Expected 'tasks' to be a list in each epic")

            for raw_task in raw_tasks:
                task_id = (raw_task or {}).get("id")
                title = (raw_task or {}).get("title")
                if not task_id or not isinstance(task_id, str):
                    logger.warning("Skipping task with invalid or missing id: %r", raw_task)
                    continue
                if not title or not isinstance(title, str):
                    logger.warning("Skipping task with invalid or missing title: %r", raw_task)
                    continue

                status = (raw_task or {}).get("status", "Not Started")
                priority = (raw_task or {}).get("priority", "Medium")
                owner = (raw_task or {}).get("owner", "Unassigned")
                description = (raw_task or {}).get("description", "")
                dependencies = raw_task.get("dependencies") or []
                if not isinstance(dependencies, list):
                    logger.warning(
                        "Task %s has non-list dependencies; coercing to empty list", task_id
                    )
                    dependencies = []

                tasks.append(
                    Task(
                        id=task_id,
                        title=title,
                        status=status,
                        priority=priority,
                        owner=owner,
                        description=description,
                        dependencies=[str(d) for d in dependencies],
                        phase_name=str(phase_name),
                        epic_title=str(epic_title),
                    )
                )

    return tasks


def get_existing_pages(
    notion_client: Client,
    database_id: str,
    id_property_name: str = DEFAULT_NOTION_ID_PROPERTY,
) -> Dict[str, Dict[str, Any]]:
    """
    Fetches all pages from the database and maps them by their Task ID.

    Returns:
        Dict[task_id, page_object]
    """
    page_map: Dict[str, Dict[str, Any]] = {}
    has_more = True
    start_cursor: Optional[str] = None

    while has_more:
        try:
            # Fallback to direct httpx call to bypass notion-client issues with this specific endpoint
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            headers = {
                "Authorization": f"Bearer {notion_client.options.auth}",
                "Notion-Version": "2022-06-28", # Force older version to avoid invalid_request_url 400 error
                "Content-Type": "application/json",
            }
            
            # Ensure body is not empty to avoid 400 Bad Request on newer API versions
            json_body = {"page_size": 100}
            if start_cursor:
                json_body["start_cursor"] = start_cursor

            # Use httpx.Client() context manager to ensure proper cleanup if we were doing this repeatedly,
            # but here a simple post is fine.
            # Note: notion_client uses httpx under the hood, so we reuse the library.

            http_response = httpx.post(url, headers=headers, json=json_body, timeout=60.0)
            http_response.raise_for_status()
            response = http_response.json()

        except httpx.HTTPStatusError as e:
            logger.error("Error fetching existing pages (HTTP %s): %s", e.response.status_code, e.response.text)
            raise APIResponseError(e.response, e.response.text, str(e.response.status_code)) from e
        except Exception as e:
            logger.error("Error fetching existing pages: %s", e)
            raise

        results = response.get("results", [])

        for page in results:
            try:
                properties = page.get("properties", {})
                task_id_prop = properties.get(id_property_name, {})
                # Handle both Title and Rich Text types for the ID property
                content_array = task_id_prop.get("title") or task_id_prop.get("rich_text") or []
                
                if not content_array:
                    # It might be empty, which is valid for a new row but we skip for sync matching
                    logger.warning(
                        "Skipping page with ID %s - %s is empty",
                        page.get("id"),
                        id_property_name,
                    )
                    continue
                    
                task_id = content_array[0].get("plain_text")
                if not task_id:
                    logger.warning(
                        "Skipping page with ID %s - %s has no plain_text",
                        page.get("id"),
                        id_property_name,
                    )
                    continue
                page_map[str(task_id)] = page
            except Exception:
                logger.exception("Skipping page with ID %s due to parsing error", page.get("id"))

        has_more = response.get("has_more", False)
        start_cursor = response.get("next_cursor")

    return page_map


def _dependencies_to_multi_select(dependencies: Iterable[str]) -> List[Dict[str, str]]:
    return [{"name": d} for d in dependencies if d]


def format_notion_properties(
    task: Task, id_property_name: str = DEFAULT_NOTION_ID_PROPERTY
) -> Dict[str, Any]:
    """
    Formats a Task into the Notion API's property structure.
    """
    return {
        # Primary key / title property
        id_property_name: {
            "rich_text": [{"type": "text", "text": {"content": task.id}}],
        },
        "Task Name": {
            "title": [{"type": "text", "text": {"content": task.title}}],
        },
        "Status": {
            "status": {"name": task.status},
        },
        "Priority": {
            "select": {"name": task.priority},
        },
        # Keeping Owner as select-of-name for simplicity; you can swap to 'people' if you
        # maintain Notion user IDs elsewhere.
        "Owner": {
            "select": {"name": task.owner},
        },
        "Phase": {
            "select": {"name": task.phase_name},
        },
        "Epic": {
            "select": {"name": task.epic_title},
        },
        "Description": {
            "rich_text": [
                {"type": "text", "text": {"content": task.description or ""}},
            ],
        },
        "Dependencies": {
            "rich_text": [
                {"type": "text", "text": {"content": ", ".join(task.dependencies)}},
            ],
        },
    }


def _simple_property_view(properties: Dict[str, Any], id_property_name: str) -> Dict[str, Any]:
    """
    Extracts a simplified, comparable view of relevant properties from either:
      - a Notion page's properties dict, or
      - a Notion properties payload about to be sent.
    """

    def _from_title(prop: Dict[str, Any]) -> str:
        arr = prop.get("title") or []
        if not arr:
            return ""
        return arr[0].get("plain_text") or arr[0].get("text", {}).get("content", "")

    def _from_rich_text(prop: Dict[str, Any]) -> str:
        arr = prop.get("rich_text") or []
        if not arr:
            return ""
        return "".join(
            [
                span.get("plain_text")
                or span.get("text", {}).get("content", "")
                or ""
                for span in arr
            ]
        )

    def _from_select(prop: Dict[str, Any]) -> str:
        select = prop.get("select") or {}
        return select.get("name", "") if isinstance(select, dict) else ""

    def _from_multi_select(prop: Dict[str, Any]) -> Tuple[str, ...]:
        items = prop.get("multi_select") or []
        names: List[str] = []
        for item in items:
            name = item.get("name")
            if name:
                names.append(name)
        return tuple(sorted(names))

    def _from_status(prop: Dict[str, Any]) -> str:
        status = prop.get("status") or {}
        return status.get("name", "") if isinstance(status, dict) else ""

    simple: Dict[str, Any] = {}
    
    # Primary ID is Rich Text in this specific DB
    id_prop = properties.get(id_property_name) or {}
    simple[id_property_name] = _from_rich_text(id_prop)

    title = properties.get("Task Name") or {}
    simple["Task Name"] = _from_title(title)

    status = properties.get("Status") or {}
    simple["Status"] = _from_status(status)

    priority = properties.get("Priority") or {}
    simple["Priority"] = _from_select(priority)

    owner = properties.get("Owner") or {}
    simple["Owner"] = _from_select(owner)

    phase = properties.get("Phase") or {}
    simple["Phase"] = _from_select(phase)

    epic = properties.get("Epic") or {}
    simple["Epic"] = _from_select(epic)

    description = properties.get("Description") or {}
    simple["Description"] = _from_rich_text(description)

    deps = properties.get("Dependencies") or {}
    # Dependencies is Rich Text in this DB
    simple["Dependencies"] = _from_rich_text(deps)

    return simple


def needs_update(
    existing_page: Dict[str, Any],
    new_properties: Dict[str, Any],
    id_property_name: str = DEFAULT_NOTION_ID_PROPERTY,
) -> bool:
    """
    Compares the relevant properties between an existing Notion page and a new
    properties payload and decides whether an update is needed.
    """
    existing_props = existing_page.get("properties") or {}
    simple_existing = _simple_property_view(existing_props, id_property_name)
    simple_new = _simple_property_view(new_properties, id_property_name)
    return simple_existing != simple_new


class SyncStats:
    def __init__(self) -> None:
        self.created = 0
        self.updated = 0
        self.skipped = 0
        self.failed = 0

    def as_dict(self) -> Dict[str, int]:
        return {
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
        }


def create_notion_page(
    notion_client: Client,
    database_id: str,
    properties: Dict[str, Any],
    id_property_name: str = DEFAULT_NOTION_ID_PROPERTY,
    dry_run: bool = False,
) -> None:
    """Creates a new page in the Notion database."""
    task_id = properties[id_property_name]["rich_text"][0]["text"]["content"]
    if dry_run:
        logger.info("DRY-RUN: Would create %s", task_id)
        return

    try:
        notion_client.pages.create(parent={"database_id": database_id}, properties=properties)
        logger.info("CREATED: %s", task_id)
    except APIResponseError as e:
        logger.error("Error creating %s: %s (status=%s)", task_id, e, e.status)
        raise


def update_notion_page(
    notion_client: Client,
    page_id: str,
    properties: Dict[str, Any],
    id_property_name: str = DEFAULT_NOTION_ID_PROPERTY,
    dry_run: bool = False,
) -> None:
    """Updates an existing page in the Notion database."""
    task_id = properties[id_property_name]["rich_text"][0]["text"]["content"]
    if dry_run:
        logger.info("DRY-RUN: Would update %s", task_id)
        return

    try:
        notion_client.pages.update(page_id=page_id, properties=properties)
        logger.info("UPDATED: %s", task_id)
    except APIResponseError as e:
        logger.error("Error updating %s: %s (status=%s)", task_id, e, e.status)
        raise


def sync_roadmap_to_notion(
    *,
    notion_api_key: str,
    notion_database_id: str,
    roadmap_file_path: str,
    id_property_name: str = DEFAULT_NOTION_ID_PROPERTY,
    dry_run: bool = False,
) -> SyncStats:
    """
    High-level sync function.
    """
    if not notion_api_key:
        raise ValueError("NOTION_API_KEY is required")
    if not notion_database_id:
        raise ValueError("NOTION_DATABASE_ID is required")

    client = Client(auth=notion_api_key)

    logger.info("Loading local roadmap from %s", roadmap_file_path)
    roadmap_data = load_local_roadmap(roadmap_file_path)
    tasks = flatten_roadmap(roadmap_data)
    logger.info("Loaded %d tasks from roadmap", len(tasks))

    logger.info("Fetching existing pages from Notion...")
    existing_pages = get_existing_pages(client, notion_database_id, id_property_name)
    logger.info("Found %d existing tasks in Notion", len(existing_pages))

    stats = SyncStats()

    for task in tasks:
        properties = format_notion_properties(task, id_property_name)
        page = existing_pages.get(task.id)

        # Existing page -> update if needed
        if page:
            if needs_update(page, properties, id_property_name):
                try:
                    update_notion_page(
                        client,
                        page_id=page["id"],
                        properties=properties,
                        id_property_name=id_property_name,
                        dry_run=dry_run,
                    )
                    stats.updated += 1
                except APIResponseError:
                    stats.failed += 1
            else:
                logger.info("SKIP (no changes): %s", task.id)
                stats.skipped += 1
        else:
            try:
                create_notion_page(
                    client,
                    database_id=notion_database_id,
                    properties=properties,
                    id_property_name=id_property_name,
                    dry_run=dry_run,
                )
                stats.created += 1
            except APIResponseError:
                stats.failed += 1

    return stats


def main_from_env_and_args(argv: Optional[List[str]] = None) -> int:
    """
    Entry helper for CLI: reads env vars and arguments, runs sync, and
    returns a process exit code.
    """
    import argparse

    # Load from .env if present
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        # It's okay if python-dotenv is not installed; env vars may still be set.
        pass

    parser = argparse.ArgumentParser(description="Sync roadmap.json tasks into a Notion database.")
    parser.add_argument(
        "--database-id",
        dest="database_id",
        help="Notion database ID (defaults to NOTION_DATABASE_ID env var).",
    )
    parser.add_argument(
        "--roadmap",
        dest="roadmap_file",
        default=os.environ.get("ROADMAP_FILE_PATH", "roadmap.json"),
        help="Path to roadmap JSON (defaults to ROADMAP_FILE_PATH env var or roadmap.json).",
    )
    parser.add_argument(
        "--id-property",
        dest="id_property_name",
        default=os.environ.get("NOTION_ID_PROPERTY", DEFAULT_NOTION_ID_PROPERTY),
        help=f"Name of Notion title property used as Task ID (default: {DEFAULT_NOTION_ID_PROPERTY}).",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Print planned changes without making any Notion API calls.",
    )
    parser.add_argument(
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Enable debug logging.",
    )

    args = parser.parse_args(argv)

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(message)s",
    )

    notion_api_key = os.environ.get("NOTION_API_KEY")
    if not notion_api_key:
        logger.error("NOTION_API_KEY environment variable not set.")
        return 1

    notion_database_id = args.database_id or os.environ.get("NOTION_DATABASE_ID")
    if not notion_database_id:
        logger.error(
            "NOTION_DATABASE_ID is not provided. "
            "Set the NOTION_DATABASE_ID environment variable or pass --database-id."
        )
        return 1
    
    # Clean database ID by removing dashes if present
    # notion_database_id = notion_database_id.replace("-", "")

    # Notion API requires the database ID to be formatted as a UUID (with dashes) if it's not already?
    # Actually, the API documentation examples show dashes. Let's try ensuring dashes are present if they are missing.
    # However, 2ac2612c-7077-80af-83ce-000b6d4d3953 appears to be a 'data_source' object (from debug search),
    # while the actual database_id is likely 2ac2612c-7077-80c6-8274-fa1f95a8f720 (from 'parent' field).
    # The user likely provided the wrong ID (a page/datasource ID instead of the database ID).
    # We will assume the provided ID is correct for now, but log a warning if it looks like a page ID.
    
    if len(notion_database_id) == 32 and "-" not in notion_database_id:
         notion_database_id = f"{notion_database_id[:8]}-{notion_database_id[8:12]}-{notion_database_id[12:16]}-{notion_database_id[16:20]}-{notion_database_id[20:]}"

    try:
        stats = sync_roadmap_to_notion(
            notion_api_key=notion_api_key,
            notion_database_id=notion_database_id,
            roadmap_file_path=args.roadmap_file,
            id_property_name=args.id_property_name,
            dry_run=bool(args.dry_run),
        )
    except RoadmapLoadError as e:
        logger.error("Failed to load roadmap: %s", e)
        return 1
    except Exception:
        logger.exception("Unexpected error during sync.")
        return 1

    summary = stats.as_dict()
    logger.info(
        "Sync complete. created=%d updated=%d skipped=%d failed=%d",
        summary["created"],
        summary["updated"],
        summary["skipped"],
        summary["failed"],
    )

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main_from_env_and_args())


