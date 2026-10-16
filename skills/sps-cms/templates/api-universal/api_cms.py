"""
SPS-CMS Universal Python Drop-in Router (FastAPI & Flask compatible)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import sqlite3
import json

router = APIRouter(prefix="/api/cms", tags=["SPS-CMS"])

class SavePageRequest(BaseModel):
    slug: str
    content: Dict[str, Any]

def get_db():
    conn = sqlite3.connect("data/sps_cms.db")
    conn.row_factory = sqlite3.Row
    return conn

@router.post("/save-page")
def save_page(req: SavePageRequest):
    conn = get_db()
    cursor = conn.cursor()
    content_json = json.dumps(req.content)
    cursor.execute("""
        INSERT INTO sps_pages (slug, title, content_json)
        VALUES (?, ?, ?)
        ON CONFLICT(slug) DO UPDATE SET content_json=excluded.content_json, updated_at=CURRENT_TIMESTAMP
    """, (req.slug, req.slug, content_json))
    conn.commit()
    conn.close()
    return {"success": True}

@router.get("/collections/{collection_name}")
def get_collection(collection_name: str, only_homepage: bool = False):
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM sps_collections WHERE collection_name = ?"
    params = [collection_name]
    if only_homepage:
        query += " AND show_on_homepage = 1"
    query += " ORDER BY order_index ASC, created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    items = []
    for row in rows:
        d = dict(row)
        d["data"] = json.loads(d["data_json"]) if d.get("data_json") else {}
        items.append(d)
    conn.close()
    return {"items": items}
