import json
import os
import sys
import argparse
from datetime import datetime

DATA_FILE = os.path.expanduser("~/.taskquest.json")

# RPG Constants
XP_PER_LEVEL = 1000
LEVEL_TITLES = {
    0: "Novice",
    5: "Apprentice",
    10: "Warrior",
    20: "Knight",
    35: "Paladin",
    50: "Hero",
    75: "Legend",
    100: "Transcendent"
}

# Evolution ASCII Art
CHARACTERS = [
    # Level 0-4: The Seed/Novice
    (0, """
      (  )
       ||
    """),
    # Level 5-9: The Sprout/Apprentice
    (5, """
      \\__/
      (oo)
     /||||\\
    """),
    # Level 10-19: The Warrior
    (10, """
      /  \\
     | -- |
     | vv |  /---
     /____\\ [ I ]
      |  |   \\---
    """),
    # Level 20-34: The Knight
    (20, """
       ___
      |_|_|
      (0.0)  /===>
      /|_|\\_//
     |     |/
      |___|
      _| |_
    """),
    # Level 35-49: The Paladin
    (35, """
        _
       / \\
      |   |  /--|
      |o.o| /   |
     /| - |\\    |
    | |___| |---/
     /     \\
    |_______|
     _|   |_
    """),
    # Level 50+: The Hero/Legend
    (50, """
        /\\
       (  )
       ||||   /|\\
      |XXXX| / | \\
      |XooX|{--|--}
      |X--X| \\ | /
      /XXXX\\  \\|/
     |______|
      _|  |_
    """)
]

# Colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RED = "\033[91m"
ENDC = "\033[0m"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"xp": 0, "tasks": [], "history": [], "habits": []}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_level(xp):
    return xp // XP_PER_LEVEL

def get_title(level):
    title = "Novice"
    for l, t in sorted(LEVEL_TITLES.items()):
        if level >= l:
            title = t
        else:
            break
    return title

def get_character(level):
    char_art = CHARACTERS[0][1]
    for l, art in CHARACTERS:
        if level >= l:
            char_art = art
        else:
            break
    return char_art

def print_status(data):
    xp = data["xp"]
    level = get_level(xp)
    next_level_xp = (level + 1) * XP_PER_LEVEL
    current_level_xp = xp % XP_PER_LEVEL
    
    # Progress bar
    bar_width = 30
    filled = int(current_level_xp / XP_PER_LEVEL * bar_width)
    
    # Color coding based on progress
    if filled > bar_width * 0.8:
        bar_color = YELLOW
    elif filled > bar_width * 0.5:
        bar_color = GREEN
    else:
        bar_color = BLUE
        
    bar = f"{bar_color}{'█' * filled}{ENDC}{'░' * (bar_width - filled)}"
    
    print(f"\n{BOLD}{CYAN}═══ TaskQuest Evolution ═══{ENDC}")
    
    # Print Character
    char_art = get_character(level)
    for line in char_art.splitlines():
        if line.strip():
            print(f"  {MAGENTA}{line}{ENDC}")
    
    print(f"\n{BOLD}Title:{ENDC} {MAGENTA}{get_title(level)}{ENDC}")
    print(f"{BOLD}Level:{ENDC} {YELLOW}{level}{ENDC}")
    print(f"{BOLD}XP:   {ENDC} {xp} / {next_level_xp}")
    print(f"[{bar}] {int(current_level_xp/XP_PER_LEVEL*100)}%")
    
    # Recent wins
    recent = 0
    now = datetime.now()
    for h in data.get("history", []):
        try:
            date_str = h.get("completed_at") or h.get("date")
            if date_str and (now - datetime.fromisoformat(date_str)).days < 1:
                recent += 1
        except: continue
            
    print(f"{BOLD}Pending Tasks:{ENDC} {len(data['tasks'])} | {BOLD}Daily Victories:{ENDC} {recent}")

