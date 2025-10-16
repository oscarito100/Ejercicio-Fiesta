#!/usr/bin/env python3
# app.py
# CRUD de invitados con Streamlit + SQLite
# Ejecuta con: streamlit run app.py

import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

DB_PATH = Path("invitados.db")

# -------------------- Utilidades de BD --------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # Garantiza que la tabla y el trigger existan (por si no se corrió setup_db.py)
    conn = get_conn()
    schema_sql = """
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
    with conn:
        conn.executescript(schema_sql)
    conn.close()

def insertar_invitado(nombre, apellidos, telefono, correo, asistira, acompanantes):
    conn = get_conn()
    with conn:
        conn.execute("""
            INSERT INTO invitados (nombre, apellidos, telefono, correo, asistira, acompanantes)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (nombre.strip(), apellidos.strip(), telefono.strip() if telefono else None,
              correo.strip() if correo else None, int(asistira), int(acompanantes)))
    conn.close()

def actualizar_invitado(id_, nombre, apellidos, telefono, correo, asistira, acompanantes):
    conn = get_conn()
    with conn:
        conn.execute("""
            UPDATE invitados
               SET nombre = ?, apellidos = ?, telefono = ?, correo = ?, asistira = ?, acompanantes = ?
             WHERE id = ?;
        """, (nombre.strip(), apellidos.strip(), telefono.strip() if telefono else None,
              correo.strip() if correo else None, int(asistira), int(acompanantes), int(id_)))
    conn.close()

def eliminar_invitado(id_):
    conn = get_conn()
    with conn:
        conn.execute("DELETE FROM invitados WHERE id = ?;", (int(id_),))
    conn.close()

def listar_invitados(filtro_texto="", solo_confirmados=False):
    conn = get_conn()
    filtro = f"%{filtro_texto.strip()}%" if filtro_texto else "%"
    where = "WHERE (nombre LIKE ? OR apellidos LIKE ? OR telefono LIKE ? OR correo LIKE ?)"
    params = [filtro, filtro, filtro, filtro]
    if solo_confirmados:
        where += " AND asistira = 1"
    query = f"""
        SELECT id, nombre, apellidos, telefono, correo, asistira, acompanantes, created_at, updated_at
          FROM invitados
          {where}
         ORDER BY apellidos, nombre, id DESC;
    """
    df = pd.read_sql_query(query, get_conn(), params=params)
    return df

def contar_totales():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN asistira=1 THEN 1 ELSE 0 END), COALESCE(SUM(CASE WHEN asistira=1 THEN acompanantes ELSE 0 END),0) FROM invitados;")
    total, confirmados, acompanantes = cur.fetchone()
    conn.close()
    return total or 0, confirmados or 0, acompanantes or 0

# -------------------- UI Streamlit --------------------
st.set_page_config(page_title="Invitados • Aniversario", page_icon="🎉", layout="wide")
init_db()

st.title("🎉 Gestión de invitados - Aniversario")
st.caption("CRUD con Streamlit + SQLite")

with st.sidebar:
    st.header("➕ Alta rápida")
    with st.form("form_alta"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre*", placeholder="Ej. Ana")
            telefono = st.text_input("Teléfono", placeholder="+52 55 ...")
            asistira = st.selectbox("¿Asistirá?", ["No sabe/No", "Sí"], index=0)
        with col2:
            apellidos = st.text_input("Apellidos*", placeholder="Ej. Pérez García")
            correo = st.text_input("Correo", placeholder="ana@correo.com")
            acompanantes = st.number_input("Acompañantes", min_value=0, max_value=20, value=0, step=1)
        submitted = st.form_submit_button("Guardar invitado")
    if submitted:
        if not nombre.strip() or not apellidos.strip():
            st.error("Los campos *Nombre* y *Apellidos* son obligatorios.")
        else:
            insertar_invitado(nombre, apellidos, telefono, correo, asistira == "Sí", acompanantes)
            st.success(f"Invitado agregado: {nombre} {apellidos}")

st.divider()

# KPIs arriba
total, confirmados, acomp_confirmados = contar_totales()
k1, k2, k3 = st.columns(3)
k1.metric("Total registrados", total)
k2.metric("Confirmados (Sí)", confirmados)
k3.metric("Acompañantes confirmados", acomp_confirmados)

st.divider()

# Filtros de lista
c1, c2, c3 = st.columns([3,1,1])
with c1:
    filtro = st.text_input("Buscar (nombre, apellidos, teléfono o correo)", placeholder="Escribe para filtrar...")
with c2:
    solo_confirmados = st.checkbox("Solo confirmados")
with c3:
    if st.button("Descargar CSV"):
        df_all = listar_invitados(filtro_texto=filtro, solo_confirmados=solo_confirmados)
        csv = df_all.to_csv(index=False).encode("utf-8")
        st.download_button("Descargar resultados como CSV", csv, "invitados.csv", "text/csv")

# Tabla principal
df = listar_invitados(filtro_texto=filtro, solo_confirmados=solo_confirmados)

# Mostrar/editar registros
st.subheader("Listado de invitados")
if df.empty:
    st.info("No hay invitados aún. Agrega el primero desde la barra lateral.")
else:
    # Vista rápida
    st.dataframe(
        df.assign(asistira=df["asistira"].map({0: "No sabe/No", 1: "Sí"})),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### ✏️ Editar / 🗑️ Eliminar")
    for _, row in df.iterrows():
        with st.expander(f"{row['apellidos']}, {row['nombre']}  |  Asiste: {'Sí' if row['asistira']==1 else 'No/No sabe'}  |  Acompañantes: {row['acompanantes']}"):
            col_a, col_b, col_c, col_d = st.columns([1,1,1,1])
            with col_a:
                nombre_e = st.text_input("Nombre*", value=row["nombre"], key=f"nombre_{row['id']}")
                telefono_e = st.text_input("Teléfono", value=row["telefono"] or "", key=f"tel_{row['id']}")
            with col_b:
                apellidos_e = st.text_input("Apellidos*", value=row["apellidos"], key=f"ap_{row['id']}")
                correo_e = st.text_input("Correo", value=row["correo"] or "", key=f"mail_{row['id']}")
            with col_c:
                asistira_e = st.selectbox("¿Asistirá?", ["No sabe/No", "Sí"], index=1 if row["asistira"]==1 else 0, key=f"asis_{row['id']}")
            with col_d:
                acompanantes_e = st.number_input("Acompañantes", min_value=0, max_value=20, value=int(row["acompanantes"] or 0), step=1, key=f"acomp_{row['id']}")

            col_btn1, col_btn2 = st.columns([1,1])
            with col_btn1:
                if st.button("💾 Guardar cambios", key=f"save_{row['id']}"):
                    if not nombre_e.strip() or not apellidos_e.strip():
                        st.error("Nombre y Apellidos son obligatorios.")
                    else:
                        actualizar_invitado(
                            row["id"],
                            nombre_e,
                            apellidos_e,
                            telefono_e,
                            correo_e,
                            asistira_e == "Sí",
                            acompanantes_e
                        )
                        st.success("Cambios guardados. Actualiza la página para ver reflejados los cambios.")
            with col_btn2:
                if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                    eliminar_invitado(row["id"])
                    st.warning("Invitado eliminado. Actualiza la página para refrescar la lista.")
