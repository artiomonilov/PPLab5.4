import tkinter as tk; root = tk.Tk(); from main import TicTacToeApp; app = TicTacToeApp(root); app.player_name='Test'; app.setup_ui(); app.connect_to_queue(); root.update()  