def print_level_up(level):
    title = get_title(level)
    print(f"\n{BOLD}{YELLOW}╔═══════════════════════════════════════════╗")
    print(f"║                                           ║")
    print(f"║   {RED}✨ CONGRATULATIONS! ✨{YELLOW}                  ║")
    print(f"║                                           ║")
    print(f"║   YOU HAVE EVOLVED TO LEVEL {level:2}            ║")
    print(f"║   NEW TITLE: {title.upper():15}              ║")
    print(f"║                                           ║")
    print(f"╚═══════════════════════════════════════════╝{ENDC}\n")
    
    # Show the new character
    print(f"{MAGENTA}{get_character(level)}{ENDC}")

def add_task(data, description, xp_reward):
    task = {
        "id": len(data["tasks"]) + 1,
        "desc": description,
        "xp": int(xp_reward),
        "created": datetime.now().isoformat()
    }
    data["tasks"].append(task)
    save_data(data)
    print(f"{GREEN}✔ Task Quest Accepted:{ENDC} {description} (+{xp_reward} XP)")

def complete_task(data, task_idx):
    if 0 <= task_idx < len(data["tasks"]):
        task = data["tasks"].pop(task_idx)
        old_level = get_level(data["xp"])
        data["xp"] += task["xp"]
        new_level = get_level(data["xp"])
        
        task["completed_at"] = datetime.now().isoformat()
        data["history"].append(task)
        save_data(data)
        
        print(f"\n{BOLD}{GREEN}⚔ Victory!{ENDC} You gained {task['xp']} XP for '{task['desc']}'")
        if new_level > old_level:
            print_level_up(new_level)
    else:
        print(f"{RED}Error: That quest does not exist in your log.{ENDC}")

def list_tasks(data):
    if not data["tasks"]:
        print(f"\n{BLUE}Your quest log is empty. Rest well, hero.{ENDC}")
        return
    
    print(f"\n{BOLD}{CYAN}══ Current Quests ══{ENDC}")
    for i, t in enumerate(data["tasks"]):
        print(f"{BOLD}{i+1}.{ENDC} {t['desc']:40} {YELLOW}[{t['xp']} XP]{ENDC}")

def good_action(data, description, xp_reward):
    old_level = get_level(data["xp"])
    data["xp"] += int(xp_reward)
    new_level = get_level(data["xp"])
    
    action = {
        "type": "good_action",
        "desc": description,
        "xp": int(xp_reward),
        "date": datetime.now().isoformat()
    }
    data["history"].append(action)
    save_data(data)
    
    print(f"\n{BOLD}{CYAN}♥ Virtue Recorded!{ENDC} {description} (+{xp_reward} XP)")
    if new_level > old_level:
        print_level_up(new_level)

def list_source(data):
    if not data["tasks"]:
        print(f"\n{BLUE}Data source is empty. No pending records.{ENDC}")
        return
    
    print(f"\n{BOLD}{CYAN}══ Quest Data Source (Pending) ══{ENDC}")
    print(f"{BOLD}{'ID':<4} {'Date':<12} {'Reward':<10} {'Quest Description'}{ENDC}")
    print(f"{'-'*70}")
    for t in data["tasks"]:
        date = datetime.fromisoformat(t['created']).strftime('%Y-%m-%d')
        print(f"{t['id']:<4} {date:<12} {YELLOW}{t['xp']:>4} XP{ENDC}   {t['desc']}")

def main():
    parser = argparse.ArgumentParser(description="TaskQuest: Evolution")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("status")
    add_p = subparsers.add_parser("add")
    add_p.add_argument("desc")
    add_p.add_argument("xp", type=int, default=100, nargs="?")
    
    subparsers.add_parser("list")
    subparsers.add_parser("source")
    
    done_p = subparsers.add_parser("done")
    done_p.add_argument("index", type=int, nargs="?")
    
    good_p = subparsers.add_parser("good")
    good_p.add_argument("desc")
    good_p.add_argument("xp", type=int, default=50, nargs="?")

    args = parser.parse_args()
    data = load_data()
    
    if args.command == "status" or not args.command:
        print_status(data)
    elif args.command == "add":
        add_task(data, args.desc, args.xp)
    elif args.command == "list":
        list_tasks(data)
    elif args.command == "source":
        list_source(data)
    elif args.command == "done":
        if args.index is not None:
            complete_task(data, args.index - 1)
        else:
            list_tasks(data)
    elif args.command == "good":
        good_action(data, args.desc, args.xp)

if __name__ == "__main__":
    main()
