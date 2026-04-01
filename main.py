import tkinter as tk
from tkinter import simpledialog, messagebox
import sqlite3
import json
import os
import sys

class MockExistentialError(Exception): pass
class MockBusyError(Exception): pass

class MockMessageQueue:
    def __init__(self, key, flags=0):
        self.filename = f"queue_{key}.json"
        if flags != 0 and not os.path.exists(self.filename):
            try:
                with open(self.filename, 'w') as f:
                    json.dump([], f)
            except Exception:
                pass
        elif flags == 0 and not os.path.exists(self.filename):
            raise MockExistentialError("ExistentialError")

    def send(self, message, type=1):
        import time
        for _ in range(5):
            try:
                try:
                    with open(self.filename, 'r') as f:
                        data = json.load(f)
                except (FileNotFoundError, json.JSONDecodeError):
                    data = []
                data.append({"type": type, "msg": message.decode()})
                with open(self.filename, 'w') as f:
                    json.dump(data, f)
                break
            except Exception:
                time.sleep(0.05)

    def receive(self, type=0, block=True):
        import time
        while True:
            try:
                with open(self.filename, 'r') as f:
                    data = json.load(f)
                
                for i, item in enumerate(data):
                    if type == 0 or item["type"] == type:
                        data.pop(i)
                        with open(self.filename, 'w') as f:
                            json.dump(data, f)
                        return (item["msg"].encode(), item["type"])
            except Exception:
                pass
            
            if not block:
                raise MockBusyError("BusyError")
            time.sleep(0.1)

try:
    import sysv_ipc
    IPC_AVAILABLE = True
