"""
Módulo de conexión a SQL Server
Maneja conexiones a:
1. Base de datos de resultados (donde guardamos predicciones)
2. Base de datos de MultiTop (origen de datos - solo lectura)
"""
import pyodbc
import logging
from typing import Optional, Dict, List
from contextlib import contextmanager
from backend.app.utils.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Gestor de conexiones a SQL Server"""
    
    def __init__(self, connection_string: str, pool_size: int = 10):
        """
        Inicializa el gestor de conexiones.
        
        Args:
            connection_string: Cadena de conexión de SQL Server
            pool_size: Tamaño del pool de conexiones
        """
        self.connection_string = connection_string
        self.pool_size = pool_size
        self._test_connection()
    
    def _test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info(f"✅ Conexión a SQL Server exitosa: {result[0]}")
        except Exception as e:
            logger.error(f"❌ Error al conectar a SQL Server: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager para obtener una conexión.
        
        Uso:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM tabla")
        """
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string)
            conn.autocommit = False  # Transacciones manuales
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error en transacción: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Ejecuta una query SELECT y retorna resultados como lista de diccionarios.
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
        
        Returns:
            Lista de diccionarios con los resultados
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Obtener nombres de columnas
            columns = [column[0] for column in cursor.description]
            
            # Convertir filas a diccionarios
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
    
    def execute_scalar(self, query: str, params: Optional[tuple] = None):
        """
        Ejecuta una query que retorna un solo valor.
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
        
        Returns:
            Valor escalar del resultado
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            result = cursor.fetchone()
            return result[0] if result else None
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Ejecuta una query INSERT/UPDATE/DELETE.
        
        Args:
            query: Query SQL a ejecutar
            params: Parámetros para la query (opcional)
        
        Returns:
            Número de filas afectadas
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            return cursor.rowcount


# ============================================================================
# INSTANCIAS GLOBALES
# ============================================================================

# Base de datos de resultados (donde guardamos predicciones)
_results_db: Optional[DatabaseConnection] = None

# Base de datos de MultiTop (origen de datos - solo lectura)
_multitop_db: Optional[DatabaseConnection] = None


def get_results_db() -> DatabaseConnection:
    """
    Obtiene conexión a la base de datos de resultados.
    Esta es donde guardamos predicciones, configuraciones, etc.
    """
    global _results_db
    
    if _results_db is None:
        connection_string = settings.DATABASE_URL
        if not connection_string:
            raise ValueError("DATABASE_URL no configurada en .env")
        
        _results_db = DatabaseConnection(connection_string)
        logger.info("📊 Base de datos de resultados inicializada")
    
    return _results_db


def get_multitop_source_db() -> Optional[DatabaseConnection]:
    """
    Obtiene conexión a la base de datos de MultiTop (origen).
    Esta es opcional - solo si quieren cargar datos directamente de su BD.
    """
    global _multitop_db
    
    # Solo inicializar si está configurada
    if settings.MULTITOP_DATABASE_URL:
        if _multitop_db is None:
            _multitop_db = DatabaseConnection(settings.MULTITOP_DATABASE_URL)
            logger.info("🏢 Base de datos de MultiTop (origen) inicializada")
        return _multitop_db
    
    return None


def close_connections():
    """Cierra todas las conexiones (útil para cleanup)"""
    global _results_db, _multitop_db
    
    # No necesitamos cerrar nada con pyodbc ya que usa context managers
    # Pero reseteamos las referencias
    _results_db = None
    _multitop_db = None
    
    logger.info("🔌 Conexiones cerradas")


# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def test_connections():
    """
    Prueba todas las conexiones configuradas.
    Útil para verificar configuración.
    """
    print("\n" + "="*60)
    print("🔍 PROBANDO CONEXIONES A BASE DE DATOS")
    print("="*60 + "\n")
    
    # Probar BD de resultados
    try:
        db = get_results_db()
        result = db.execute_scalar("SELECT @@VERSION")
        print("✅ Base de datos de RESULTADOS:")
        print(f"   {result[:100]}...")
        
        # Ver tablas
        tables = db.execute_query("""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_NAME
        """)
        print(f"   📋 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"      - {table['TABLE_NAME']}")
    except Exception as e:
        print(f"❌ Error en BD de resultados: {e}")
    
    print()
    
    # Probar BD de MultiTop (si está configurada)
    try:
        db = get_multitop_source_db()
        if db:
            result = db.execute_scalar("SELECT @@VERSION")
            print("✅ Base de datos de MULTITOP (origen):")
            print(f"   {result[:100]}...")
            
            # Ver tablas
            tables = db.execute_query("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """)
            print(f"   📋 Tablas encontradas: {len(tables)}")
            for table in tables[:10]:  # Mostrar solo primeras 10
                print(f"      - {table['TABLE_NAME']}")
            if len(tables) > 10:
                print(f"      ... y {len(tables) - 10} más")
        else:
            print("⚠️  Base de datos de MultiTop NO configurada")
            print("   (Opcional - solo para carga directa desde BD)")
    except Exception as e:
        print(f"❌ Error en BD de MultiTop: {e}")
    
    print("\n" + "="*60)
    print("✅ Prueba de conexiones completada")
    print("="*60 + "\n")


def get_table_row_counts() -> Dict[str, int]:
    """
    Obtiene el conteo de filas de todas las tablas principales.
    Útil para monitoreo.
    """
    db = get_results_db()
    
    tables = ['uploaded_files', 'prediction_jobs', 'prediction_rows', 'configurations']
    counts = {}
    
    for table in tables:
        try:
            count = db.execute_scalar(f"SELECT COUNT(*) FROM {table}")
            counts[table] = count
        except:
            counts[table] = 0
    
    return counts


if __name__ == "__main__":
    """
    Ejecutar este archivo directamente para probar conexiones:
    python app/database.py
    """
    import sys
    sys.path.insert(0, ".")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    test_connections()
    
    print("\n📊 Conteo de registros:")
    counts = get_table_row_counts()
    for table, count in counts.items():
        print(f"   {table}: {count:,} registros")