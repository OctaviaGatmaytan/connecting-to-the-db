from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI()
DB_NAME = "tasks.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        done INTEGER NOT NULL DEFAULT 0
    )
    """)

    cur.execute("SELECT COUNT(*) FROM tasks")
    count = cur.fetchone()[0]

    if count == 0:
        cur.executemany(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            [
                ("Buy groceries", 1),
                ("Work on assignments", 0),
                ("Visit grandma", 0),
            ],
        )

    conn.commit()
    conn.close()


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


init_db()


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

    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})


@app.post("/tasks", status_code=201)
def create_task(task: dict):
    title = task.get("title", "").strip()
    if not title:
        return JSONResponse(status_code=400, content={"error": "Title is required"})

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0))
    conn.commit()

    new_id = cur.lastrowid
    cur.execute("SELECT id, title, done FROM tasks WHERE id = ?", (new_id,))
    row = cur.fetchone()
    conn.close()

    return row_to_task(row)


@app.put("/tasks/{id}")
def update_task(id: int, body: dict):
    if not body:
        return JSONResponse(status_code=400, content={"error": "Body is required"})

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    title = row["title"]
    done = row["done"]

    if "title" in body:
        new_title = body["title"].strip()
        if not new_title:
            conn.close()
            return JSONResponse(status_code=400, content={"error": "Title cannot be empty"})
        title = new_title

    if "done" in body:
        done = 1 if body["done"] else 0

    cur.execute(
        "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
        (title, done, id),
    )
    conn.commit()

    cur.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
    updated = cur.fetchone()
    conn.close()

    return row_to_task(updated)


@app.delete("/tasks/{id}")
def delete_task(id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (id,))

    if cur.rowcount == 0:
        conn.close()
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    conn.commit()
    conn.close()
    return Response(status_code=204)