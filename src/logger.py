"""
Módulo opcional para registrar logs de conversaciones en SQLite.
Almacena preguntas, respuestas, categorías y confianza para análisis.
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class ChatLogger:
    """Registra conversaciones en base de datos SQLite."""

    def __init__(self, db_path: str = "data/chat_logs.db"):
        """
        Inicializa el logger.

        Args:
            db_path: Ruta a la base de datos SQLite
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Crea la estructura de la base de datos si no existe."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabla principal de logs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    pregunta TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    categoria TEXT,
                    confianza REAL,
                    exito INTEGER,
                    tipo_fuente TEXT,
                    tiempo_respuesta_ms INTEGER
                )
            ''')

            # Tabla de sesiones
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fin DATETIME,
                    total_preguntas INTEGER DEFAULT 0,
                    total_exitosas INTEGER DEFAULT 0,
                    ip_origen TEXT
                )
            ''')

            # Tabla de errores
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT,
                    tipo_error TEXT,
                    mensaje TEXT,
                    traceback TEXT
                )
            ''')

            conn.commit()

    def create_session(self, session_id: str, ip_origen: Optional[str] = None) -> None:
        """
        Crea una nueva sesión de chat.

        Args:
            session_id: ID único de la sesión
            ip_origen: IP del cliente (opcional)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sessions (id, ip_origen)
                VALUES (?, ?)
            ''', (session_id, ip_origen))
            conn.commit()

    def log_interaction(
        self,
        session_id: str,
        pregunta: str,
        respuesta: str,
        categoria: Optional[str] = None,
        confianza: float = 0.0,
        exito: bool = True,
        tipo_fuente: str = "faq",
        tiempo_respuesta_ms: int = 0
    ) -> int:
        """
        Registra una interacción de chat.

        Args:
            session_id: ID de la sesión
            pregunta: Pregunta del usuario
            respuesta: Respuesta del bot
            categoria: Categoría de la FAQ
            confianza: Score de confianza (0-1)
            exito: Si la respuesta fue exitosa
            tipo_fuente: Fuente de la respuesta (faq, web_search, error, etc)
            tiempo_respuesta_ms: Tiempo de respuesta en ms

        Returns:
            ID del log creado
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO chat_logs
                (session_id, pregunta, respuesta, categoria, confianza, exito, tipo_fuente, tiempo_respuesta_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                pregunta,
                respuesta,
                categoria,
                confianza,
                1 if exito else 0,
                tipo_fuente,
                tiempo_respuesta_ms
            ))
            conn.commit()
            return cursor.lastrowid

    def log_error(
        self,
        session_id: str,
        tipo_error: str,
        mensaje: str,
        traceback: Optional[str] = None
    ) -> int:
        """
        Registra un error en el log.

        Args:
            session_id: ID de la sesión
            tipo_error: Tipo de error
            mensaje: Mensaje del error
            traceback: Traceback (opcional)

        Returns:
            ID del log de error
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO errors (session_id, tipo_error, mensaje, traceback)
                VALUES (?, ?, ?, ?)
            ''', (session_id, tipo_error, mensaje, traceback))
            conn.commit()
            return cursor.lastrowid

    def end_session(self, session_id: str) -> None:
        """
        Marca el final de una sesión.

        Args:
            session_id: ID de la sesión
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Obtener estadísticas de la sesión
            cursor.execute('''
                SELECT COUNT(*), SUM(exito)
                FROM chat_logs
                WHERE session_id = ?
            ''', (session_id,))

            result = cursor.fetchone()
            total_preguntas = result[0] if result[0] else 0
            total_exitosas = result[1] if result[1] else 0

            # Actualizar sesión
            cursor.execute('''
                UPDATE sessions
                SET fin = CURRENT_TIMESTAMP, total_preguntas = ?, total_exitosas = ?
                WHERE id = ?
            ''', (total_preguntas, total_exitosas, session_id))
            conn.commit()

    def get_session_stats(self, session_id: str) -> Dict:
        """
        Obtiene estadísticas de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con estadísticas
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Estadísticas generales
            cursor.execute('''
                SELECT COUNT(*), SUM(exito), AVG(confianza)
                FROM chat_logs
                WHERE session_id = ?
            ''', (session_id,))

            result = cursor.fetchone()
            total = result[0] if result[0] else 0
            exitosas = result[1] if result[1] else 0
            confianza_promedio = result[2] if result[2] else 0

            # Categorías más usadas
            cursor.execute('''
                SELECT categoria, COUNT(*)
                FROM chat_logs
                WHERE session_id = ? AND categoria IS NOT NULL
                GROUP BY categoria
                ORDER BY COUNT(*) DESC
            ''', (session_id,))

            categorias = {cat: count for cat, count in cursor.fetchall()}

            return {
                'total_preguntas': total,
                'preguntas_exitosas': exitosas,
                'tasa_exito': (exitosas / total * 100) if total > 0 else 0,
                'confianza_promedio': confianza_promedio,
                'categorias': categorias
            }

    def get_all_logs(self, limit: int = 100) -> List[Dict]:
        """
        Obtiene los últimos logs.

        Args:
            limit: Número máximo de logs a retornar

        Returns:
            Lista de dicts con logs
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM chat_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def get_logs_by_session(self, session_id: str) -> List[Dict]:
        """
        Obtiene logs de una sesión específica.

        Args:
            session_id: ID de la sesión

        Returns:
            Lista de logs de la sesión
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute('''
                SELECT * FROM chat_logs
                WHERE session_id = ?
                ORDER BY timestamp
            ''', (session_id,))

            return [dict(row) for row in cursor.fetchall()]

    def get_analytics(self) -> Dict:
        """
        Obtiene análisis general de los logs.

        Returns:
            Dict con análisis
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total de preguntas y tasa de éxito
            cursor.execute('SELECT COUNT(*), SUM(exito), AVG(confianza) FROM chat_logs')
            total, exitosas, conf = cursor.fetchone()

            # Categorías más consultadas
            cursor.execute('''
                SELECT categoria, COUNT(*) FROM chat_logs
                WHERE categoria IS NOT NULL
                GROUP BY categoria
                ORDER BY COUNT(*) DESC
            ''')
            categorias = {cat: count for cat, count in cursor.fetchall()}

            # Fuentes más usadas
            cursor.execute('''
                SELECT tipo_fuente, COUNT(*) FROM chat_logs
                GROUP BY tipo_fuente
                ORDER BY COUNT(*) DESC
            ''')
            fuentes = {source: count for source, count in cursor.fetchall()}

            return {
                'total_interacciones': total or 0,
                'exitosas': exitosas or 0,
                'tasa_exito': (exitosas / total * 100) if total else 0,
                'confianza_promedio': conf or 0,
                'categorias_consultadas': categorias,
                'fuentes_usadas': fuentes
            }


if __name__ == "__main__":
    # Ejemplo de uso
    logger = ChatLogger()

    print("Chat Logger Inicializado")
    print("=" * 50)

    # Crear sesión
    session_id = "demo_session_001"
    logger.create_session(session_id)
    print(f"\nSesión creada: {session_id}")

    # Registrar algunas interacciones
    preguntas = [
        ("¿Cómo recupero mi usuario?", "Puedes recuperar tu usuario en...", "General", 0.95),
        ("¿Cuándo se paga?", "El pago se realiza...", "Nómina y Pagos", 0.87),
        ("¿Salario mínimo?", "El salario mínimo en 2024 es...", "General", 0.75)
    ]

    for preg, resp, cat, conf in preguntas:
        logger.log_interaction(session_id, preg, resp, cat, conf)

    # Finalizar sesión
    logger.end_session(session_id)

    # Mostrar estadísticas
    stats = logger.get_session_stats(session_id)
    print(f"\nEstadísticas de la sesión:")
    print(f"  Total preguntas: {stats['total_preguntas']}")
    print(f"  Tasa de éxito: {stats['tasa_exito']:.1f}%")
    print(f"  Confianza promedio: {stats['confianza_promedio']:.2f}")

    # Mostrar analytics generales
    analytics = logger.get_analytics()
    print(f"\n\nAnalítics generales:")
    print(f"  Total interacciones: {analytics['total_interacciones']}")
    print(f"  Tasa de éxito: {analytics['tasa_exito']:.1f}%")
