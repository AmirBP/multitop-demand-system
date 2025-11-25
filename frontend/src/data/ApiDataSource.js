import { IDataSource } from "./DataSource";
import { api, getJson } from "../utils/api";

export class ApiDataSource extends IDataSource {
  async cargarCSV(file) {
    // Predicción por CSV (tu flujo actual)
    const form = new FormData();
    form.append("file", file);
    const { data } = await api.post("/api/predictions/run", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return {
      job_id: data.job_id,
      summary: data.summary || {},
      rawPredictions: data.predictions || [],
    };
  }

  async cargarMuestra() {
    // Si tienes endpoint de sample, úsalo; si no, que Mock se encargue
    const data = await getJson("/api/predictions/sample"); // opcional
    return {
      job_id: data.job_id || "sample",
      summary: data.summary || {},
      rawPredictions: data.predictions || [],
    };
  }

  async obtenerMetrics() {
    // Si hay endpoint, úsalo. Si no, leer localStorage (ya lo haces en index.html)
    try {
      const m = await getJson("/api/metrics/current");
      return m;
    } catch {
      const raw = localStorage.getItem("last_train_metrics");
      return raw ? JSON.parse(raw) : null;
    }
  }

  // Utilidades para DashboardGeneral
  getSummary() { return getJson("/api/predictions/summary"); }
  getHistory() { return getJson("/api/predictions/history"); }
  getDetail(jobId) { return getJson(`/api/predictions/${jobId}`); }
  async validar(jobId, fileB64) {
    const { data } = await api.post("/api/validation/compare-real", {
      job_id: jobId,
      ventas_real_csv_base64: fileB64,
      nivel: "SKU",
    });
    return data;
  }
}
