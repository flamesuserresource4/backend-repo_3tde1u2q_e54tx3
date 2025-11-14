import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Project, ContactMessage

app = FastAPI(title="Portfolio API", description="Backend for portfolio site")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Portfolio API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = getattr(db, 'name', None) or ("✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set")
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# Basic in-memory cache for initial content seeding avoidance (not for data storage)
_seeded = False

@app.get('/api/projects', response_model=List[Project])
def list_projects(featured: Optional[bool] = None):
    global _seeded
    try:
        # Seed sample projects once if empty
        if db is not None and not _seeded and db['project'].count_documents({}) == 0:
            samples: List[Project] = [
                Project(
                    title="Aurora UI System",
                    slug="aurora-ui-system",
                    summary="Design system and React component library with motion primitives.",
                    role="Frontend Engineer",
                    stack=["React", "TypeScript", "Tailwind", "Framer Motion"],
                    challenges="Accessibility, performance, theming",
                    github="https://github.com/example/aurora",
                    demo="https://example.com/aurora",
                    images=["/projects/aurora-1.webp", "/projects/aurora-2.webp"],
                    featured=True
                ),
                Project(
                    title="Nebula Analytics",
                    slug="nebula-analytics",
                    summary="Realtime dashboards with WebGL charts and streaming APIs.",
                    role="Full‑stack Developer",
                    stack=["Next.js", "WebGL", "Node", "Postgres"],
                    challenges="Realtime rendering, data pipelining",
                    github="https://github.com/example/nebula",
                    demo="https://example.com/nebula",
                    images=["/projects/nebula-1.webp"],
                    featured=True
                ),
                Project(
                    title="Pulse Commerce",
                    slug="pulse-commerce",
                    summary="Headless e‑commerce with edge personalization.",
                    role="Frontend Lead",
                    stack=["Next.js", "Edge", "Stripe", "Sanity"],
                    challenges="Edge caching, a/b testing, complex UI",
                    github="https://github.com/example/pulse",
                    demo="https://example.com/pulse",
                    images=["/projects/pulse-1.webp"],
                    featured=False
                )
            ]
            for p in samples:
                try:
                    create_document('project', p)
                except Exception:
                    pass
            _seeded = True

        query = {}
        if featured is not None:
            query['featured'] = featured
        docs = get_documents('project', query)
        # Convert ObjectId to str-safe
        for d in docs:
            d.pop('_id', None)
        return [Project(**d) for d in docs]
    except Exception as e:
        # If db not configured, return static sample data
        fallback: List[Project] = [
            Project(
                title="Aurora UI System",
                slug="aurora-ui-system",
                summary="Design system and React component library with motion primitives.",
                role="Frontend Engineer",
                stack=["React", "TypeScript", "Tailwind", "Framer Motion"],
                challenges="Accessibility, performance, theming",
                github="https://github.com/example/aurora",
                demo="https://example.com/aurora",
                images=["/projects/aurora-1.webp", "/projects/aurora-2.webp"],
                featured=True
            )
        ]
        return fallback

class ContactIn(ContactMessage):
    pass

@app.post('/api/contact')
def submit_contact(payload: ContactIn):
    try:
        if db is not None:
            create_document('contactmessage', payload)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
