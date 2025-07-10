import tkinter as tk
from tkinter import simpledialog, messagebox
import json

class KakuroEditor:
    def __init__(self, master):
        self.master = master
        self.master.title("Kakuro Grid Editor")
        self.rows = 10
        self.cols = 9
        self.grid = [[{"type": "black"} for _ in range(self.cols)] for _ in range(self.rows)]
        self.buttons = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.create_grid()
        self.done_button = tk.Button(master, text="Done", command=self.save_puzzle)
        self.done_button.grid(row=self.rows, column=0, columnspan=self.cols)

    def create_grid(self):
        for i in range(self.rows):
            for j in range(self.cols):
                btn = tk.Button(self.master, width=6, height=3, command=lambda r=i, c=j: self.edit_cell(r, c))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def edit_cell(self, row, col):
        cell_type = simpledialog.askstring("Cell Type", "Enter 'w' for white or 'c' for clue:")
        if cell_type == 'w':
            self.grid[row][col] = {"type": "white"}
            self.buttons[row][col].config(text="W", bg="white")
        elif cell_type == 'c':
            clue = {"type": "clue"}
            while True:
                entry = simpledialog.askstring("Clue", "Enter clue (a<number> or d<number> or 'done'):")
                if not entry or entry == 'done':
                    break
                try:
                    if entry.startswith('a'):
                        clue["across"] = int(entry[1:])
                    elif entry.startswith('d'):
                        clue["down"] = int(entry[1:])
                except ValueError:
                    pass
            self.grid[row][col] = clue
            label = []
            if "across" in clue:
                label.append(f"A{clue['across']}")
            if "down" in clue:
                label.append(f"D{clue['down']}")
            self.buttons[row][col].config(text="\n".join(label), bg="lightgray")

    def save_puzzle(self):
        data = {"puzzles": [{"grid": self.grid}]}
        with open("kakuro_puzzle.json", "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "Kakuro puzzle saved as kakuro_puzzle.json")
        self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = KakuroEditor(root)
    root.mainloop()
