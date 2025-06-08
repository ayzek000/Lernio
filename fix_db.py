import os
import sqlite3
import shutil

def fix_database():
    print("\n[1/5] u041fu0440u043eu0432u0435u0440u043au0430 u0431u0430u0437 u0434u0430u043du043du044bu0445...")
    
    # u041fu0443u0442u0438 u043a u0431u0430u0437u0430u043c u0434u0430u043du043du044bu0445
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    app_db_path = os.path.join(instance_dir, 'app.db')
    site_db_path = os.path.join(instance_dir, 'site.db')
    
    # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u0444u0430u0439u043bu043eu0432 u0431u0430u0437 u0434u0430u043du043du044bu0445
    app_db_exists = os.path.exists(app_db_path)
    site_db_exists = os.path.exists(site_db_path)
    
    print(f"app.db u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442: {app_db_exists}")
    print(f"site.db u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442: {site_db_exists}")
    
    # u0415u0441u043bu0438 u043eu0431u0435 u0431u0430u0437u044b u0434u0430u043du043du044bu0445 u0441u0443u0449u0435u0441u0442u0432u0443u044eu0442, u0441u0434u0435u043bu0430u0435u043c u0440u0435u0437u0435u0440u0432u043du044bu0435 u043au043eu043fu0438u0438
    if app_db_exists and site_db_exists:
        print("\n[2/5] u0421u043eu0437u0434u0430u043du0438u0435 u0440u0435u0437u0435u0440u0432u043du044bu0445 u043au043eu043fu0438u0439...")
        try:
            shutil.copy2(app_db_path, f"{app_db_path}.backup")
            shutil.copy2(site_db_path, f"{site_db_path}.backup")
            print("u0420u0435u0437u0435u0440u0432u043du044bu0435 u043au043eu043fu0438u0438 u0441u043eu0437u0434u0430u043du044b.")
        except Exception as e:
            print(f"u041eu0448u0438u0431u043au0430 u043fu0440u0438 u0441u043eu0437u0434u0430u043du0438u0438 u0440u0435u0437u0435u0440u0432u043du044bu0445 u043au043eu043fu0438u0439: {str(e)}")
            return
    
    # u041fu0440u043eu0432u0435u0440u044fu0435u043c u0441u0442u0440u0443u043au0442u0443u0440u0443 u0442u0430u0431u043bu0438u0446u044b materials u0432 site.db
    if site_db_exists:
        print("\n[3/5] u041fu0440u043eu0432u0435u0440u043au0430 u0441u0442u0440u0443u043au0442u0443u0440u044b u0442u0430u0431u043bu0438u0446u044b materials u0432 site.db...")
        try:
            conn = sqlite3.connect(site_db_path)
            cursor = conn.cursor()
            
            # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u0442u0430u0431u043bu0438u0446u044b materials
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='materials';")
            if not cursor.fetchone():
                print("u0422u0430u0431u043bu0438u0446u0430 materials u043du0435 u043du0430u0439u0434u0435u043du0430 u0432 site.db!")
                conn.close()
                return
            
            # u041fu0440u043eu0432u0435u0440u044fu0435u043c u043du0430u043bu0438u0447u0438u0435 u043fu043eu043bu0435u0439 order u0438 position
            cursor.execute("PRAGMA table_info(materials);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            has_order = 'order' in column_names
            has_position = 'position' in column_names
            
            print(f"u041fu043eu043bu0435 'order' u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442: {has_order}")
            print(f"u041fu043eu043bu0435 'position' u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442: {has_position}")
            
            # u0415u0441u043bu0438 u0435u0441u0442u044c u043eu0431u0430 u043fu043eu043bu044f, u043au043eu043fu0438u0440u0443u0435u043c u0434u0430u043du043du044bu0435 u0438u0437 position u0432 order
            if has_order and has_position:
                print("u041au043eu043fu0438u0440u0443u0435u043c u0434u0430u043du043du044bu0435 u0438u0437 position u0432 order...")
                cursor.execute("UPDATE materials SET \"order\" = position WHERE position IS NOT NULL AND \"order\" IS NULL;")
                conn.commit()
                print("u0414u0430u043du043du044bu0435 u0441u043au043eu043fu0438u0440u043eu0432u0430u043du044b.")
            # u0415u0441u043bu0438 u0435u0441u0442u044c u0442u043eu043bu044cu043au043e position, u0441u043eu0437u0434u0430u0435u043c order u0438 u043au043eu043fu0438u0440u0443u0435u043c u0434u0430u043du043du044bu0435
            elif not has_order and has_position:
                print("u0421u043eu0437u0434u0430u0435u043c u043fu043eu043bu0435 order u0438 u043au043eu043fu0438u0440u0443u0435u043c u0434u0430u043du043du044bu0435 u0438u0437 position...")
                cursor.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                cursor.execute("UPDATE materials SET \"order\" = position WHERE position IS NOT NULL;")
                conn.commit()
                print("u041fu043eu043bu0435 order u0441u043eu0437u0434u0430u043du043e u0438 u0434u0430u043du043du044bu0435 u0441u043au043eu043fu0438u0440u043eu0432u0430u043du044b.")
            # u0415u0441u043bu0438 u043du0435u0442 u043du0438 u043eu0434u043du043eu0433u043e u043fu043eu043bu044f, u0441u043eu0437u0434u0430u0435u043c order
            elif not has_order and not has_position:
                print("u0421u043eu0437u0434u0430u0435u043c u043fu043eu043bu0435 order...")
                cursor.execute("ALTER TABLE materials ADD COLUMN \"order\" INTEGER DEFAULT 0;")
                conn.commit()
                print("u041fu043eu043bu0435 order u0441u043eu0437u0434u0430u043du043e.")
            
            conn.close()
        except Exception as e:
            print(f"u041eu0448u0438u0431u043au0430 u043fu0440u0438 u043fu0440u043eu0432u0435u0440u043au0435 u0441u0442u0440u0443u043au0442u0443u0440u044b u0442u0430u0431u043bu0438u0446u044b materials: {str(e)}")
            return
    
    # u0415u0441u043bu0438 u0441u0443u0449u0435u0441u0442u0432u0443u044eu0442 u043eu0431u0435 u0431u0430u0437u044b u0434u0430u043du043du044bu0445, u0443u0434u0430u043bu044fu0435u043c app.db
    if app_db_exists and site_db_exists:
        print("\n[4/5] u0423u0434u0430u043bu0435u043du0438u0435 u043du0435u0438u0441u043fu043eu043bu044cu0437u0443u0435u043cu043eu0439 u0431u0430u0437u044b u0434u0430u043du043du044bu0445 app.db...")
        try:
            os.remove(app_db_path)
            print("app.db u0443u0441u043fu0435u0448u043du043e u0443u0434u0430u043bu0435u043du0430.")
        except Exception as e:
            print(f"u041eu0448u0438u0431u043au0430 u043fu0440u0438 u0443u0434u0430u043bu0435u043du0438u0438 app.db: {str(e)}")
    
    print("\n[5/5] u041fu0440u043eu0432u0435u0440u043au0430 u0437u0430u0432u0435u0440u0448u0435u043du0430.")
    print("u0422u0435u043fu0435u0440u044c u043fu0440u043eu0435u043au0442 u043du0430u0441u0442u0440u043eu0435u043d u043du0430 u0438u0441u043fu043eu043bu044cu0437u043eu0432u0430u043du0438u0435 u0442u043eu043bu044cu043au043e u043eu0434u043du043eu0439 u0431u0430u0437u044b u0434u0430u043du043du044bu0445: site.db")

if __name__ == "__main__":
    fix_database()
