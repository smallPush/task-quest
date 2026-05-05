# ⚔️ TaskQuest: CLI Evolution

TaskQuest is a gamified task manager for your terminal. It transforms your daily productivity into an RPG-style progression system where you earn XP, level up, and evolve your character avatar.

## 📂 Database Location
All your progress, task history, and evolution data is stored in a Markdown-based directory structure located at:
**`~/.taskquest/`**

The directory contains:
- `status.md`: Global stats (e.g., XP)
- `tasks/`: Directory containing active tasks as individual `.md` files
- `history/`: Directory containing completed tasks and good deeds as individual `.md` files

---

## 🚀 Commands

| Command | Action | Description |
|:---|:---|:---|
| `tq status` | **Check Status** | View your level, title, XP progress bar, and current avatar form. |
| `tq add "Desc" [XP]` | **Accept Quest** | Add a new pending task with an optional XP reward (default: 100). |
| `tq list` | **Quest Log** | List all your currently pending quests. |
| `tq done` | **Complete Quest** | Interactively select a quest to complete using `fzf`. |
| `tq good` | **Record Virtue** | Record a good deed or habit for instant XP gain. |
| `tq source` | **Data Source** | View technical details (IDs, Dates) of your pending quests. |

---

## 🧬 Evolution Mechanics
As you gain XP and reach new levels, your title and ASCII avatar will evolve:

*   **Novice** (Lvl 0): A tiny sprout.
*   **Apprentice** (Lvl 5): A growing plant.
*   **Warrior** (Lvl 10): Armed and ready.
*   **Knight** (Lvl 20): Heavily armored.
*   **Paladin** (Lvl 35): Holy protector.
*   **Hero** (Lvl 50): Legendary champion.

---

## 🛠️ Installation
The core logic resides in `~/repositories/task-quest/tq.py`. 
Integration is handled via the `tq()` function in your `~/extra_bash/functions.sh`.

To apply changes after an update:
```bash
source ~/.zshrc
```
