import tkinter as tk
from tkinter import simpledialog, messagebox
import json

class CrosswordEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Crossword Grid Editor")
        self.grid_size = 14
        self.grid = [[{} for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.entries = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.create_grid()
        self.done_button = tk.Button(master, text="Done with Grid", command=self.done_with_grid)
        self.done_button.grid(row=self.grid_size, column=0, columnspan=self.grid_size)

    def create_grid(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                btn = tk.Button(self.master, width=4, height=2, command=lambda x=i, y=j: self.edit_cell(x, y))
                btn.grid(row=i, column=j)
                self.entries[i][j] = btn

    def edit_cell(self, row, col):
        letter = simpledialog.askstring("Input", f"Enter letter for cell ({row},{col}):")
        if letter:
            self.grid[row][col]["letter"] = letter.lower()
        number = simpledialog.askstring("Input", f"Enter number for cell ({row},{col}) (optional):")
        if number:
            try:
                self.grid[row][col]["number"] = int(number)
            except ValueError:
                pass
        display = self.grid[row][col].get("letter", "")
        if "number" in self.grid[row][col]:
            display = f"{self.grid[row][col]['number']}\n{display}"
        self.entries[row][col].config(text=display)

    def done_with_grid(self):
        self.clues = {"across": [], "down": []}
        self.ask_clues("across")

    def ask_clues(self, direction):
        while True:
            number = simpledialog.askstring("Clues", f"Enter {direction} clue number (or type 'next' to move on):")
            if number == 'next':
                if direction == "across":
                    return self.ask_clues("down")
                else:
                    return self.finish()
            clue = simpledialog.askstring("Clue", f"Enter clue for number {number} ({direction}):")
            if number and clue:
                try:
                    self.clues[direction].append({"number": int(number), "clue": clue})
                except ValueError:
                    pass

    def finish(self):
        data = {
            "grid": self.grid,
            "clues": self.clues
        }
        with open("crossword.json", "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "Crossword saved as crossword.json")
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = CrosswordEditor(root)
    root.mainloop()
