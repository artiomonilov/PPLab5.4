import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
import json
import os
import sys

try:
    import sysv_ipc
    IPC_AVAILABLE = True
except ImportError:
    IPC_AVAILABLE = False
    print("Modulul sysv_ipc nu este instalat sau nu este suportat nativ pe Windows.")
    print("Pentru rulare pe Windows, s-ar putea folosi un mecanism de fallback (ex: sockets sau fisiere).")

DB_FILE = "scores.db"
QUEUE_KEY = 1234

class TicTacToeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("X si 0 - P2P")
        self.root.geometry("400x450")

        self.player_name = ""
        self.opponent_name = ""
        self.symbol = "" 
        self.board = [""] * 9
        self.buttons = []
        self.my_turn = False

        self.init_db()
        self.ask_name()

    def init_db(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                player1 TEXT,
                player2 TEXT,
                score1 INTEGER,
                score2 INTEGER,
                PRIMARY KEY (player1, player2)
            )
        ''')
        self.conn.commit()

    def ask_name(self):
        self.player_name = simpledialog.askstring("Nume Jucator", "Introdu numele tau:")
        if not self.player_name:
            self.root.destroy()
            sys.exit()

        self.setup_ui()
        self.connect_to_queue()

    def setup_ui(self):
        self.info_label = tk.Label(self.root, text=f"Jucator: {self.player_name}\nAsteptare oponent...", font=("Arial", 12))
        self.info_label.pack(pady=10)

        self.grid_frame = tk.Frame(self.root)
        self.grid_frame.pack()

        for i in range(9):
            btn = tk.Button(self.grid_frame, text="", font=("Arial", 24), width=5, height=2,
                            command=lambda i=i: self.make_move(i))
            btn.grid(row=i//3, column=i%3)
            self.buttons.append(btn)

    def connect_to_queue(self):

        pass

    def make_move(self, index):
        if self.board[index] == "" and self.my_turn:
            self.board[index] = self.symbol
            self.buttons[index].config(text=self.symbol)
            self.my_turn = False
            self.info_label.config(text="Randul oponentului")

            self.check_winner()

    def check_winner(self):

        winning_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), 
            (0, 3, 6), (1, 4, 7), (2, 5, 8), 
            (0, 4, 8), (2, 4, 6)             
        ]

        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeApp(root)
    root.mainloop()
