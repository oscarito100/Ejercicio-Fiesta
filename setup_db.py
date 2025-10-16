#!/usr/bin/env python3
"""
setup_db.py
Crea la base de datos SQLite para la fiesta de aniversario.

Tabla: invitados
Campos:
- id (PRIMARY KEY AUTOINCREMENT)
- nombre TEXT NOT NULL
- apellidos TEXT NOT NULL
- telefono TEXT
- correo TEXT
- asistira INTEGER NOT NULL DEFAULT 0   # 0 = No sabe / No, 1 = Sí
- acompanantes INTEGER NOT NULL DEFAULT 0
- created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

Uso:
    python setup_db.py
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("invitados.db")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS invitados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    telefono TEXT,
    correo TEXT,
    asistira INTEGER NOT NULL DEFAULT 0,
    acompanantes INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_invitados_nombre ON invitados(nombre);
CREATE INDEX IF NOT EXISTS idx_invitados_apellidos ON invitados(apellidos);
CREATE INDEX IF NOT EXISTS idx_invitados_telefono ON invitados(telefono);
CREATE INDEX IF NOT EXISTS idx_invitados_correo ON invitados(correo);

DROP TRIGGER IF EXISTS trg_invitados_updated_at;

CREATE TRIGGER IF NOT EXISTS trg_invitados_updated_at
AFTER UPDATE ON invitados
FOR EACH ROW
WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE invitados
       SET updated_at = CURRENT_TIMESTAMP
     WHERE id = OLD.id;
END;
"""

def main():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA_SQL)
        print(f"Base de datos creada/actualizada en: {DB_PATH.resolve()}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
