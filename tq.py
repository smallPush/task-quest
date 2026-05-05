import json
import os
import sys
import argparse
from datetime import datetime

DATA_DIR = os.path.expanduser("~/.taskquest")
LEGACY_DATA_FILE = os.path.expanduser("~/.taskquest.json")

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

def parse_markdown(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    lines = content.splitlines()
    item = {}
    body = []
    in_frontmatter = False
    frontmatter_count = 0

    for line in lines:
        if line.strip() == "---" and frontmatter_count < 2:
            in_frontmatter = not in_frontmatter
            frontmatter_count += 1
            continue

        if in_frontmatter:
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                # Type inference
                if val.isdigit():
                    val = int(val)
                elif val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                elif val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                # Special handling for habits list which might have been serialized as string
                if key == "habits" and val.startswith("[") and val.endswith("]"):
                    try:
                        import ast
                        val = ast.literal_eval(val)
                    except:
                        pass
                item[key] = val
        else:
            body.append(line)

    desc = "\n".join(body).strip()
    if desc:
        item["desc"] = desc

    return item

def write_markdown(item, filepath):
    with open(filepath, "w") as f:
        f.write("---\n")
        # Keep id first if it exists, otherwise type, etc. for cleaner viewing
        keys = list(item.keys())
        keys.remove("desc") if "desc" in keys else None

        # Ensure id is at the front if it exists
        if "id" in keys:
            keys.remove("id")
            keys.insert(0, "id")

        for key in keys:
            val = item[key]
            if isinstance(val, str):
                f.write(f'{key}: "{val}"\n')
            else:
                f.write(f"{key}: {val}\n")
        f.write("---\n\n")

        if "desc" in item:
            f.write(f"{item['desc']}\n")

def load_data():
    data = {"xp": 0, "tasks": [], "history": [], "habits": []}

    if not os.path.exists(DATA_DIR):
        # Migration from legacy JSON if it exists
        if os.path.exists(LEGACY_DATA_FILE):
            with open(LEGACY_DATA_FILE, "r") as f:
                data = json.load(f)
            # Make sure to return so it can trigger a save_data later
            return data
        else:
            return data

    # Load status
    status_file = os.path.join(DATA_DIR, "status.md")
    if os.path.exists(status_file):
        status_data = parse_markdown(status_file)
        data["xp"] = status_data.get("xp", 0)
        data["habits"] = status_data.get("habits", [])

    # Load tasks
    tasks_dir = os.path.join(DATA_DIR, "tasks")
    if os.path.exists(tasks_dir):
        for filename in os.listdir(tasks_dir):
            if filename.endswith(".md"):
                item = parse_markdown(os.path.join(tasks_dir, filename))
                data["tasks"].append(item)
    # Sort tasks by ID to keep logical order
    data["tasks"].sort(key=lambda x: x.get("id", 0))

    # Load history
    history_dir = os.path.join(DATA_DIR, "history")
    if os.path.exists(history_dir):
        for filename in os.listdir(history_dir):
            if filename.endswith(".md"):
                item = parse_markdown(os.path.join(history_dir, filename))
                data["history"].append(item)
    # History can be sorted by completed_at or date
    data["history"].sort(key=lambda x: x.get("completed_at", x.get("date", "")))

    return data

def save_data(data):
    # Ensure directories exist
    tasks_dir = os.path.join(DATA_DIR, "tasks")
    history_dir = os.path.join(DATA_DIR, "history")
    os.makedirs(tasks_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)

    # Write status.md
    status_file = os.path.join(DATA_DIR, "status.md")
    status_item = {"xp": data.get("xp", 0)}
    # Add habits if they exist and are non-empty
    if data.get("habits"):
        status_item["habits"] = data["habits"]
    write_markdown(status_item, status_file)

    # Clear old tasks before writing new ones to ensure deleted/completed tasks are actually removed
    for filename in os.listdir(tasks_dir):
        if filename.endswith(".md"):
            os.remove(os.path.join(tasks_dir, filename))

    # Write tasks
    for task in data.get("tasks", []):
        task_id = task.get("id", "0")
        filepath = os.path.join(tasks_dir, f"task_{task_id}.md")
        write_markdown(task, filepath)

    # Write history
    # Clear old history first to ensure no old files linger and no accidental overwrites due to naming bugs
    for filename in os.listdir(history_dir):
        if filename.endswith(".md"):
            os.remove(os.path.join(history_dir, filename))

    for i, action in enumerate(data.get("history", [])):
        # determine timestamp
        ts = action.get("completed_at") or action.get("date") or datetime.now().isoformat()
        # safe filename, adding index to guarantee uniqueness for items with same timestamp
        safe_ts = ts.replace(":", "-").replace(".", "-")
        filename = f"hist_{safe_ts}_{i}.md"
        filepath = os.path.join(history_dir, filename)
        write_markdown(action, filepath)

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
