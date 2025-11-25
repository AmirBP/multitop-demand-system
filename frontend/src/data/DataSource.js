// Fuente de datos con toggle DEMO
export const DEMO_MODE =
  (import.meta.env?.VITE_DEMO_MODE === "true") ||
  (localStorage.getItem("DEMO_MODE") === "true");

export class IDataSource {
  cargarCSV(file) { throw new Error("not impl"); }
  cargarMuestra() { throw new Error("not impl"); }
  obtenerMetrics() { throw new Error("not impl"); }
}
