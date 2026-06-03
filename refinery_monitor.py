import os
import time
import curses

# --- CONFIGURATION ---
LOG_FILE = "/home/dalien/Refinery-01/refinery.log"
NODE_ID = "M4800-TAS-PRIME"
REFINERY_DIR = "/home/dalien/Refinery-01/inventory" # Where your data packets live

def get_stats():
    bot_hits = 0
    inventory_count = 0
    
    # Count Bot Hits from logs
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            for line in f:
                if "402" in line or "GPTBot" in line or "CCBot" in line:
                    bot_hits += 1
                    
    # Count processed data packets in inventory
    if os.path.exists(REFINERY_DIR):
        inventory_count = len([f for f in os.listdir(REFINERY_DIR) if os.path.isfile(os.path.join(REFINERY_DIR, f))])
        
    return bot_hits, inventory_count

def draw_dashboard(stdscr):
    # Hide cursor
    curses.curs_set(0)
    # Don't wait for input
    stdscr.nodelay(True)
    
    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        bot_hits, inventory = get_stats()
        
        # --- UI DRAWING ---
        stdscr.attron(curses.A_BOLD)
        stdscr.addstr(1, 2, f"REFINERY NODE: {NODE_ID}")
        stdscr.attroff(curses.A_BOLD)
        
        stdscr.addstr(2, 2, "=" * (width - 4))
        
        # Stats Block
        stdscr.addstr(4, 4, f"STATUS:    ONLINE (Tunnel Active)", curses.A_BOLD)
        stdscr.addstr(6, 4, f"BOT HITS:  {bot_hits}", curses.color_pair(1) if bot_hits > 0 else curses.A_NORMAL)
        stdscr.addstr(7, 4, f"INVENTORY: {inventory} Data Packets")
        
        stdscr.addstr(9, 2, "=" * (width - 4))
        stdscr.addstr(11, 4, "Press 'Q' to Exit Monitor")
        
        stdscr.refresh()
        
        # Check for exit key
        try:
            key = stdscr.getch()
            if key == ord('q') or key == ord('Q'):
                break
        except:
            pass
            
        time.sleep(2) # Refresh every 2 seconds

def main():
    # Initialize colors if supported
    curses.wrapper(draw_dashboard)

if __name__ == "__main__":
    # Create inventory dir if it doesn't exist so count doesn't error
    if not os.path.exists(REFINERY_DIR):
        os.makedirs(REFINERY_DIR)
    main()
