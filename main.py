from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI()
DB_NAME = "tasks.db"

tasks = [
    {"id": 1, "title": "Buy groceries", "done": True},
    {"id": 2, "title": "Work on assignments", "done": False},
    {"id": 3, "title": "Visit grandma", "done": False},
]


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


@app.get("/tasks")
def get_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return [row_to_task(row) for row in rows]


@app.get("/tasks/{id}")
def get_task(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return row_to_task(row)

    return JSONResponse(status_code=404, content={"error": "Task not found"})


@app.post("/tasks", status_code=201)
def create_task(task: dict):
    title = task.get("title", "").strip()
    if not title:
        return JSONResponse(status_code=400, content={"error": "Title is required"})

    next_id = max(task["id"] for task in tasks) + 1 if tasks else 1
    new_task = {"id": next_id, "title": title, "done": False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{id}")
def update_task(id: int, body: dict):
    if not body:
        return JSONResponse(status_code=400, content={"error": "Body is required"})

    for task in tasks:
        if task["id"] == id:
            if "title" in body:
                title = body["title"].strip()
                if not title:
                    return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
                task["title"] = title

            if "done" in body:
                task["done"] = body["done"]

            return task

    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})


@app.delete("/tasks/{id}")
def delete_task(id: int):
    for i, task in enumerate(tasks):
        if task["id"] == id:
            del tasks[i]
            return Response(status_code=204)

    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})