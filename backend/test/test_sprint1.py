import io, csv, re, json
import pytest

# ==== Helpers ================================================================

def _csv_bytes(rows, fieldnames):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    return io.BytesIO(buf.getvalue().encode("utf-8"))

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}")

def _pick_uuid(d: dict) -> str | None:
    # prueba keys comunes; si no, escanea todo el JSON buscando un UUID
    for k in ("job_id","export_id","id","task_id","prediction_id"):
        v = d.get(k)
        if isinstance(v, str) and UUID_RE.fullmatch(v):
            return v
    txt = json.dumps(d)
    m = UUID_RE.search(txt)
    return m.group(0) if m else None

def _find_route(client, keywords, methods=("POST","GET")):
    cands = []
    for r in client.app.routes:
        path = getattr(r, "path", "")
        mets = set(getattr(r, "methods", []) or [])
        if not mets.intersection(methods): 
            continue
        text = path.lower()
        if all(k in text for k in keywords):
            cands.append(path)
    return sorted(cands, key=len)[0] if cands else None

@pytest.fixture(scope="module")
def endpoints(client):
    upload  = _find_route(client, ["api","files","upload"], methods=("POST",))
    predict = _find_route(client, ["api","predictions","run"], methods=("POST",))
    export  = _find_route(client, ["api","predictions","export"], methods=("GET",))
    assert upload and predict and export, "Ajusta keywords si cambian rutas"
    return {"upload": upload, "predict": predict, "export": export}

# ==== Debug (deja este test para imprimir rutas en consola) ==================
def test__debug_routes_snapshot(client):
    routes = [(r.path, sorted(getattr(r, "methods", []))) for r in client.app.routes]
    print("\nROUTES:", routes)
    assert routes

# ==== HU001 ==================================================================
def test_s1_hu001_upload_real_data_ok(client, endpoints):
    fieldnames = ["SKU","tienda","fecha","unidades_vendidas","Fechaventa"]
    rows = [
        {"SKU":"M0001","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":12},
        {"SKU":"M0002","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":5},
    ]
    files = {"file": ("ventas.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["upload"], files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "file_id" in data or "rows" in data

# ==== HU002 ==================================================================
def test_s1_hu002_invalid_schema_detected(client, endpoints):
    # probamos validación EN PREDICT (upload no valida)
    fieldnames = ["tienda","fecha","unidades_vendidas"]  # falta SKU y Fechaventa
    rows = [{"tienda":"101","fecha":"2025-05-01","unidades_vendidas":1}]
    files = {"file": ("sin_sku.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["predict"], files=files)
    # esperamos 4xx; si tu API devuelve 200 con error controlado, aceptamos body con "error"
    assert r.status_code // 100 in (4,), r.text

# ==== HU003 ==================================================================
def test_s1_hu003_predict_ok_returns_predictions(client, endpoints):
    fieldnames = ["SKU","tienda","fecha","unidades_vendidas","Fechaventa"]
    rows = [
        {"SKU":"M0001","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":12},
        {"SKU":"M0001","tienda":"101","fecha":"2025-05-08","Fechaventa":"08/05/2025","unidades_vendidas":9},
        {"SKU":"M0002","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":5},
    ]
    files = {"file": ("ventas.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["predict"], files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "predictions" in data and isinstance(data["predictions"], list) and data["predictions"], data
    keys = {k.lower() for k in data["predictions"][0].keys()}
    assert {"sku","tienda"}.issubset(keys)
    assert any(k in keys for k in ("y_hat","yhat","prediccion","forecast"))

# ==== HU004 ==================================================================
def test_s1_hu004_table_render_backend_contract(client, endpoints):
    fieldnames = ["SKU","tienda","fecha","unidades_vendidas","Fechaventa"]
    rows = [{"SKU":"M0003","tienda":"102","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":7}]
    files = {"file": ("ventas.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["predict"], files=files)
    assert r.status_code == 200
    keys = {k.lower() for k in r.json()["predictions"][0].keys()}
    assert {"sku","tienda","fecha"}.issubset(keys)

# ==== HU005 ==================================================================
def test_s1_hu005_visual_status_fields_exist(client, endpoints):
    fieldnames = ["SKU","tienda","fecha","unidades_vendidas","Fechaventa"]
    rows = [{"SKU":"M0004","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":3}]
    files = {"file": ("ventas.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["predict"], files=files)
    assert r.status_code == 200
    keys = {k.lower() for k in r.json()["predictions"][0].keys()}
    assert any(k in keys for k in ("estado","status","risk"))

# ==== HU006 ==================================================================
def test_s1_hu006_export_csv_download(client, endpoints):
    # 1) correr predict para obtener un id de export
    fieldnames = ["SKU","tienda","fecha","unidades_vendidas","Fechaventa"]
    rows = [{"SKU":"M0005","tienda":"101","fecha":"2025-05-01","Fechaventa":"01/05/2025","unidades_vendidas":2}]
    files = {"file": ("ventas.csv", _csv_bytes(rows, fieldnames), "text/csv")}
    r = client.post(endpoints["predict"], files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    export_id = _pick_uuid(data)
    assert export_id, f"No se halló UUID en respuesta de predict: {data}"

    # 2) exportar usando el UUID en la ruta
    export_url = f"{endpoints['export'].rstrip('/')}/{export_id}"
    r2 = client.get(export_url)
    assert r2.status_code == 200, r2.text
    assert "csv" in r2.headers.get("content-type","").lower()
    header = r2.text.splitlines()[0].lower()
    assert "sku" in header and "tienda" in header
