import os
import sys
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin(username, password, full_name=None):
    print("\n[1/3] u041fu0440u043eu0432u0435u0440u043au0430 u0431u0430u0437u044b u0434u0430u043du043du044bu0445...")
    
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
        
        # u041fu0440u043eu0432u0435u0440u044fu0435u043c, u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442 u043bu0438 u0443u0436u0435 u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044c u0441 u0442u0430u043au0438u043c u0438u043cu0435u043du0435u043c
        print(f"\n[2/3] u041fu0440u043eu0432u0435u0440u043au0430 u043du0430u043bu0438u0447u0438u044f u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f {username}...")
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f"u041fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044c u0441 u0438u043cu0435u043du0435u043c {username} u0443u0436u0435 u0441u0443u0449u0435u0441u0442u0432u0443u0435u0442. u0412u044bu0431u0435u0440u0438u0442u0435 u0434u0440u0443u0433u043eu0435 u0438u043cu044f u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f.")
            conn.close()
            return
        
        # u0421u043eu0437u0434u0430u0435u043c u0445u0435u0448 u043fu0430u0440u043eu043bu044f
        password_hash = generate_password_hash(password)
        registration_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # u0414u043eu0431u0430u0432u043bu044fu0435u043c u043du043eu0432u043eu0433u043e u0430u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u043eu0440u0430
        print(f"\n[3/3] u0421u043eu0437u0434u0430u043du0438u0435 u043du043eu0432u043eu0433u043e u0430u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u043eu0440u0430...")
        cursor.execute("""
        INSERT INTO users (username, password_hash, role, full_name, registration_date)
        VALUES (?, ?, ?, ?, ?)
        """, (username, password_hash, 'admin', full_name, registration_date))
        
        # u0421u043eu0445u0440u0430u043du044fu0435u043c u0438u0437u043cu0435u043du0435u043du0438u044f
        conn.commit()
        
        # u041fu043eu043bu0443u0447u0430u0435u043c ID u043du043eu0432u043eu0433u043e u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user_id = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\nu0410u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u043eu0440 {username} (ID: {user_id}) u0443u0441u043fu0435u0448u043du043e u0441u043eu0437u0434u0430u043d.")
        print("u0422u0435u043fu0435u0440u044c u0432u044b u043cu043eu0436u0435u0442u0435 u0432u043eu0439u0442u0438 u0432 u0441u0438u0441u0442u0435u043cu0443 u0441 u044du0442u0438u043cu0438 u0443u0447u0435u0442u043du044bu043cu0438 u0434u0430u043du043du044bu043cu0438.")
        
    except Exception as e:
        print(f"\nu041eu0448u0438u0431u043au0430 u043fu0440u0438 u0441u043eu0437u0434u0430u043du0438u0438 u0430u0434u043cu0438u043du0438u0441u0442u0440u0430u0442u043eu0440u0430: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("u0418u0441u043fu043eu043bu044cu0437u043eu0432u0430u043du0438u0435: python create_admin.py <u0438u043cu044f_u043fu043eu043bu044cu0437u043eu0432u0430u0442u0435u043bu044f> <u043fu0430u0440u043eu043bu044c> [u043fu043eu043bu043du043eu0435_u0438u043cu044f]")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    full_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    create_admin(username, password, full_name)