except ImportError:
    IPC_AVAILABLE = False
    print("Modulul sysv_ipc nu este instalat pe Windows. Folosim MockMessageQueue (Fisiere) ca fallback pentru teste.")
    # Fallback rapid pt testare pe Windows
    class sysv_ipc:
        IPC_CREAT = 1
        ExistentialError = MockExistentialError
        BusyError = MockBusyError
        MessageQueue = MockMessageQueue

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
        # Amână apelarea dialogului pentru a lăsa Tkinter să afișeze fereastra principală
        self.root.after(100, self.ask_name)

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
        
        # Aduce fereastra in prim-plan dupa ce dispare dialogul
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

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
        try:
            self.mq = sysv_ipc.MessageQueue(QUEUE_KEY)
            self.symbol = "0"
            self.opponent_symbol = "X"
            self.msg_type_send = 2
            self.msg_type_recv = 1
            
            join_msg = json.dumps({"action": "join", "name": self.player_name}).encode()
            self.mq.send(join_msg, type=self.msg_type_send)
            
            self.info_label.config(text=f"Jucator 2: {self.player_name} (0)\nAsteptare Player 1...")
            self.my_turn = False
            
        except sysv_ipc.ExistentialError:
            self.mq = sysv_ipc.MessageQueue(QUEUE_KEY, sysv_ipc.IPC_CREAT)
            self.symbol = "X"
            self.opponent_symbol = "0"
            self.msg_type_send = 1
            self.msg_type_recv = 2
            
            self.info_label.config(text=f"Jucator 1: {self.player_name} (X)\nAsteptare Player 2...")
            self.my_turn = False

        self.root.after(500, self.listen_queue)

    def load_score(self):
        self.cursor.execute("SELECT score1, score2 FROM scores WHERE player1=? AND player2=?",
                            (self.player_name, self.opponent_name))
        row = self.cursor.fetchone()
        if row:
            self.root.title(f"Scor: {self.player_name} [{row[0]} - {row[1]}] {self.opponent_name}")
        else:
            self.cursor.execute("SELECT score2, score1 FROM scores WHERE player1=? AND player2=?",
                                (self.opponent_name, self.player_name))
            row = self.cursor.fetchone()
            if row:
                self.root.title(f"Scor: {self.player_name} [{row[0]} - {row[1]}] {self.opponent_name}")
            else:
                self.root.title(f"Scor: {self.player_name} [0 - 0] {self.opponent_name}")

    def save_score(self, winner):
        self.cursor.execute("SELECT score1, score2 FROM scores WHERE player1=? AND player2=?",
                            (self.player_name, self.opponent_name))
        row = self.cursor.fetchone()
        
        if not row:
            self.cursor.execute("SELECT score1 FROM scores WHERE player1=? AND player2=?",
                                (self.opponent_name, self.player_name))
            if not self.cursor.fetchone():
                self.cursor.execute("INSERT INTO scores (player1, player2, score1, score2) VALUES (?, ?, 0, 0)",
                                    (self.player_name, self.opponent_name))

        if winner == self.player_name:
            self.cursor.execute("UPDATE scores SET score1 = score1 + 1 WHERE player1=? AND player2=?",
                                (self.player_name, self.opponent_name))
            self.cursor.execute("UPDATE scores SET score2 = score2 + 1 WHERE player1=? AND player2=?",
                                (self.opponent_name, self.player_name))
        elif winner == self.opponent_name:
            self.cursor.execute("UPDATE scores SET score2 = score2 + 1 WHERE player1=? AND player2=?",
                                (self.player_name, self.opponent_name))
            self.cursor.execute("UPDATE scores SET score1 = score1 + 1 WHERE player1=? AND player2=?",
                                (self.opponent_name, self.player_name))
        
        self.conn.commit()

    def listen_queue(self):
        try:
            message, t = self.mq.receive(type=self.msg_type_recv, block=False)
            data = json.loads(message.decode())
            
            if data["action"] == "join":
                self.opponent_name = data["name"]
                self.info_label.config(text=f"Adversar: {self.opponent_name}\nEsti la rand (X)!")
                self.my_turn = True
                
                ack_msg = json.dumps({"action": "ack_join", "name": self.player_name}).encode()
                self.mq.send(ack_msg, type=self.msg_type_send)
                self.load_score()
                
            elif data["action"] == "ack_join":
                self.opponent_name = data["name"]
                self.info_label.config(text=f"Adversar: {self.opponent_name}\nAsteapta (0)...")
                self.load_score()
                
            elif data["action"] == "move":
                idx = data["index"]
                self.board[idx] = self.opponent_symbol
                self.buttons[idx].config(text=self.opponent_symbol)
                
                if not self.check_winner(self.opponent_symbol, self.opponent_name):
                    self.my_turn = True
                    self.info_label.config(text="Esti la rand!")
                    
        except sysv_ipc.BusyError:
            pass
            
        self.root.after(500, self.listen_queue)

    def make_move(self, index):
        if self.board[index] == "" and self.my_turn:
            self.board[index] = self.symbol
            self.buttons[index].config(text=self.symbol)
            self.my_turn = False
            self.info_label.config(text="Randul oponentului")
            
            move_msg = json.dumps({"action": "move", "index": index}).encode()
            self.mq.send(move_msg, type=self.msg_type_send)
            
            self.check_winner(self.symbol, self.player_name)

    def check_winner(self, symbol, player):
        winning_combinations = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8), 
            (0, 3, 6), (1, 4, 7), (2, 5, 8), 
            (0, 4, 8), (2, 4, 6)             
        ]

        won = False
        for combo in winning_combinations:
            if self.board[combo[0]] == symbol and self.board[combo[1]] == symbol and self.board[combo[2]] == symbol:
                won = True
                break
                
        if won:
            messagebox.showinfo("Joc Terminat", f"Jucatorul {player} a castigat!")
            self.save_score(player)
            self.reset_game()
            return True
            
        if "" not in self.board:
            messagebox.showinfo("Joc Terminat", "Remiza!")
            self.reset_game()
            return True
            
        return False

    def reset_game(self):
        self.board = [""] * 9
        for btn in self.buttons:
            btn.config(text="")
        
        self.load_score()
        if self.symbol == "X":
            self.my_turn = True
            self.info_label.config(text="Joc resetat. Esti la rand (X)!")
        else:
            self.my_turn = False
            self.info_label.config(text="Joc resetat. Asteapta (0)...")

if __name__ == "__main__":
    root = tk.Tk()
    app = TicTacToeApp(root)
    root.mainloop()
