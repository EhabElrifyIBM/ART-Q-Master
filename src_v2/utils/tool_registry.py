"""
Unified tool registry for the src_v2 migration workspace (Phase 6.1 Enhanced).

Enhanced with icons and user-friendly descriptions for the modernized main menu.
"""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional


@dataclass(frozen=True)
class ToolDefinition:
    """
    Describes a v2 tool entry exposed in the unified shell.
    
    Attributes:
        tool_id: Unique identifier for the tool
        display_name: User-friendly name shown in UI
        description: User-friendly description (no technical jargon)
        area: Category/area (Operations, Automation, Analytics)
        status: Internal status (not shown in UI)
        icon: Emoji icon for visual identification
    """

    tool_id: str
    display_name: str
    description: str
    area: str
    status: str
    icon: str = "📦"  # Default icon


_TOOL_DEFINITIONS: List[ToolDefinition] = [
    ToolDefinition(
        tool_id="qcontrol",
        display_name="ART Q Control",
        description="Launch AutoSender, CaseReviewer, and CompaniesProcess from a modern dispatcher with agent-aware configuration",
        area="Automation",
        status="modernized-phase-6.5-dispatcher",
        icon="🎯",
    ),
    ToolDefinition(
        tool_id="assigner",
        display_name="Assigner",
        description="Assign cases to team members with smart distribution and workload balancing",
        area="Operations",
        status="modernized-phase-6.4",
        icon="📊",
    ),
    ToolDefinition(
        tool_id="daily_merger",
        display_name="Daily Case Merger",
        description="Merge up to 30 daily Active Cases workbooks into one deduplicated output with All Cases, Chat Agent, and Companies sheets",
        area="Operations",
        status="new",
        icon="📅",
    ),
    ToolDefinition(
        tool_id="monthly_merger",
        display_name="Monthly Case Merger",
        description="Merge multiple monthly output workbooks into one deduplicated result — latest month always wins across All Cases, Chat Agent, and Companies sheets",
        area="Operations",
        status="new",
        icon="📆",
    ),
    ToolDefinition(
        tool_id="merger",
        display_name="Merger",
        description="Merge multiple Excel files into a single consolidated dataset with sheet selection and column mapping",
        area="Operations",
        status="migrated-phase-6.3",
        icon="🔗",
    ),
    ToolDefinition(
        tool_id="archiver",
        display_name="Case Archiver",
        description="Archive closed cases from Excel workbooks by month or age with automatic backups",
        area="Operations",
        status="migrated-phase-6.2",
        icon="📦",
    ),
    ToolDefinition(
        tool_id="reachrate",
        display_name="Reach Rate Calculator",
        description="Calculate team performance metrics and customer reach statistics across SMS, Email, and Phone channels",
        area="Analytics",
        status="modernized-phase-6.9",
        icon="📈",
    ),
]


def get_tool_definitions() -> Iterable[ToolDefinition]:
    """Return all registered v2 tool definitions."""
    return list(_TOOL_DEFINITIONS)


def get_shell_cards() -> List[tuple[str, str, str]]:
    """Return the simple card tuple format required by the unified shell."""
    return [
        (
            tool.tool_id,
            tool.display_name,
            f"{tool.description} [{tool.area} · {tool.status}]",
        )
        for tool in _TOOL_DEFINITIONS
    ]


def get_tool_status_map() -> Dict[str, str]:
    """Return tool status values keyed by tool identifier."""
    return {tool.tool_id: tool.status for tool in _TOOL_DEFINITIONS}


def get_tool_definition(tool_id: str) -> ToolDefinition:
    """Return a single tool definition by identifier."""
    for tool in _TOOL_DEFINITIONS:
        if tool.tool_id == tool_id:
            return tool
    raise KeyError(f"Unknown tool_id: {tool_id}")

# Made with Bob
