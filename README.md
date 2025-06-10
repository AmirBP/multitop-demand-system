# 🧠 MultiTop Demand Predictor

Sistema inteligente para la predicción de demanda por SKU, visualización de stock actual vs stock recomendado y generación de alertas accionables.

## 🛠 Tecnologías

- ⚛️ React + Vite + Tailwind CSS
- 📊 Recharts
- 🧮 FastAPI (backend)
- 🤖 XGBoost modelo `.joblib` entrenado
- 📦 Exportación a CSV
- ✅ Interfaz adaptada a perfiles de usuario (gerente, analista, almacén)

## 📸 Capturas

![Tabla Resumen](./screenshots/tabla-prediccion.png)

## 🚀 Cómo correr el proyecto

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
uvicorn main:app --reload
