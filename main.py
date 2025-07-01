"""
FastMCP Task Manager Server
A comprehensive example FastMCP server that provides task management capabilities.
Perfect for deployment on Railway.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastmcp import FastMCP
from pydantic import BaseModel, Field


# Data models
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    priority: Priority = Priority.MEDIUM
    created_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class CreateTaskRequest(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Priority = Priority.MEDIUM
    due_date: Optional[str] = None  # ISO format string
    tags: List[str] = Field(default_factory=list)


class UpdateTaskRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[str] = None  # ISO format string
    tags: Optional[List[str]] = None


# Simple in-memory storage (in production, use a real database)
class TaskStorage:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.next_id = 1
    
    def create_task(self, request: CreateTaskRequest) -> Task:
        task_id = str(self.next_id)
        self.next_id += 1
        
        due_date = None
        if request.due_date:
            due_date = datetime.fromisoformat(request.due_date.replace('Z', '+00:00'))
        
        task = Task(
            id=task_id,
            title=request.title,
            description=request.description,
            priority=request.priority,
            created_at=datetime.now(),
            due_date=due_date,
            tags=request.tags
        )
        
        self.tasks[task_id] = task
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, updates: UpdateTaskRequest) -> Optional[Task]:
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        update_data = {}
        for field, value in updates.model_dump(exclude_unset=True).items():
            if field == 'due_date' and value:
                update_data[field] = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif field == 'status' and value == TaskStatus.COMPLETED and task.status != TaskStatus.COMPLETED:
                update_data[field] = value
                update_data['completed_at'] = datetime.now()
            else:
                update_data[field] = value
        
        for field, value in update_data.items():
            setattr(task, field, value)
        
        return task
    
    def delete_task(self, task_id: str) -> bool:
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    def list_tasks(self, status: Optional[TaskStatus] = None, tag: Optional[str] = None) -> List[Task]:
        tasks = list(self.tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if tag:
            tasks = [t for t in tasks if tag in t.tags]
        
        # Sort by priority and creation date
        priority_order = {Priority.URGENT: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}
        tasks.sort(key=lambda t: (priority_order[t.priority], t.created_at))
        
        return tasks
    
    def get_stats(self) -> Dict[str, Any]:
        tasks = list(self.tasks.values())
        total = len(tasks)
        
        if total == 0:
            return {"total": 0, "by_status": {}, "by_priority": {}}
        
        by_status = {}
        by_priority = {}
        overdue = 0
        
        now = datetime.now()
        
        for task in tasks:
            # Count by status
            status_key = task.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1
            
            # Count by priority
            priority_key = task.priority.value
            by_priority[priority_key] = by_priority.get(priority_key, 0) + 1
            
            # Count overdue
            if task.due_date and task.due_date < now and task.status != TaskStatus.COMPLETED:
                overdue += 1
        
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "overdue": overdue
        }


# Initialize FastMCP server
mcp = FastMCP("Task Manager Server")

# Global storage instance
storage = TaskStorage()


# Tools (actions that can be performed)
@mcp.tool
def create_task(request: CreateTaskRequest) -> Dict[str, Any]:
    """Create a new task with the specified details."""
    try:
        task = storage.create_task(request)
        return {
            "success": True,
            "task": task.model_dump(mode='json'),
            "message": f"Task '{task.title}' created successfully with ID {task.id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
def get_task(task_id: str) -> Dict[str, Any]:
    """Retrieve a specific task by its ID."""
    task = storage.get_task(task_id)
    if task:
        return {"success": True, "task": task.model_dump(mode='json')}
    else:
        return {"success": False, "error": f"Task with ID {task_id} not found"}


@mcp.tool
def update_task(task_id: str, updates: UpdateTaskRequest) -> Dict[str, Any]:
    """Update an existing task with new information."""
    try:
        task = storage.update_task(task_id, updates)
        if task:
            return {
                "success": True,
                "task": task.model_dump(mode='json'),
                "message": f"Task {task_id} updated successfully"
            }
        else:
            return {"success": False, "error": f"Task with ID {task_id} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
def delete_task(task_id: str) -> Dict[str, Any]:
    """Delete a task by its ID."""
    if storage.delete_task(task_id):
        return {"success": True, "message": f"Task {task_id} deleted successfully"}
    else:
        return {"success": False, "error": f"Task with ID {task_id} not found"}


@mcp.tool
def list_tasks(status: Optional[str] = None, tag: Optional[str] = None) -> Dict[str, Any]:
    """List all tasks, optionally filtered by status or tag."""
    try:
        task_status = TaskStatus(status) if status else None
        tasks = storage.list_tasks(status=task_status, tag=tag)
        
        return {
            "success": True,
            "tasks": [task.model_dump(mode='json') for task in tasks],
            "count": len(tasks)
        }
    except ValueError as e:
        return {"success": False, "error": f"Invalid status: {status}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool
def complete_task(task_id: str) -> Dict[str, Any]:
    """Mark a task as completed."""
    updates = UpdateTaskRequest(status=TaskStatus.COMPLETED)
    return update_task(task_id, updates)


@mcp.tool
def get_task_stats() -> Dict[str, Any]:
    """Get statistics about all tasks."""
    try:
        stats = storage.get_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Resources (data that can be read)
@mcp.resource("task://{task_id}")
def get_task_resource(task_id: str) -> str:
    """Get detailed information about a specific task."""
    task = storage.get_task(task_id)
    if not task:
        return f"Task {task_id} not found"
    
    status_emoji = {
        TaskStatus.TODO: "📋",
        TaskStatus.IN_PROGRESS: "⏳",
        TaskStatus.COMPLETED: "✅",
        TaskStatus.CANCELLED: "❌"
    }
    
    priority_emoji = {
        Priority.LOW: "🟢",
        Priority.MEDIUM: "🟡",
        Priority.HIGH: "🟠",
        Priority.URGENT: "🔴"
    }
    
    result = f"""# Task: {task.title}

