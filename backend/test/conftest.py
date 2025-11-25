"""
Configuración global de pytest para el proyecto Multitop
Estructura: backend/test/
"""

import pytest
import sys
from pathlib import Path

# Ruta absoluta a backend/
TEST_DIR = Path(__file__).resolve().parent        # backend/test
BACKEND_DIR = TEST_DIR.parent                     # backend

# Asegurar que backend/ está en el PYTHONPATH
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ==== Directorios de outputs compartidos por todos los tests ====

@pytest.fixture(scope="session", autouse=True)
def setup_directories():
    """Crear directorios necesarios para las pruebas (una sola vez por sesión)"""
    directories = [
        BACKEND_DIR / "outputs",
        BACKEND_DIR / "outputs" / "store",
        BACKEND_DIR / "outputs" / "exports",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    yield


# ==== Fixtures reutilizables de DataFrames ====

@pytest.fixture
def sample_dataframe():
    """DataFrame pequeño válido para pruebas de predicción"""
    import pandas as pd
    import numpy as np

    return pd.DataFrame({
        "Fechaventa": pd.date_range("2024-01-01", periods=40),
        "CodArticulo": ["ME000008556"] * 40,
        "Temporada": ["Verano"] * 40,
        "PrecioVenta": [45.5] * 40,
        "CantidadVendida": np.random.randint(100, 150, 40),
        "StockMes": [5000] * 40,
        "TiempoReposicionDias": [60] * 40,
        "Promocion": [0] * 40,
        "DiaFestivo": [0] * 40,
        "EsDomingo": [0] * 40,
        "TiendaCerrada": [0] * 40,
    })


@pytest.fixture
def sample_training_dataframe():
    """DataFrame más grande para entrenamiento"""
    import pandas as pd
    import numpy as np

    return pd.DataFrame({
        "Fechaventa": pd.date_range("2024-01-01", periods=120),
        "CodArticulo": ["ME000008556"] * 120,
        "Temporada": ["Verano"] * 120,
        "PrecioVenta": np.random.uniform(40, 50, 120),
        "CantidadVendida": np.random.randint(90, 160, 120),
        "StockMes": [5000] * 120,
        "TiempoReposicionDias": [60] * 120,
        "Promocion": np.random.choice([0, 1], 120),
        "DiaFestivo": np.random.choice([0, 1], 120),
        "EsDomingo": [0] * 120,
        "TiendaCerrada": [0] * 120,
    })


# ==== Marcadores personalizados ====

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marca pruebas que toman tiempo (entrenamientos)",
    )
    config.addinivalue_line(
        "markers", "integration: pruebas de integración end-to-end",
    )
    config.addinivalue_line(
        "markers", "requires_model: pruebas que requieren modelo entrenado",
    )