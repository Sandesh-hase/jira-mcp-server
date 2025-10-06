import os
import base64
import httpx
from mcp.server.fastmcp import FastMCP

JIRA_DOMAIN="your jira domain"
JIRA_EMAIL="your email id"
JIRA_TOKEN="your jira token"



auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
auth_bytes = base64.b64encode(auth_str.encode()).decode()

HEADERS = {
    "Authorization": f"Basic {auth_bytes}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}



mcp = FastMCP(name="jira_mcp_connector")

# ===========================================================
#                 Helper: Atlassian Doc Format
# ===========================================================

def adf_paragraph(text: str) -> dict:
    """Return Atlassian Document Format (ADF) paragraph block."""
    return {"type": "paragraph", "content": [{"type": "text", "text": text}]}


# ===========================================================
#                 Tool 1: Create Jira Issue
# ===========================================================

@mcp.tool()
async def create_issue(
    project_key: str,
    summary: str,
    description: str = "Created via MCP Jira Connector",
    issue_type: str = "Story",
    acceptance_criteria: str = None,
    story_points: float = None
) -> dict:
    """
    Create a new Jira issue dynamically with optional acceptance criteria and story points.

    Parameters
    ----------
    project_key : str
        The Jira project key (e.g., "SCRUM")
    summary : str
        The title of the story
    description : str, optional
        Story description (ADF format handled automatically)
    issue_type : str, optional
        Type of issue (Story, Task, Bug, etc.)
    acceptance_criteria : str, optional
        Text for acceptance criteria (appended in description)
    story_points : float, optional
        Story point value for estimation
    """

    description_adf = {
        "type": "doc",
        "version": 1,
        "content": [adf_paragraph(description)]
    }

    if acceptance_criteria:
        description_adf["content"].append(
            adf_paragraph(f"Acceptance Criteria: {acceptance_criteria}")
        )

    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": description_adf
        }
    }

    if story_points:
        payload["fields"]["customfield_10016"] = story_points  # Default field for Story Points

    async with httpx.AsyncClient() as client:
        res = await client.post(f"{JIRA_DOMAIN}/rest/api/3/issue", json=payload, headers=HEADERS)

    if res.status_code == 201:
        data = res.json()
        return {
            "status": "success",
            "key": data.get("key"),
            "id": data.get("id"),
            "message": f"Issue {data.get('key')} created successfully."
        }
    else:
        return {"status": "error", "details": res.text}


# ===========================================================
#                 Tool 2: Search Jira Issues
# ===========================================================

@mcp.tool()
async def search_issues(
    query: str = None,
    jql: str = None,
    max_results: int = 10
) -> list:
    """
    Search Jira issues.

    Parameters
    ----------
    query : str, optional
        Free-text keyword search (matches summary, description, etc.)
    jql : str, optional
        Jira Query Language string for advanced filtering
    max_results : int, optional
        Number of issues to fetch (default = 10)
    """

    params = {"maxResults": max_results}
    if jql:
        params["jql"] = jql
    elif query:
        params["jql"] = f'text ~ "{query}"'

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{JIRA_DOMAIN}/rest/api/3/search", headers=HEADERS, params=params)

    if res.status_code == 200:
        issues = res.json().get("issues", [])
        return [
            {
                "key": issue["key"],
                "summary": issue["fields"]["summary"],
                "status": issue["fields"]["status"]["name"],
                "issuetype": issue["fields"]["issuetype"]["name"]
            }
            for issue in issues
        ]
    else:
        return {"status": "error", "details": res.text}

@mcp.tool()
async def assign_issue(issue_key: str, assignee_email: str) -> dict:
    """
    Assign a Jira issue to a specific user.

    Parameters
    ----------
    issue_key : str
        Jira issue key (e.g., "SCRUM-101")
    assignee_email : str
        Email of the user to assign
    """

    payload = {"accountId": None}

    async with httpx.AsyncClient() as client:
        # Get user ID from email
        user_res = await client.get(f"{JIRA_DOMAIN}/rest/api/3/user/search", headers=HEADERS, params={"query": assignee_email})
        if user_res.status_code == 200:
            users = user_res.json()
            if users:
                payload["accountId"] = users[0]["accountId"]
            else:
                return {"status": "error", "message": f"No user found with email {assignee_email}"}
        else:
            return {"status": "error", "details": user_res.text}

        res = await client.put(f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/assignee", headers=HEADERS, json=payload)

    return {"status": "success", "message": f"Issue {issue_key} assigned to {assignee_email}."} if res.status_code == 204 else {"status": "error", "details": res.text}

@mcp.tool()
async def update_issue_status(issue_key: str, new_status: str) -> dict:
    """
    Transition a Jira issue to a new status.

    Parameters
    ----------
    issue_key : str
        The Jira issue key (e.g., "SCRUM-123")
    new_status : str
        The target status name (e.g., "In Progress", "Done")
    """

    async with httpx.AsyncClient() as client:
        transitions = await client.get(f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions", headers=HEADERS)
        if transitions.status_code != 200:
            return {"status": "error", "details": transitions.text}

        data = transitions.json()
        available = {t["name"]: t["id"] for t in data.get("transitions", [])}

        if new_status not in available:
            return {"status": "error", "message": f"Status '{new_status}' not found for this issue."}

        payload = {"transition": {"id": available[new_status]}}
        res = await client.post(f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/transitions", headers=HEADERS, json=payload)

        return {"status": "success", "message": f"Issue {issue_key} moved to {new_status}."} if res.status_code == 204 else {"status": "error", "details": res.text}

@mcp.tool()
async def add_comment(issue_key: str, comment: str) -> dict:
    """
    Add a comment to an existing Jira issue.

    Parameters
    ----------
    issue_key : str
        The Jira issue key
    comment : str
        The comment text
    """

    # Jira Cloud requires ADF (Atlassian Document Format)
    payload = {
        "body": {
            "version": 1,
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": comment
                        }
                    ]
                }
            ]
        }
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(
            f"{JIRA_DOMAIN}/rest/api/3/issue/{issue_key}/comment",
            headers={
                "Authorization": f"Basic {auth_bytes}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=payload
        )

    if res.status_code == 201:
        data = res.json()
        return {
            "status": "success",
            "message": f"Comment added to {issue_key}.",
            "comment_id": data.get("id"),
            "author": data.get("author", {}).get("displayName", "Unknown")
        }
    else:
        return {
            "status": "error",
            "status_code": res.status_code,
            "details": res.text
        }

