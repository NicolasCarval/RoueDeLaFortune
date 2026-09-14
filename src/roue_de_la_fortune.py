import os
import random
import unicodedata
import tkinter as tk
from tkinter import messagebox

# Constantes du plateau télévisé (4 lignes de 12 à 14 colonnes)
GRID_ROWS = 4
GRID_COLS = 14

VOYELLES = set("AEIOUY")
CONSONNES = set("BCDFGHJKLMNPQRSTVWXZ")

# Fichiers par défaut
FILES = {
    "courte": "enigmes_courtes.txt",
    "principale": "enigmes_principales.txt",
    "finale": "enigmes_finales.txt"
}

DEFAULT_DATA = {
    "enigmes_courtes.txt": [
        "Fromage / LA FONDUE SAVOYARDE",
        "Botanique / UNE HERBE AROMATIQUE",
        "Cinéma / UN FILM CULTE",
        "Gastronomie / UNE TARTE AUX POMMES"
    ],
    "enigmes_principales.txt": [
        "Proverbe / PIERRE QUI ROULE N'AMASSE PAS MOUSSE",
        "Chanson / TOURNER LES SERVIETTES ET CHANTER",
        "Voyage / UN TOUR DU MONDE EN VOILIER",
        "Expression / AVOIR DU PAIN SUR LA PLANCHE"
    ],
    "enigmes_finales.txt": [
        "Plante / OSEILLE",
        "Métier / ARCHITECTE",
        "Instrument / CLARINETTE",
        "Animal / ORNITHORYNQUE"
    ]
}


def strip_accents(text: str) -> str:
    """Normalise une chaîne : majuscules, sans accents."""
    text = unicodedata.normalize('NFD', text)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn').upper().strip()


class EnigmeLoader:
    @staticmethod
    def initialize_files():
        for filename, lines in DEFAULT_DATA.items():
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")

    @staticmethod
    def load(filename: str):
        EnigmeLoader.initialize_files()
        enigmes = []
        if not os.path.exists(filename):
            return enigmes

        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "/" not in line:
                    continue
                parts = line.split("/", 1)
                indice = parts[0].strip()
                raw_sol = parts[1].strip()
                clean_sol = strip_accents(raw_sol)
                enigmes.append({"indice": indice, "solution_clean": clean_sol, "solution_display": raw_sol.upper()})
        return enigmes


class RoueDeLaFortuneApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Entraînement - La Roue de la Fortune")
        self.geometry("1100x780")
        self.configure(bg="#0B1325")

        EnigmeLoader.initialize_files()

        # État du jeu
        self.mode = None
        self.bank = []
        self.current_enigme = None
        self.revealed_letters = set()
        self.lives = 5
        self.cagnotte = 0
        self.auto_timer = None
        self.auto_mode = False

        # Configuration grille
        self.grid_cells = []
        self.cell_labels = []

        self._build_ui()
        self.show_menu()

    def _build_ui(self):
        # En-tête
        self.top_bar = tk.Frame(self, bg="#111B33", pady=10, padx=20)
        self.top_bar.pack(fill=tk.X)

        self.lbl_title = tk.Label(self.top_bar, text="LA ROUE DE LA FORTUNE", font=("Helvetica", 16, "bold"), fg="#FFD700", bg="#111B33")
        self.lbl_title.pack(side=tk.LEFT)

        # BOUTON RETOUR AU MENU
        self.btn_home = tk.Button(
            self.top_bar,
            text="⌂ Menu Principal",
            font=("Helvetica", 10, "bold"),
            bg="#263238",
            fg="#ECEFF1",
            activebackground="#37474F",
            activeforeground="#FFFFFF",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2",
            command=self.confirm_return_menu
        )
        self.btn_home.pack(side=tk.LEFT, padx=20)

        self.lbl_status = tk.Label(self.top_bar, text="", font=("Helvetica", 12, "bold"), fg="#FFFFFF", bg="#111B33")
        self.lbl_status.pack(side=tk.RIGHT)

        # Indicateurs (Score / Vies / Indice)
        self.info_bar = tk.Frame(self, bg="#19284D", pady=8, padx=20)
        self.info_bar.pack(fill=tk.X)

        self.lbl_indice = tk.Label(self.info_bar, text="Indice : -", font=("Helvetica", 14, "bold"), fg="#00E5FF", bg="#19284D")
        self.lbl_indice.pack(side=tk.LEFT)

        self.lbl_lives = tk.Label(self.info_bar, text="Vies : 5", font=("Helvetica", 14, "bold"), fg="#FF5252", bg="#19284D")
        self.lbl_lives.pack(side=tk.RIGHT, padx=15)

        self.lbl_cagnotte = tk.Label(self.info_bar, text="Cagnotte : 0 €", font=("Helvetica", 14, "bold"), fg="#69F0AE", bg="#19284D")
        self.lbl_cagnotte.pack(side=tk.RIGHT, padx=15)

        # Conteneur du plateau
        self.board_container = tk.Frame(self, bg="#004D40", padx=15, pady=15, bd=5, relief=tk.RIDGE)
        self.board_container.pack(pady=20)

        for r in range(GRID_ROWS):
            row_labels = []
            for c in range(GRID_COLS):
                lbl = tk.Label(
                    self.board_container,
                    text="",
                    font=("Courier New", 22, "bold"),
                    width=2,
                    height=1,
                    relief=tk.RAISED,
                    bd=2,
                    bg="#00332C"  # Case inactive (vert sombre)
                )
                lbl.grid(row=r, column=c, padx=3, pady=3)
                row_labels.append(lbl)
            self.cell_labels.append(row_labels)

        # Zone d'interaction dynamique
        self.control_area = tk.Frame(self, bg="#0B1325")
        self.control_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    def clear_control_area(self):
        for widget in self.control_area.winfo_children():
            widget.destroy()

    # --- Gestion du Tableau ---

    def _format_solution_to_grid(self, solution: str):
        """Répartit les mots de la solution sur les 4 lignes en centrant chaque ligne."""
        words = solution.split(" ")
        lines = [[] for _ in range(GRID_ROWS)]
        cur_row = 1 if len(solution) <= 24 else 0

        current_line = []
        cur_len = 0

        for w in words:
            word_len = len(w)
            needed = word_len if not current_line else cur_len + 1 + word_len
            if needed <= GRID_COLS:
                current_line.append(w)
                cur_len = needed
            else:
                if cur_row < GRID_ROWS:
                    lines[cur_row] = current_line
                    cur_row += 1
                current_line = [w]
                cur_len = word_len

        if cur_row < GRID_ROWS and current_line:
            lines[cur_row] = current_line

        # Si seules 1 ou 2 lignes sont utilisées, on équilibre verticalement
        used = [idx for idx, l in enumerate(lines) if l]
        if len(used) == 1 and used[0] != 1:
            lines[1], lines[used[0]] = lines[used[0]], []
        elif len(used) == 2 and used != [1, 2]:
            lines[1] = lines[used[0]]
            lines[2] = lines[used[1]]
            if used[0] != 1 and used[1] != 1:
                lines[used[0]] = []
            if used[0] != 2 and used[1] != 2:
                lines[used[1]] = []

        grid = [[" " for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
        for r_idx, words_in_row in enumerate(lines):
            row_str = " ".join(words_in_row)
            start_col = max(0, (GRID_COLS - len(row_str)) // 2)
            for i, ch in enumerate(row_str):
                if start_col + i < GRID_COLS:
                    grid[r_idx][start_col + i] = ch

        return grid

    def render_board(self):
        if not self.current_enigme:
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    self.cell_labels[r][c].config(text="", bg="#00332C")
            return

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                target_char = self.grid_cells[r][c]
                lbl = self.cell_labels[r][c]

                if target_char == " ":
                    lbl.config(text="", bg="#00332C")
                elif target_char in ("'", "-", ","):
                    lbl.config(text=target_char, bg="#FFFFFF", fg="#000000")
                elif target_char in self.revealed_letters:
                    lbl.config(text=target_char, bg="#FFFFFF", fg="#000000")
                else:
                    lbl.config(text="", bg="#FFFFFF")

    # --- Vues et Menus ---
    def confirm_return_menu(self):
        """Demande confirmation si une manche est en cours, puis retourne au menu."""
        if self.current_enigme is not None:
            if not messagebox.askyesno("Retour Menu", "Voulez-vous abandonner cette manche et revenir au menu principal ?"):
                return
        self.show_menu()

    def show_menu(self):
        self.stop_timer()
        self.clear_control_area()
        self.current_enigme = None
        self.render_board()

        self.lbl_indice.config(text="Sélectionnez une manche")
        self.lbl_status.config(text="Entraînement Libre")
        self.lbl_lives.config(text="")
        self.lbl_cagnotte.config(text="")

        frame = tk.Frame(self.control_area, bg="#0B1325")
        frame.pack(expand=True)

        tk.Label(frame, text="Choisissez votre session :", font=("Helvetica", 14), fg="#FFFFFF", bg="#0B1325").pack(pady=10)

        btn_opt = {"font": ("Helvetica", 12, "bold"), "width": 25, "pady": 6}
        tk.Button(frame, text="1. Énigme Rapide", bg="#0288D1", fg="white", command=lambda: self.start_session("courte"), **btn_opt).pack(pady=6)
        tk.Button(frame, text="2. Manche Principale", bg="#388E3C", fg="white", command=lambda: self.start_session("principale"), **btn_opt).pack(pady=6)
        tk.Button(frame, text="3. Finale", bg="#D32F2F", fg="white", command=lambda: self.start_session("finale"), **btn_opt).pack(pady=6)

    def start_session(self, mode: str):
        self.mode = mode
        self.bank = EnigmeLoader.load(FILES[mode])
        if not self.bank:
            messagebox.showwarning("Banque vide", f"Le fichier {FILES[mode]} ne contient aucune énigme valide.")
            self.show_menu()
            return

        self.cagnotte = 0
        self.lives = 5
        self.next_enigme()

    def next_enigme(self):
        self.stop_timer()
        if not self.bank:
            messagebox.showinfo("Terminé", "Toutes les énigmes de ce fichier ont été passées.")
            self.show_menu()
            return

        self.current_enigme = random.choice(self.bank)
        self.bank.remove(self.current_enigme)

        self.grid_cells = self._format_solution_to_grid(self.current_enigme["solution_clean"])
        self.revealed_letters = set()

        self.lbl_indice.config(text=f"Indice : {self.current_enigme['indice']}")
        self.update_stats()

        if self.mode == "courte":
            self.setup_courte_view()
        elif self.mode == "principale":
            self.setup_principale_view()
        elif self.mode == "finale":
            self.setup_finale_view()

        self.render_board()

    def update_stats(self):
        self.lbl_lives.config(text=f"Vies : {self.lives}")
        self.lbl_cagnotte.config(text=f"Cagnotte : {self.cagnotte} €")

    # --- Mode 1 : Énigme Rapide ---

    def setup_courte_view(self):
        self.clear_control_area()
        self.lbl_status.config(text="Manche : Énigme Rapide")

        bar = tk.Frame(self.control_area, bg="#0B1325")
        bar.pack(fill=tk.X, pady=5)

        tk.Button(bar, text="Nouvelle Lettre", bg="#FFA000", font=("Helvetica", 11, "bold"), command=self.reveal_one_letter).pack(side=tk.LEFT, padx=10)

        self.btn_auto = tk.Button(bar, text="Auto (5s) : OFF", bg="#455A64", fg="white", font=("Helvetica", 11), command=self.toggle_auto)
        self.btn_auto.pack(side=tk.LEFT, padx=10)

        # Zone proposition solution
        resolve_bar = tk.Frame(self.control_area, bg="#0B1325", pady=10)
        resolve_bar.pack(fill=tk.X)

        tk.Label(resolve_bar, text="Solution :", fg="#FFFFFF", bg="#0B1325", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.ent_sol = tk.Entry(resolve_bar, font=("Helvetica", 14), width=35)
        self.ent_sol.pack(side=tk.LEFT, padx=5)
        self.ent_sol.bind("<Return>", lambda e: self.check_solution_courte())

        tk.Button(resolve_bar, text="Buzzer & Valider", bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), command=self.check_solution_courte).pack(side=tk.LEFT, padx=10)
        tk.Button(resolve_bar, text="Passer", bg="#757575", fg="white", font=("Helvetica", 11), command=self.next_enigme).pack(side=tk.RIGHT, padx=5)

    def toggle_auto(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.btn_auto.config(text="Auto (5s) : ON", bg="#2E7D32")
            self.auto_timer_tick()
        else:
            self.btn_auto.config(text="Auto (5s) : OFF", bg="#455A64")
            self.stop_timer()

    def auto_timer_tick(self):
        if not self.auto_mode:
            return
        self.reveal_one_letter()
        self.auto_timer = self.after(5000, self.auto_timer_tick)

    def stop_timer(self):
        if self.auto_timer:
            self.after_cancel(self.auto_timer)
            self.auto_timer = None
        self.auto_mode = False

    def reveal_one_letter(self):
        sol_chars = set(c for c in self.current_enigme["solution_clean"] if c.isalpha())
        hidden = list(sol_chars - self.revealed_letters)
        if hidden:
            picked = random.choice(hidden)
            self.revealed_letters.add(picked)
            self.render_board()
            if set(sol_chars) == self.revealed_letters:
                self.stop_timer()
                messagebox.showinfo("Révélé", "Toutes les lettres sont affichées.")

    def check_solution_courte(self):
        prop = strip_accents(self.ent_sol.get())
        if not prop:
            return
        if prop == self.current_enigme["solution_clean"]:
            self.stop_timer()
            self.cagnotte += 100
            messagebox.showinfo("Bravo !", f"Bonne réponse : {self.current_enigme['solution_display']} (+100 €)")
            self.next_enigme()
        else:
            self.lives -= 1
            self.update_stats()
            messagebox.showerror("Faux", f"'{prop}' n'est pas la solution. Vous perdez 1 vie.")
            if self.lives <= 0:
                self.game_over()

    # --- Mode 2 : Manche Principale ---

    def setup_principale_view(self):
        self.clear_control_area()
        self.lbl_status.config(text="Manche : Principale")

        frame = tk.Frame(self.control_area, bg="#0B1325")
        frame.pack(fill=tk.X, pady=5)

        # Proposer consonne
        f_c = tk.LabelFrame(frame, text="Proposer une Consonne (+100 € par lettre)", fg="#FFD700", bg="#0B1325", font=("Helvetica", 10, "bold"), padx=10, pady=5)
        f_c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.ent_cons = tk.Entry(f_c, font=("Helvetica", 14), width=4, justify="center")
        self.ent_cons.pack(side=tk.LEFT, padx=5)
        self.ent_cons.bind("<Return>", lambda e: self.play_consonne())
        tk.Button(f_c, text="Valider", bg="#1976D2", fg="white", font=("Helvetica", 10, "bold"), command=self.play_consonne).pack(side=tk.LEFT, padx=5)

        # Acheter voyelle
        f_v = tk.LabelFrame(frame, text="Acheter une Voyelle (Coût fixe : 200 €)", fg="#FFD700", bg="#0B1325", font=("Helvetica", 10, "bold"), padx=10, pady=5)
        f_v.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.ent_voy = tk.Entry(f_v, font=("Helvetica", 14), width=4, justify="center")
        self.ent_voy.pack(side=tk.LEFT, padx=5)
        self.ent_voy.bind("<Return>", lambda e: self.buy_voyelle())
        tk.Button(f_v, text="Acheter", bg="#E64A19", fg="white", font=("Helvetica", 10, "bold"), command=self.buy_voyelle).pack(side=tk.LEFT, padx=5)

        # Résolution
        f_res = tk.Frame(self.control_area, bg="#0B1325", pady=10)
        f_res.pack(fill=tk.X)

        tk.Label(f_res, text="Proposer la solution :", fg="#FFFFFF", bg="#0B1325", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.ent_sol = tk.Entry(f_res, font=("Helvetica", 14), width=35)
        self.ent_sol.pack(side=tk.LEFT, padx=5)
        self.ent_sol.bind("<Return>", lambda e: self.resolve_principale())

        tk.Button(f_res, text="Résoudre", bg="#388E3C", fg="white", font=("Helvetica", 11, "bold"), command=self.resolve_principale).pack(side=tk.LEFT, padx=10)
        tk.Button(f_res, text="Passer", bg="#757575", fg="white", font=("Helvetica", 11), command=self.next_enigme).pack(side=tk.RIGHT, padx=5)

        # Lettres déjà jouées
        self.lbl_played = tk.Label(self.control_area, text="Lettres proposées : Aucune", font=("Helvetica", 11), fg="#B0BEC5", bg="#0B1325")
        self.lbl_played.pack(pady=5)

    def update_played_label(self):
        if hasattr(self, "lbl_played"):
            played = ", ".join(sorted(self.revealed_letters)) if self.revealed_letters else "Aucune"
            self.lbl_played.config(text=f"Lettres trouvées : {played}")

    def play_consonne(self):
        raw = strip_accents(self.ent_cons.get())
        self.ent_cons.delete(0, tk.END)
        if len(raw) != 1 or raw not in CONSONNES:
            messagebox.showwarning("Attention", "Veuillez entrer une seule consonne valide.")
            return

        if raw in self.revealed_letters:
            messagebox.showinfo("Information", f"La consonne '{raw}' a déjà été trouvée.")
            return

        count = self.current_enigme["solution_clean"].count(raw)
        if count > 0:
            self.revealed_letters.add(raw)
            gain = 100 * count
            self.cagnotte += gain
            self.render_board()
            self.update_stats()
            self.update_played_label()
            messagebox.showinfo("Bravo", f"Il y a {count} fois la lettre {raw} (+{gain} €)")
        else:
            self.lives -= 1
            self.update_stats()
            messagebox.showerror("Erreur", f"Pas de lettre {raw} ! Vous perdez 1 vie.")
            if self.lives <= 0:
                self.game_over()

    def buy_voyelle(self):
        raw = strip_accents(self.ent_voy.get())
        self.ent_voy.delete(0, tk.END)
        if len(raw) != 1 or raw not in VOYELLES:
            messagebox.showwarning("Attention", "Veuillez entrer une seule voyelle valide.")
            return

        if self.cagnotte < 200:
            messagebox.showerror("Fonds insuffisants", "Il vous faut au moins 200 € pour acheter une voyelle.")
            return

        if raw in self.revealed_letters:
            messagebox.showinfo("Information", f"La voyelle '{raw}' a déjà été achetée.")
            return

        self.cagnotte -= 200
        count = self.current_enigme["solution_clean"].count(raw)
        if count > 0:
            self.revealed_letters.add(raw)
            self.render_board()
            self.update_stats()
            self.update_played_label()
            messagebox.showinfo("Voyelle achetée", f"Il y a {count} fois la voyelle {raw} (-200 €).")
        else:
            self.update_stats()
            messagebox.showinfo("Voyelle absente", f"Aucune lettre {raw} présente (-200 €).")

    def resolve_principale(self):
        prop = strip_accents(self.ent_sol.get())
        if not prop:
            return
        if prop == self.current_enigme["solution_clean"]:
            messagebox.showinfo("Victoire !", f"Manche remportée ! La réponse était : {self.current_enigme['solution_display']}")
            self.next_enigme()
        else:
            self.lives -= 1
            self.update_stats()
            messagebox.showerror("Erreur", f"Mauvaise réponse. Vous perdez 1 vie.")
            if self.lives <= 0:
                self.game_over()

    # --- Mode 3 : Finale ---

    def setup_finale_view(self):
        self.clear_control_area()
        self.lbl_status.config(text="Manche : La Finale")

        # Révélation automatique de R, S, T, N, L, E
        base_letters = set("RSTNLE")
        self.revealed_letters = set(c for c in base_letters if c in self.current_enigme["solution_clean"])

        frame = tk.Frame(self.control_area, bg="#0B1325")
        frame.pack(fill=tk.X, pady=5)

        tk.Label(frame, text="Lettres de base révélées : R, S, T, L, N, E", fg="#00E5FF", bg="#0B1325", font=("Helvetica", 12, "bold")).pack(pady=5)
        tk.Label(frame, text="Proposez 3 consonnes et 1 voyelle :", fg="#FFFFFF", bg="#0B1325", font=("Helvetica", 11)).pack(pady=2)

        input_frame = tk.Frame(frame, bg="#0B1325")
        input_frame.pack(pady=5)

        tk.Label(input_frame, text="3 Consonnes :", fg="#FFFFFF", bg="#0B1325").grid(row=0, column=0, padx=5)
        self.ent_c1 = tk.Entry(input_frame, width=3, font=("Helvetica", 12), justify="center")
        self.ent_c1.grid(row=0, column=1, padx=2)
        self.ent_c2 = tk.Entry(input_frame, width=3, font=("Helvetica", 12), justify="center")
        self.ent_c2.grid(row=0, column=2, padx=2)
        self.ent_c3 = tk.Entry(input_frame, width=3, font=("Helvetica", 12), justify="center")
        self.ent_c3.grid(row=0, column=3, padx=2)

        tk.Label(input_frame, text="1 Voyelle :", fg="#FFFFFF", bg="#0B1325").grid(row=0, column=4, padx=10)
        self.ent_v = tk.Entry(input_frame, width=3, font=("Helvetica", 12), justify="center")
        self.ent_v.grid(row=0, column=5, padx=2)

        self.btn_apply_letters = tk.Button(input_frame, text="Révéler les lettres", bg="#FFA000", font=("Helvetica", 10, "bold"), command=self.apply_finale_letters)
        self.btn_apply_letters.grid(row=0, column=6, padx=15)

        # Résolution finale
        res_frame = tk.Frame(self.control_area, bg="#0B1325", pady=10)
        res_frame.pack(fill=tk.X)

        tk.Label(res_frame, text="Votre proposition :", fg="#FFFFFF", bg="#0B1325", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=5)
        self.ent_sol = tk.Entry(res_frame, font=("Helvetica", 14), width=25)
        self.ent_sol.pack(side=tk.LEFT, padx=5)
        self.ent_sol.bind("<Return>", lambda e: self.check_finale())

        tk.Button(res_frame, text="Valider la finale", bg="#4CAF50", fg="white", font=("Helvetica", 11, "bold"), command=self.check_finale).pack(side=tk.LEFT, padx=10)
        tk.Button(res_frame, text="Passer", bg="#757575", fg="white", font=("Helvetica", 11), command=self.next_enigme).pack(side=tk.RIGHT, padx=5)

    def apply_finale_letters(self):
        c1 = strip_accents(self.ent_c1.get())
        c2 = strip_accents(self.ent_c2.get())
        c3 = strip_accents(self.ent_c3.get())
        v = strip_accents(self.ent_v.get())

        chosen_c = [c1, c2, c3]
        if not all(len(c) == 1 and c in CONSONNES for c in chosen_c) or len(set(chosen_c)) != 3:
            messagebox.showwarning("Saisie", "Veuillez entrer 3 consonnes distinctes et valides.")
            return

        if len(v) != 1 or v not in VOYELLES:
            messagebox.showwarning("Saisie", "Veuillez entrer une voyelle valide.")
            return

        for char in chosen_c + [v]:
            if char in self.current_enigme["solution_clean"]:
                self.revealed_letters.add(char)

        self.btn_apply_letters.config(state=tk.DISABLED)
        self.render_board()

    def check_finale(self):
        prop = strip_accents(self.ent_sol.get())
        if not prop:
            return
        if prop == self.current_enigme["solution_clean"]:
            messagebox.showinfo("Gagné !", f"Exceptionnel ! Vous remportez la finale !\nSolution : {self.current_enigme['solution_display']}")
        else:
            messagebox.showerror("Perdu", f"Dommage ! La solution était : {self.current_enigme['solution_display']}")
        self.next_enigme()

    # --- Gestion Fin de partie ---

    def game_over(self):
        self.stop_timer()
        messagebox.showerror("Fin de partie", f"Vous n'avez plus de vies.\nLa solution était : {self.current_enigme['solution_display']}")
        self.show_menu()


if __name__ == "__main__":
    app = RoueDeLaFortuneApp()
    app.mainloop()