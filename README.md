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

![Imagen de WhatsApp 2025-06-09 a las 18 58 45_086ec59c](https://github.com/user-attachments/assets/2a0ead7a-1d0b-43d6-a7da-2c14d0bf4cd8)

![Imagen de WhatsApp 2025-06-09 a las 18 58 54_36a077d7](https://github.com/user-attachments/assets/a8c237bb-7f26-498b-9cef-c790b00703be)

![Imagen de WhatsApp 2025-06-09 a las 18 59 04_b9275b87](https://github.com/user-attachments/assets/788a064b-c31d-4de6-a644-b4362b7d02a9)

## 🚀 Cómo correr el proyecto

```bash
# Proyecto
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
uvicorn main:app --reload
