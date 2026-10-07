# 🌍 Geospatial File Measurement API

A production-grade backend service built with **FastAPI** + **PostgreSQL/PostGIS** that accepts geospatial files (Shapefile, KML), processes their features, and returns measurement information (area for polygons, length for line strings).

---

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Setup](#-setup)
  - [Docker (Recommended)](#option-1-docker-recommended)
  - [Local Development](#option-2-local-development)
- [API Documentation](#-api-documentation)
- [Architecture](#-architecture)
- [Design Decisions](#-design-decisions)
- [Learnings](#-learnings)
- [Future Scope](#-future-scope)

---

## ✨ Features

- **File Upload** — Accepts `.zip` (Shapefile) and `.kml` files via REST API
- **Feature Extraction** — Parses all geospatial features with geometry, CRS, and properties
- **Accurate Measurements** — Calculates area (m²) for polygons and length (m) for line strings
- **Smart CRS Handling** — Auto-detects UTM zone and reprojects from geographic to projected CRS
- **Graceful Degradation** — Unsupported geometry types (e.g., Point) are handled without errors
- **Background Processing** — File processing runs asynchronously; API returns immediately
- **Interactive Docs** — Auto-generated Swagger UI at `/docs` and ReDoc at `/redoc`

---

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Geo Processing | GeoPandas, Fiona, Shapely, pyproj |
| Validation | Pydantic v2 |
| Testing | pytest, httpx |
| Containerization | Docker + docker-compose |

---

## 🚀 Setup

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (for Docker setup)
- Python 3.11+ (for local setup)
- PostgreSQL with PostGIS extension (for local setup)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/<your-username>/geospatial-measurement-api.git
cd geospatial-measurement-api

# Start all services
docker-compose up --build

# API is available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# 1. Clone and enter the project
git clone https://github.com/<your-username>/geospatial-measurement-api.git
cd geospatial-measurement-api

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 5. Ensure PostgreSQL is running with PostGIS
# Create the database:
# psql -U postgres -c "CREATE DATABASE geospatial_db;"
# psql -U postgres -d geospatial_db -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# 6. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 7. Run tests
pytest tests/ -v
```

---

## 📡 API Documentation

### Base URL: `http://localhost:8000`

Interactive documentation is auto-generated and available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 1. Upload File

```
POST /api/files/
Content-Type: multipart/form-data
```

**Request:**
```bash
curl -X POST http://localhost:8000/api/files/ \
  -F "file=@survey.kml"
```

**Response (201 Created):**
```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "survey.kml",
    "status": "PENDING",
    "uploaded_at": "2026-10-07T14:30:00.000000Z"
}
```

---

### 2. Get File Information

```
GET /api/files/{id}/
```

**Request:**
```bash
curl http://localhost:8000/api/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**Response (200 OK):**
```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "survey.kml",
    "file_type": "kml",
    "feature_count": 120,
    "crs": "EPSG:4326",
    "status": "COMPLETED",
    "uploaded_at": "2026-10-07T14:30:00.000000Z",
    "processed_at": "2026-10-07T14:30:05.000000Z",
    "error_message": null
}
```

---

### 3. Get Measurements

```
GET /api/files/{id}/measurements/
```

**Request:**
```bash
curl http://localhost:8000/api/files/a1b2c3d4-e5f6-7890-abcd-ef1234567890/measurements/
```

**Response (200 OK):**
```json
{
    "file_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "filename": "survey.kml",
    "total_features": 3,
    "measurements": [
        {
            "feature_index": 0,
            "geometry_type": "Polygon",
            "properties": {"name": "Zone A"},
            "area_sq_meters": 15234.5678,
            "length_meters": null,
            "measurement_supported": true,
            "measurement_note": null
        },
        {
            "feature_index": 1,
            "geometry_type": "LineString",
            "properties": {"name": "Road B"},
            "area_sq_meters": null,
            "length_meters": 1523.4567,
            "measurement_supported": true,
            "measurement_note": null
        },
        {
            "feature_index": 2,
            "geometry_type": "Point",
            "properties": {"name": "Station 1"},
            "area_sq_meters": null,
            "length_meters": null,
            "measurement_supported": false,
            "measurement_note": "No measurement required for Point geometry"
        }
    ]
}
```

---

### 4. List All Files

```
GET /api/files/?skip=0&limit=50
```

---

### Error Responses

| Status | Scenario |
|--------|----------|
| `404` | File ID not found |
| `409` | File still being processed |
| `422` | Unsupported file format / Processing failed |

---

## 🏗 Architecture

### Application Structure

```
app/
├── main.py              # FastAPI app, lifespan, middleware
├── config.py            # Pydantic Settings (env-based config)
├── database.py          # SQLAlchemy engine, session, Base
├── models/              # ORM models (GeoFile, Feature)
├── schemas/             # Pydantic request/response schemas
├── api/
│   ├── router.py        # Central router aggregation
│   └── endpoints/
│       └── files.py     # /api/files/ CRUD endpoints
├── services/
│   ├── file_service.py  # Upload validation & storage
│   ├── geo_processor.py # File parsing & feature extraction
│   ├── crs_handler.py   # CRS detection & transformation
│   └── measurement.py   # Area/length calculation
└── utils/
    ├── exceptions.py    # Custom HTTP exceptions
    └── file_utils.py    # File-system helpers
```

### File-Processing Flow

```
Upload Request
    │
    ▼
┌─────────────────┐
│  Validate File   │ ← Check extension (.zip / .kml)
│  Save to Disk    │ ← Generate unique filename
│  Create DB Record│ ← Status: PENDING
└────────┬────────┘
         │
    ▼ (Background Task)
┌─────────────────┐
│  Parse File      │ ← Fiona/GeoPandas reads SHP or KML
│  Detect CRS      │ ← Extract CRS from file metadata
│  For each feature│
│    ├─ Get geometry│
│    ├─ Transform   │ ← Reproject to UTM (metres)
│    ├─ Measure     │ ← Area or Length calculation
│    └─ Store       │ ← Save Feature + measurement to DB
│  Update Status   │ ← Status: COMPLETED / FAILED
└─────────────────┘
```

### Measurement Calculation Flow

1. **Input**: Raw geometry in source CRS (e.g., EPSG:4326 — lat/lon degrees)
2. **Detect CRS**: Read CRS from file metadata; default to EPSG:4326 if missing
3. **Select Projection**: Auto-detect UTM zone from geometry centroid
4. **Transform**: Reproject geometry to UTM using `pyproj.Transformer`
5. **Calculate**: Use `shapely.area` or `shapely.length` on projected geometry
6. **Result**: Area in m² or length in m (depending on geometry type)

### CRS Handling

The API follows this strategy for coordinate reference system handling:

1. **Detection**: Source CRS is read from the file's metadata via GeoPandas/Fiona
2. **Fallback**: If no CRS is found, EPSG:4326 (WGS84) is assumed with a warning logged
3. **Projection Selection**: UTM zone is auto-selected based on the geometry's centroid:
   - Longitude → UTM zone number: `floor((lon + 180) / 6) + 1`
   - Northern hemisphere → `EPSG:326xx`
   - Southern hemisphere → `EPSG:327xx`
4. **Transformation**: Geometries are reprojected using `pyproj.Transformer` with `always_xy=True`
5. **Skip if Projected**: If the source CRS is already metre-based (projected), no transformation is performed

---

## 💡 Design Decisions

### 1. FastAPI over Django
**Choice**: FastAPI  
**Rationale**: Native async support, automatic OpenAPI documentation, Pydantic integration for validation, and lighter footprint. For a focused API service without admin UI needs, FastAPI is the better fit.

### 2. Background Processing via BackgroundTasks
**Choice**: FastAPI `BackgroundTasks` (not Celery)  
**Rationale**: For this service's scale, the built-in background task mechanism is sufficient and avoids the operational complexity of a Redis + Celery stack. The upload endpoint returns immediately while processing happens in a thread pool.  
**Alternative considered**: Celery — better for distributed processing but adds infrastructure overhead.

### 3. Auto UTM Zone Detection
**Choice**: Compute UTM zone from geometry centroid  
**Rationale**: UTM provides metre-based coordinates suitable for accurate area/length calculations. Auto-detection makes the API zero-configuration — clients don't need to specify a target CRS.  
**Alternative considered**: A fixed projection (e.g., Web Mercator EPSG:3857) — rejected because it introduces significant distortion for area calculations at non-equatorial latitudes.

### 4. Geometry stored as WKT (not PostGIS native)
**Choice**: Store geometry as WKT text in the `features` table  
**Rationale**: All geospatial operations (parsing, transforming, measuring) happen in Python using Shapely/pyproj. We don't need spatial indexing or database-level spatial queries. WKT storage simplifies the setup while keeping full geometry data available for future use.  
**Alternative considered**: GeoAlchemy2 with PostGIS geometry columns — better if spatial queries are needed in the future.

### 5. Sync SQLAlchemy with sync session
**Choice**: Synchronous SQLAlchemy engine  
**Rationale**: The geo-processing pipeline is CPU-bound (Shapely/pyproj operations), not I/O-bound. Using async SQLAlchemy would add complexity without performance benefit since the heavy work runs in background threads anyway.

---

## 📚 Learnings

- **CRS matters**: Directly computing area from lat/lon degrees gives incorrect results. A polygon near the equator vs. near the poles would have vastly different distortions. UTM projection solves this by providing a local metre-based coordinate system.
- **Fiona driver registration**: KML support requires explicitly enabling the driver (`fiona.drvsupport.supported_drivers['KML'] = 'r'`) as it's not enabled by default in all builds.
- **Shapefile is multi-file**: A single "shapefile" is actually 3-7 files (.shp, .shx, .dbf, .prj, etc.). Accepting a ZIP archive and extracting the `.shp` is the standard approach.
- **GeoPandas + Fiona**: GeoPandas provides a high-level interface for reading geospatial files, while Fiona handles the low-level driver management. Together they support most common formats.
- **Background processing design**: Separating the upload response from processing allows the API to remain responsive even for large files. Status polling via `GET /api/files/{id}/` gives clients visibility into processing progress.

---

## 🔮 Future Scope

- **GeoJSON Support** — Accept `.geojson` files as an additional input format
- **Spatial Queries** — Use PostGIS native geometry columns for spatial indexing and queries (e.g., "find all features within a bounding box")
- **Celery Integration** — For production scale, replace BackgroundTasks with Celery + Redis for distributed, fault-tolerant processing
- **File Management** — Add DELETE endpoint and automatic cleanup of old files
- **Streaming Upload** — Support chunked uploads for very large files
- **WebSocket Status** — Real-time processing status updates via WebSocket instead of polling
- **Unit Conversion** — Return measurements in multiple units (m², km², acres, miles, etc.)
- **Geometry Visualization** — Return GeoJSON for frontend map rendering
- **Authentication** — Add JWT-based auth for multi-tenant usage
- **Rate Limiting** — Protect the upload endpoint from abuse
- **CI/CD Pipeline** — GitHub Actions for automated testing, linting, and deployment

---

## 📄 License

MIT