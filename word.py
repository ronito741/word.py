#!/usr/bin/env python3
"""
Advanced Penetration Testing Wordlist Generator with GUI
Description: This script provides a graphical interface to generate custom, 
high-probability password dictionaries by applying leet speak, number ranges, 
and customizable symbol injection positions to base seed words, complete with an enhanced realtime preview and live count estimator.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import re

# =====================================================================
# 1. CORE MUTATION & TRANSFORMATION LOGIC
# =====================================================================

# Standard Leet Speak substitution map used to replace letters with visual lookalikes
LEET_MAP = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '$', 't': '7'}

def leet_speak(word):
    """
    Description: Converts standard alphabetical characters into leet speak 
    equivalents (e.g., 'admin' becomes '4dm1n').
    """
    return "".join(LEET_MAP.get(c.lower(), c) for c in word)

def generate_mutations(word, range_tuple, symbols_str="!@#$", 
                       inject_symbols=True, 
                       sym_suffix=True, sym_prefix=False, sym_middle=False,
                       pos_suffix=True, pos_prefix=True, pos_middle=True):
    """
    Description: Takes a single base word and applies all enabled mutation rules, 
    number range positions, and symbol injection positions.
    """
    word = word.strip()
    if not word:
        return []

    # Step 1: Establish foundational base mutations of the word
    raw_bases = [
        word,                 # Original case
        word.lower(),         # All lowercase
        word.upper(),         # All uppercase
        word.capitalize(),    # Capitalized first letter
        word[::-1],           # Reversed string
        leet_speak(word),     # Leet speak variant
        leet_speak(word).capitalize() # Capitalized leet variant
    ]
    
    # Filter out duplicate base forms to optimize processing
    unique_bases = []
    seen_bases = set()
    for b in raw_bases:
        if b not in seen_bases:
            seen_bases.add(b)
            unique_bases.append(b)

    # Step 2: Build core variations (base words + number range combinations)
    core_variations = []
    for form in unique_bases:
        core_variations.append(form)
        length = len(form)
        
        if range_tuple:
            start, end = range_tuple
            for num in range(start, end + 1):
                num_str = str(num)
                
                # Position 1: Suffix (e.g., word123)
                if pos_suffix:
                    core_variations.append(f"{form}{num_str}")
                
                # Position 2: Prefix (e.g., 123word)
                if pos_prefix:
                    core_variations.append(f"{num_str}{form}")
                
                # Position 3: Middle (e.g., wo123rd)
                if pos_middle and length > 1:
                    for i in range(1, length):
                        core_variations.append(f"{form[:i]}{num_str}{form[i:]}")

    # Step 3: Apply symbol injections across selected symbol positions
    mutations = []
    seen = set()

    def add_mut(m):
        """Helper function to ensure generated mutations are unique."""
        if m not in seen:
            seen.add(m)
            mutations.append(m)

    symbols = list(symbols_str) if (inject_symbols and symbols_str) else [""]

    for item in core_variations:
        add_mut(item)
        
        if inject_symbols and symbols_str:
            item_len = len(item)
            for sym in symbols:
                # Symbol Position 1: Suffix (e.g., word!)
                if sym_suffix:
                    add_mut(f"{item}{sym}")
                
                # Symbol Position 2: Prefix (e.g., !word)
                if sym_prefix:
                    add_mut(f"{sym}{item}")
                
                # Symbol Position 3: Middle (e.g., wo!rd)
                if sym_middle and item_len > 1:
                    for i in range(1, item_len):
                        add_mut(f"{item[:i]}{sym}{item[i:]}")

    return mutations


# =====================================================================
# 2. USER INTERFACE (GUI) APPLICATION CLASS
# =====================================================================

class WordlistApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Wordlist Generator")
        self.root.geometry("720x960")
        self.root.resizable(False, False)

        # Apply a polished Dark Tech theme styling
        self.setup_styles()
        self.create_widgets()
        self.update_preview() # Initial preview population

    def setup_styles(self):
        """Description: Configures a modern, dark cybersecurity-themed color palette using ttk Style."""
        self.BG_DARK = "#181824"
        self.BG_CARD = "#212130"
        self.FG_TEXT = "#e2e8f0"
        self.FG_MUTED = "#94a3b8"
        self.ACCENT = "#00bcd4" # Cyan / Teal highlight
        self.INPUT_BG = "#2a2a3d"

        self.root.configure(bg=self.BG_DARK)

        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Global styles
        self.style.configure(".", background=self.BG_DARK, foreground=self.FG_TEXT, font=("Segoe UI", 10))
        self.style.configure("TLabel", background=self.BG_DARK, foreground=self.FG_TEXT)
        self.style.configure("TCheckbutton", background=self.BG_DARK, foreground=self.FG_TEXT, focuscolor="")
        self.style.map("TCheckbutton", background=[('active', self.BG_DARK)], foreground=[('active', self.ACCENT)])

        # LabelFrame styling
        self.style.configure("TLabelframe", background=self.BG_DARK, bordercolor="#3b3b54", borderwidth=1)
        self.style.configure("TLabelframe.Label", background=self.BG_DARK, foreground=self.ACCENT, font=("Segoe UI", 10, "bold"))

        # Entry styling
        self.style.configure("TEntry", fieldbackground=self.INPUT_BG, foreground=self.FG_TEXT, insertcolor=self.FG_TEXT, bordercolor="#3b3b54")

        # Standard Button styling
        self.style.configure("TButton", background="#313147", foreground=self.FG_TEXT, bordercolor="#454566", focusthickness=0, font=("Segoe UI", 9, "bold"))
        self.style.map("TButton", background=[('active', '#3f3f5e'), ('pressed', '#272738')])

        # Accent Action Button styling
        self.style.configure("Accent.TButton", background=self.ACCENT, foreground="#12121a", bordercolor=self.ACCENT, font=("Segoe UI", 10, "bold"))
        self.style.map("Accent.TButton", background=[('active', '#26c6da'), ('pressed', '#00838f')], foreground=[('active', '#12121a')])

    def create_widgets(self):
        """Description: Builds and lays out all interface sections, inputs, options, and live preview with modern dark styling."""
        main_frame = ttk.Frame(self.root, padding="12")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="🛡️ PENETRATION TESTING WORDLIST MUTATOR 🛡️", font=("Segoe UI", 13, "bold"), foreground=self.ACCENT)
        title_label.pack(pady=(0, 6))

        # ==================== SECTION 1: SOURCES & OUTPUT ====================
        source_frame = ttk.LabelFrame(main_frame, text=" 📂 1. Base Words Source & Output ", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 6))

        desc_lbl1 = ttk.Label(source_frame, text="💡 Enter seed words manually or select a .txt file. Output will combine all rules.", font=("Segoe UI", 8, "italic"), foreground=self.FG_MUTED)
        desc_lbl1.pack(anchor="w", pady=(0, 4))

        ttk.Label(source_frame, text="✍ Type or paste base words below (one per line):", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 2))
        
        self.words_text = tk.Text(source_frame, height=3, width=72, font=("Consolas", 10), bg=self.INPUT_BG, fg=self.FG_TEXT, insertbackground=self.FG_TEXT, relief="flat", highlightthickness=1, highlightbackground="#3b3b54", highlightcolor=self.ACCENT)
        self.words_text.pack(fill=tk.X, pady=(0, 6))
        self.words_text.insert(tk.END, "admin\nronni\nroot")
        self.words_text.bind("<KeyRelease>", self.update_preview)

        file_row = ttk.Frame(source_frame)
        file_row.pack(fill=tk.X, pady=(2, 3))
        ttk.Label(file_row, text="📁 Select file:").pack(side=tk.LEFT, padx=(0, 8))
        self.input_entry = ttk.Entry(file_row, width=46)
        self.input_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(file_row, text="Browse", command=self.browse_input, width=10).pack(side=tk.RIGHT)

        out_row = ttk.Frame(source_frame)
        out_row.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(out_row, text="💾 Save path:").pack(side=tk.LEFT, padx=(0, 8))
        self.output_entry = ttk.Entry(out_row, width=46)
        self.output_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(out_row, text="Browse", command=self.browse_output, width=10).pack(side=tk.RIGHT)

        # ==================== SECTION 2: NUMBERS & RANGES ====================
        num_frame = ttk.LabelFrame(main_frame, text=" 🔢 2. Numbers & Ranges Category ", padding="10")
        num_frame.pack(fill=tk.X, pady=(0, 6))

        desc_lbl2 = ttk.Label(num_frame, text="💡 Configure numeric sequences and positioning.", font=("Segoe UI", 8, "italic"), foreground=self.FG_MUTED)
        desc_lbl2.pack(anchor="w", pady=(0, 4))

        num_row1 = ttk.Frame(num_frame)
        num_row1.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(num_row1, text="📊 Range:").pack(side=tk.LEFT, padx=(0, 8))
        self.range_entry = ttk.Entry(num_row1, width=12)
        self.range_entry.insert(0, "0-99")
        self.range_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.range_entry.bind("<KeyRelease>", self.update_preview)
        ttk.Label(num_row1, text="(e.g., 0-9999, leave blank to skip)", font=("Segoe UI", 8), foreground=self.FG_MUTED).pack(side=tk.LEFT, padx=5)

        loc_row = ttk.Frame(num_frame)
        loc_row.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(loc_row, text="📍 Positions:", font=("Segoe UI", 9, "bold"), foreground=self.ACCENT).pack(side=tk.LEFT, padx=(0, 10))
        self.pos_suffix_var = tk.BooleanVar(value=True)
        self.pos_prefix_var = tk.BooleanVar(value=True)
        self.pos_middle_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(loc_row, text="📌 Suffix", variable=self.pos_suffix_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(loc_row, text="📍 Prefix", variable=self.pos_prefix_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(loc_row, text="↔️ Middle", variable=self.pos_middle_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)

        # ==================== SECTION 3: SYMBOLS CATEGORY ====================
        sym_frame = ttk.LabelFrame(main_frame, text=" 🔣 3. Symbols Category ", padding="10")
        sym_frame.pack(fill=tk.X, pady=(0, 6))

        desc_lbl3 = ttk.Label(sym_frame, text="💡 Configure symbol injection and positioning checkboxes.", font=("Segoe UI", 8, "italic"), foreground=self.FG_MUTED)
        desc_lbl3.pack(anchor="w", pady=(0, 4))

        sym_row1 = ttk.Frame(sym_frame)
        sym_row1.pack(fill=tk.X, pady=(0, 4))
        self.sym_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sym_row1, text="🔣 Inject Symbols", variable=self.sym_var, command=self.update_preview).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(sym_row1, text="🔤 Set:").pack(side=tk.LEFT, padx=(0, 5))
        self.symbols_entry = ttk.Entry(sym_row1, width=15)
        self.symbols_entry.insert(0, "!@#$")
        self.symbols_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.symbols_entry.bind("<KeyRelease>", self.update_preview)
        ttk.Label(sym_row1, text="(Chars used)", font=("Segoe UI", 8), foreground=self.FG_MUTED).pack(side=tk.LEFT)

        sym_loc_row = ttk.Frame(sym_frame)
        sym_loc_row.pack(fill=tk.X, pady=(2, 0))
        ttk.Label(sym_loc_row, text="📍 Positions:", font=("Segoe UI", 9, "bold"), foreground=self.ACCENT).pack(side=tk.LEFT, padx=(0, 10))
        self.sym_suffix_var = tk.BooleanVar(value=True)
        self.sym_prefix_var = tk.BooleanVar(value=False)
        self.sym_middle_var = tk.BooleanVar(value=False)

        ttk.Checkbutton(sym_loc_row, text="📌 Suffix", variable=self.sym_suffix_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(sym_loc_row, text="📍 Prefix", variable=self.sym_prefix_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(sym_loc_row, text="↔️ Middle", variable=self.sym_middle_var, command=self.update_preview).pack(side=tk.LEFT, padx=6)

        # ==================== SECTION 4: REALTIME PREVIEW ====================
        preview_frame = ttk.LabelFrame(main_frame, text=" 👁️ 4. Realtime Preview & Live Estimator ", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 6))

        preview_header_row = ttk.Frame(preview_frame)
        preview_header_row.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(preview_header_row, text="💡 Live Sample Output:", font=("Segoe UI", 8, "italic"), foreground=self.FG_MUTED).pack(side=tk.LEFT)
        
        # Live counter badge
        self.preview_count_label = ttk.Label(preview_header_row, text="⚡ Estimated Total: 0 variations", font=("Segoe UI", 9, "bold"), foreground=self.ACCENT)
        self.preview_count_label.pack(side=tk.RIGHT)

        self.preview_text = tk.Text(preview_frame, height=5, width=72, font=("Consolas", 9), bg=self.INPUT_BG, fg=self.ACCENT, insertbackground=self.FG_TEXT, state=tk.DISABLED, relief="flat", highlightthickness=1, highlightbackground="#3b3b54")
        self.preview_text.pack(fill=tk.X, pady=(0, 2))

        # ==================== SECTION 5: ACTION & STATUS ====================
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=(6, 0))

        self.generate_btn = ttk.Button(action_frame, text="🚀 GENERATE WORDLIST", style="Accent.TButton", command=self.start_generation_thread)
        self.generate_btn.pack(fill=tk.X, ipady=8, pady=(0, 4))

        self.status_label = ttk.Label(action_frame, text="📊 Status: Ready", font=("Segoe UI", 9, "italic"), foreground=self.FG_MUTED)
        self.status_label.pack(anchor="center")

    # ==================== GUI EVENT HANDLERS & PREVIEW LOGIC ====================

    def update_preview(self, event=None):
        """Description: Dynamically calculates total variations and displays sample preview live as inputs change."""
        try:
            manual_words = self.words_text.get("1.0", tk.END).strip()
            words = [line.strip() for line in manual_words.splitlines() if line.strip()]
            if not words:
                words = ["admin"]

            range_str = self.range_entry.get().strip()
            range_tuple = None
            if range_str:
                parts = range_str.split("-")
                if len(parts) == 2:
                    range_tuple = (int(parts[0].strip()), int(parts[1].strip()))

            symbols_str = self.symbols_entry.get()
            inject_symbols = self.sym_var.get()
            sym_suffix = self.sym_suffix_var.get()
            sym_prefix = self.sym_prefix_var.get()
            sym_middle = self.sym_middle_var.get()
            pos_suffix = self.pos_suffix_var.get()
            pos_prefix = self.pos_prefix_var.get()
            pos_middle = self.pos_middle_var.get()

            # Generate full set for accurate count and preview sample
            full_preview_list = []
            for word in words:
                muts = generate_mutations(word, range_tuple, symbols_str, 
                                          inject_symbols, sym_suffix, sym_prefix, sym_middle,
                                          pos_suffix, pos_prefix, pos_middle)
                full_preview_list.extend(muts)

            # Deduplicate total items for live count
            seen = set()
            unique_preview = []
            for item in full_preview_list:
                if item not in seen:
                    seen.add(item)
                    unique_preview.append(item)

            total_estimated = len(unique_preview)
            self.preview_count_label.config(text=f"⚡ Estimated Total: {total_estimated:,} variations")

            # Take top 40 for preview box display
            display_sample = unique_preview[:40]

            self.preview_text.config(state=tk.NORMAL)
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, "\n".join(display_sample))
            self.preview_text.config(state=tk.DISABLED)
        except Exception:
            self.preview_count_label.config(text="⚡ Estimated Total: Check range format")

    def browse_input(self):
        """Description: Opens a file dialog to select an input text file of base words."""
        filename = filedialog.askopenfilename(title="Select Base Words File", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            self.words_text.delete("1.0", tk.END)
            self.update_preview()

    def browse_output(self):
        """Description: Opens a save dialog to choose the output destination file path."""
        filename = filedialog.asksaveasfilename(title="Save Wordlist As", defaultextension=".txt", filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def start_generation_thread(self):
        """Description: Validates user input and starts the generation task in a background thread."""
        manual_words = self.words_text.get("1.0", tk.END).strip()
        input_file = self.input_entry.get().strip()
        output_path = self.output_entry.get().strip()

        if not manual_words and not input_file:
            messagebox.showerror("Error", "Please either type words in the text box or select an input file.")
            return
        if not output_path:
            messagebox.showerror("Error", "Please specify a valid output file path.")
            return

        range_str = self.range_entry.get().strip()
        range_tuple = None
        if range_str:
            try:
                parts = range_str.split("-")
                if len(parts) != 2:
                    raise ValueError
                range_tuple = (int(parts[0].strip()), int(parts[1].strip()))
            except ValueError:
                messagebox.showerror("Error", "Range must be in format START-END (e.g., 0-9999).")
                return

        symbols_str = self.symbols_entry.get()
        inject_symbols = self.sym_var.get()
        sym_suffix = self.sym_suffix_var.get()
        sym_prefix = self.sym_prefix_var.get()
        sym_middle = self.sym_middle_var.get()
        pos_suffix = self.pos_suffix_var.get()
        pos_prefix = self.pos_prefix_var.get()
        pos_middle = self.pos_middle_var.get()

        self.generate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="📊 Status: Generating wordlist...", foreground="#00bcd4")

        threading.Thread(target=self.run_generation, args=(
            manual_words, input_file, output_path, range_tuple, 
            symbols_str, inject_symbols, sym_suffix, sym_prefix, sym_middle,
            pos_suffix, pos_prefix, pos_middle
        ), daemon=True).start()

    def run_generation(self, manual_words, input_file, output_path, range_tuple, 
                       symbols_str, inject_symbols, sym_suffix, sym_prefix, sym_middle,
                       pos_suffix, pos_prefix, pos_middle):
        """Description: Core background worker that processes words, removes duplicates, and saves output."""
        try:
            words = []
            if manual_words:
                words = [line.strip() for line in manual_words.splitlines() if line.strip()]
            elif input_file:
                with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
                    words = [line.strip() for line in f.readlines() if line.strip()]

            final_list = []
            for word in words:
                muts = generate_mutations(word, range_tuple, symbols_str, 
                                          inject_symbols, sym_suffix, sym_prefix, sym_middle,
                                          pos_suffix, pos_prefix, pos_middle)
                final_list.extend(muts)

            # Deduplicate the list
            seen_final = set()
            unique_final_list = []
            for item in final_list:
                if item not in seen_final:
                    seen_final.add(item)
                    unique_final_list.append(item)

            with open(output_path, 'w', encoding='utf-8') as f:
                for m in unique_final_list:
                    f.write(m + '\n')

            total_count = len(unique_final_list)
            self.root.after(0, lambda: self.generation_complete(output_path, total_count))
        except Exception as e:
            self.root.after(0, lambda: self.generation_error(str(e)))

    def generation_complete(self, output_path, count):
        """Description: Updates status when generation finishes successfully."""
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="📊 Status: Complete!", foreground="#4ade80")
        messagebox.showinfo("Success", f"Successfully generated {count:,} variations!\nSaved to:\n{output_path}")

    def generation_error(self, err_msg):
        """Description: Handles errors during generation and re-enables the UI."""
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="📊 Status: Error encountered", foreground="#f87171")
        messagebox.showerror("Execution Error", f"An error occurred:\n{err_msg}")

# =====================================================================
# 3. APPLICATION ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = WordlistApp(root)
    root.mainloop()