{status_emoji.get(task.status, "📋")} **Status**: {task.status.value.title()}
{priority_emoji.get(task.priority, "🟡")} **Priority**: {task.priority.value.title()}
📅 **Created**: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}
"""

    if task.description:
        result += f"\n📝 **Description**: {task.description}"
    
    if task.due_date:
        result += f"\n⏰ **Due Date**: {task.due_date.strftime('%Y-%m-%d %H:%M:%S')}"
    
    if task.completed_at:
        result += f"\n✅ **Completed**: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    if task.tags:
        result += f"\n🏷️ **Tags**: {', '.join(task.tags)}"
    
    return result


@mcp.resource("tasks://all")
def get_all_tasks_resource() -> str:
    """Get a summary of all tasks."""
    tasks = storage.list_tasks()
    stats = storage.get_stats()
    
    if not tasks:
        return "No tasks found. Create your first task to get started!"
    
    result = f"""# Task Summary

📊 **Statistics**:
- Total Tasks: {stats['total']}
- Overdue: {stats.get('overdue', 0)}

## Tasks by Status:
"""
    
    for status, count in stats['by_status'].items():
        result += f"- {status.replace('_', ' ').title()}: {count}\n"
    
    result += "\n## Recent Tasks:\n"
    
    # Show first 10 tasks
    for task in tasks[:10]:
        status_emoji = {"todo": "📋", "in_progress": "⏳", "completed": "✅", "cancelled": "❌"}
        priority_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "urgent": "🔴"}
        
        result += f"- {status_emoji.get(task.status.value, '📋')} {priority_emoji.get(task.priority.value, '🟡')} **{task.title}** (ID: {task.id})\n"
    
    if len(tasks) > 10:
        result += f"\n... and {len(tasks) - 10} more tasks"
    
    return result


# Prompts (templates for LLM interactions)
@mcp.prompt
def task_planning_prompt() -> str:
    """A prompt template for helping with task planning and organization."""
    return """You are a helpful task management assistant. Help the user plan and organize their tasks effectively.

Available task statuses:
- todo: Task is planned but not started
- in_progress: Task is currently being worked on
- completed: Task is finished
- cancelled: Task was cancelled

Available priorities:
- low: Nice to have, no rush
- medium: Normal priority
- high: Important, should be done soon
- urgent: Critical, needs immediate attention

When helping users:
1. Break down complex tasks into smaller, manageable pieces
2. Suggest appropriate priorities based on deadlines and importance
3. Recommend useful tags for categorization
4. Help identify dependencies between tasks
5. Suggest realistic timelines

Current task statistics: {get_task_stats()}

How can I help you organize your tasks today?"""


# Health check endpoint for Railway
@mcp.tool
def health_check() -> Dict[str, Any]:
    """Check if the server is running properly."""
    return {
        "status": "healthy",
        "server": "FastMCP Task Manager",
        "timestamp": datetime.now().isoformat(),
        "task_count": len(storage.tasks)
    }


# Server configuration for Railway deployment
if __name__ == "__main__":
    # Get port from environment (Railway sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the server
    print(f"Starting FastMCP Task Manager Server on port {port}")
    print("Available tools: create_task, get_task, update_task, delete_task, list_tasks, complete_task, get_task_stats, health_check")
    print("Available resources: task://{task_id}, tasks://all")
    print("Available prompts: task_planning_prompt")
    
    # For Railway deployment, use SSE transport instead of stdio
    # This enables HTTP-based communication suitable for web deployments
    mcp.run(transport="sse", host="0.0.0.0", port=port)
