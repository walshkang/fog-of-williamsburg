import json
from pathlib import Path

import pytest

from notion_sync.core import (
    Task,
    _simple_property_view,
    flatten_roadmap,
    format_notion_properties,
    needs_update,
)


def test_flatten_roadmap_basic():
    roadmap = {
        "phases": [
            {
                "phaseName": "Phase 1",
                "epics": [
                    {
                        "epicTitle": "Epic A",
                        "tasks": [
                            {
                                "id": "T1",
                                "title": "Task 1",
                                "status": "In Progress",
                                "priority": "High",
                                "owner": "Alex",
                                "description": "First task",
                                "dependencies": ["T0"],
                            },
                        ],
                    }
                ],
            }
        ]
    }

    tasks = flatten_roadmap(roadmap)
    assert len(tasks) == 1

    t = tasks[0]
    assert isinstance(t, Task)
    assert t.id == "T1"
    assert t.title == "Task 1"
    assert t.status == "In Progress"
    assert t.priority == "High"
    assert t.owner == "Alex"
    assert t.description == "First task"
    assert t.dependencies == ["T0"]
    assert t.phase_name == "Phase 1"
    assert t.epic_title == "Epic A"


def test_flatten_roadmap_skips_invalid_tasks(caplog):
    roadmap = {
        "phases": [
            {
                "phaseName": "Phase 1",
                "epics": [
                    {
                        "epicTitle": "Epic A",
                        "tasks": [
                            {"title": "Missing ID"},
                            {"id": "NO_TITLE"},
                        ],
                    }
                ],
            }
        ]
    }

    tasks = flatten_roadmap(roadmap)
    assert tasks == []
    # Optional: ensure warnings logged
    assert any("Skipping task with invalid or missing id" in rec.message for rec in caplog.records) or any(
        "Skipping task with invalid or missing title" in rec.message for rec in caplog.records
    )


def test_format_notion_properties_round_trip_simplified():
    task = Task(
        id="T1",
        title="Task 1",
        status="In Progress",
        priority="High",
        owner="Alex",
        description="First task",
        dependencies=["T0", "T2"],
        phase_name="Phase 1",
        epic_title="Epic A",
    )

    props = format_notion_properties(task)
    simple = _simple_property_view(props, "Task ID")

    assert simple["Task ID"] == "T1"
    assert simple["Title"] == "Task 1"
    assert simple["Status"] == "In Progress"
    assert simple["Priority"] == "High"
    assert simple["Owner"] == "Alex"
    assert simple["Phase"] == "Phase 1"
    assert simple["Epic"] == "Epic A"
    assert simple["Description"] == "First task"
    # multi_select is normalized/sorted in _simple_property_view
    assert simple["Dependencies"] == ("T0", "T2")


def test_needs_update_detects_changes():
    task = Task(
        id="T1",
        title="Task 1",
        status="In Progress",
        priority="High",
        owner="Alex",
        description="First task",
        dependencies=["T0"],
        phase_name="Phase 1",
        epic_title="Epic A",
    )

    new_props = format_notion_properties(task)

    existing_page = {
        "id": "page-1",
        "properties": json.loads(json.dumps(new_props)),  # deep copy
    }

    # No change -> False
    assert needs_update(existing_page, new_props) is False

    # Change status -> True
    modified = json.loads(json.dumps(new_props))
    modified["Status"]["select"]["name"] = "Done"
    assert needs_update(existing_page, modified) is True


