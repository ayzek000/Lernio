import os
import sqlite3

def fix_materials_storage():
    print("\n[1/3] u041fu0440u043eu0432u0435u0440u043au0430 u0441u0442u0440u0443u043au0442u0443u0440u044b u0442u0430u0431u043bu0438u0446u044b materials...")
    
    # u041fu0443u0442u044c u043a u0431u0430u0437u0435 u0434u0430u043du043du044bu0445
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    site_db_path = os.path.join(instance_dir, 'site.db')
    
    if not os.path.exists(site_db_path):
        print(f"u041eu0448u0438u0431u043au0430: u0431u0430u0437u0430 u0434u0430u043du043du044bu0445 {site_db_path} u043du0435 u043du0430u0439u0434u0435u043du0430!")
        return
    
    try:
        # u041fu043eu0434u043au043bu044eu0447u0430u0435u043cu0441u044f u043a u0431u0430u0437u0435 u0434u0430u043du043du044bu0445
        conn = sqlite3.connect(site_db_path)
        cursor = conn.cursor()
        
        # u041fu043eu043bu0443u0447u0430u0435u043c u0438u043du0444u043eu0440u043cu0430u0446u0438u044e u043e u0441u0442u0440u0443u043au0442u0443u0440u0435 u0442u0430u0431u043bu0438u0446u044b materials
        cursor.execute("PRAGMA table_info(materials);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("u0422u0435u043au0443u0449u0438u0435 u043au043eu043bu043eu043du043au0438 u0432 u0442u0430u0431u043bu0438u0446u0435 materials:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u043au043eu043bu043eu043du043au0438 storage_type
        if 'storage_type' not in column_names:
            print("\n[2/3] u0414u043eu0431u0430u0432u043bu0435u043du0438u0435 u043au043eu043bu043eu043du043au0438 storage_type u0432 u0442u0430u0431u043bu0438u0446u0443 materials...")
            try:
                cursor.execute("ALTER TABLE materials ADD COLUMN storage_type VARCHAR(20) DEFAULT 'local';")
                conn.commit()
                print("u041au043eu043bu043eu043du043au0430 storage_type u0443u0441u043fu0435u0448u043du043e u0434u043eu0431u0430u0432u043bu0435u043du0430.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("u041au043eu043bu043eu043du043au0430 storage_type u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442.")
                else:
                    raise
        else:
            print("\n[2/3] u041au043eu043bu043eu043du043au0430 storage_type u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u0432 u0442u0430u0431u043bu0438u0446u0435 materials.")
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u043au043eu043bu043eu043du043au0438 storage_path
        if 'storage_path' not in column_names:
            print("\n[3/3] u0414u043eu0431u0430u0432u043bu0435u043du0438u0435 u043au043eu043bu043eu043du043au0438 storage_path u0432 u0442u0430u0431u043bu0438u0446u0443 materials...")
            try:
                cursor.execute("ALTER TABLE materials ADD COLUMN storage_path VARCHAR(512);")
                conn.commit()
                print("u041au043eu043bu043eu043du043au0430 storage_path u0443u0441u043fu0435u0448u043du043e u0434u043eu0431u0430u0432u043bu0435u043du0430.")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print("u041au043eu043bu043eu043du043au0430 storage_path u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442.")
                else:
                    raise
        else:
            print("\n[3/3] u041au043eu043bu043eu043du043au0430 storage_path u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u0432 u0442u0430u0431u043bu0438u0446u0435 materials.")
        
        # u0417u0430u043au0440u044bu0432u0430u0435u043c u0441u043eu0435u0434u0438u043du0435u043du0438u0435 u0441 u0431u0430u0437u043eu0439 u0434u0430u043du043du044bu0445
        conn.close()
        
        print("\nu0418u0441u043fu0440u0430u0432u043bu0435u043du0438u0435 u0441u0442u0440u0443u043au0442u0443u0440u044b u0442u0430u0431u043bu0438u0446u044b materials u0437u0430u0432u0435u0440u0448u0435u043du043e.")
        
    except Exception as e:
        print(f"u041eu0448u0438u0431u043au0430 u043fu0440u0438 u0438u0441u043fu0440u0430u0432u043bu0435u043du0438u0438 u0441u0442u0440u0443u043au0442u0443u0440u044b u0442u0430u0431u043bu0438u0446u044b materials: {str(e)}")

if __name__ == "__main__":
    fix_materials_storage()
