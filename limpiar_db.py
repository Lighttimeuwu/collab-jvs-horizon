import os
import sqlite3

def purga_total_sistema():
    # Detectar la ruta de la base de datos en la carpeta actual
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "boleteria.db")
    
    if not os.path.exists(db_path):
        print(f"❌ No se encontró el archivo 'boleteria.db' en: {db_path}")
        return

    print(f"🔗 Conectando a la base de datos: {db_path}")
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()

    try:
        # 1. DESACTIVAR restricciones de integridad temporalmente para limpiar libremente
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # 2. Lista exhaustiva de tablas a vaciar de raíz (Eventos, Boletas, Compras, Asientos, Técnicos)
        tablas_a_vaciar = [
            # --- Relacionadas con Ventas y Clientes ---
            "Venta",                    # Historial de transacciones/compras web
            "Boleta",                   # Físicamente las boletas generadas/compradas
            "Asientos_Ocupados",        # Registro de qué sillas ya apartaron los usuarios
            
            # --- Relacionadas con el Evento y Cartelera ---
            "Evento",                   # Datos principales del evento (Borradores y Publicados)
            "Funcion",                  # Fechas y horas asignadas a los eventos
            "Funcion_Localidad",        # Precios, aforos y localidades por cada función
            "Evento_Boleta",            # Tabla pivot que amarra boletas con el evento
            
            # --- Relacionadas con Artistas y Riders ---
            "Evento_Artista",           # Vínculos de qué artistas cantan en qué evento
            "Rider_Tecnico",            # Documentos y especificaciones técnicas de artistas
            
            # --- Relacionadas con Logística y Proveedores ---
            "Personal_Tecnico_Evento",  # El personal técnico asignado a los eventos
            "Evento_Proveedor"          # Catálogo o asignaciones de proveedores al show
        ]

        print("\n🧹 Iniciando la purga absoluta del sistema (Cero rastros)...")
        for tabla in tablas_a_vaciar:
            try:
                cursor.execute(f"DELETE FROM {tabla};")
                print(f"  ✓ Tabla '{tabla}' vaciada por completo.")
            except sqlite3.OperationalError as e:
                # Por si alguna tabla accesoria tiene un nombre ligeramente distinto
                print(f"  ⚠️ Omitido/No crítica: '{tabla}' ({e})")

        # 3. REINICIAR CONTADORES AUTOINCREMENTALES de SQLite
        print("\n🔢 Reiniciando contadores de ID (AUTOINCREMENT) de vuelta a 1...")
        for tabla in tablas_a_vaciar:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?;", (tabla,))
        print("  ✓ Todos los contadores de identificación reiniciados.")

        # Guardar de forma definitiva
        conexion.commit()
        print("\n🎉 ¡ÉXITO ABSOLUTO! Todo rastro de eventos, compras, boletas y logística ha sido erradicado.")
        print("Tu sistema está listo para pruebas impecables desde cero.")

    except Exception as error:
        conexion.rollback()
        print(f"\n❌ Error crítico durante la limpieza profunda: {error}")
        
    finally:
        # 4. VOLVER A ACTIVAR las llaves foráneas por seguridad del flujo diario
        cursor.execute("PRAGMA foreign_keys = ON;")
        conexion.close()

if __name__ == "__main__":
    print("⚠️ ADVERTENCIA: Esto borrará TODO historial de compras, boletas, eventos y riders.")
    confirmacion = input("¿Estás completamente seguro de continuar con la purga total? (s/n): ")
    if confirmacion.lower() == 's':
        purga_total_sistema()
    else:
        print("❌ Operación cancelada de forma segura.")