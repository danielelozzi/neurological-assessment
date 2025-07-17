import tkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import sys
import webbrowser
import traceback

# Importa le funzioni main dagli altri script
import trim_video
import detect_and_save_ball
import generate_report

class StdoutRedirector:
    """Redirige l'output della console a un widget Text di tkinter."""
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tkinter.END, string)
        self.text_widget.see(tkinter.END)
        self.text_widget.configure(state="disabled")

    def flush(self):
        pass

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CONFIGURAZIONE FINESTRA ---
        self.title("LabSCoC - Strumento di Analisi CNA")
        self.geometry("800x950")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- VARIABILI DI STATO ---
        self.input_dir = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.yolo_model_path = ctk.StringVar()
        self.detection_method = ctk.StringVar(value="YOLO")
        self.run_fragmentation_analysis = ctk.BooleanVar(value=False)
        self.run_excursion_analysis = ctk.BooleanVar(value=False)

        # --- HEADER E BRANDING ---
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(header_frame, text="Strumento di Analisi Neuro-Visuale", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        lab_link = ctk.CTkLabel(header_frame, text="LabSCoC - Laboratorio di Scienze Cognitive e del Comportamento e Dr. Daniele Lozzi", text_color="#5DADE2", cursor="hand2")
        lab_link.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")
        lab_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://labscoc.wordpress.com/"))
        github_link = ctk.CTkLabel(header_frame, text="Pagina GitHub del Progetto", text_color="#5DADE2", cursor="hand2")
        github_link.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/danielelozzi/neurological-assessment"))

        # --- FRAME PRINCIPALE DEI CONTROLLI ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        # Input / Output
        ctk.CTkLabel(main_frame, text="1. Cartella Input (Dati Pupil Cloud):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(main_frame, textvariable=self.input_dir, text_color="gray").grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_input_dir).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="2. Cartella Output:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkLabel(main_frame, textvariable=self.output_dir, text_color="gray").grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_output_dir).grid(row=1, column=2, padx=10, pady=10)

        # Detection Method
        ctk.CTkLabel(main_frame, text="3. Metodo Rilevamento Palla:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkSegmentedButton(main_frame, values=["YOLO", "Hough Circle"], variable=self.detection_method, command=self.toggle_yolo_path).grid(row=2, column=1, columnspan=2, padx=10, pady=10, sticky="w")
        
        # YOLO Model Path
        self.yolo_label = ctk.CTkLabel(main_frame, text="4. Modello YOLO (.pt):")
        self.yolo_path_label = ctk.CTkLabel(main_frame, textvariable=self.yolo_model_path, text_color="gray")
        self.yolo_button = ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_yolo_model)
        self.yolo_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.yolo_path_label.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
        self.yolo_button.grid(row=3, column=2, padx=10, pady=10)

        # --- ANALISI AGGIUNTIVE ---
        ctk.CTkLabel(main_frame, text="5. Analisi Aggiuntive:").grid(row=4, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkCheckBox(main_frame, text="Genera grafici 'Frammentazione' (distanza sguardi)", variable=self.run_fragmentation_analysis, onvalue=True, offvalue=False).grid(row=4, column=1, columnspan=2, padx=10, pady=10, sticky="w")
        ctk.CTkCheckBox(main_frame, text="Calcola metrica 'Escursione' (completamento traiettoria)", variable=self.run_excursion_analysis, onvalue=True, offvalue=False).grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        # --- CONSOLE E PULSANTE AVVIO ---
        console_frame = ctk.CTkFrame(self); console_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        console_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(console_frame, text="Log di Analisi:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.console = ctk.CTkTextbox(console_frame, height=200, state="disabled"); self.console.pack(fill="x", expand=True, padx=10, pady=10)
        sys.stdout = StdoutRedirector(self.console); sys.stderr = StdoutRedirector(self.console)
        self.run_button = ctk.CTkButton(self, text="Avvia Analisi Completa", command=self.start_analysis_thread, height=40, font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.run_button.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.check_inputs()

    def select_input_dir(self):
        path = filedialog.askdirectory(title="Seleziona cartella input")
        if path: self.input_dir.set(path)
        self.check_inputs()
    def select_output_dir(self):
        path = filedialog.askdirectory(title="Seleziona cartella output")
        if path: self.output_dir.set(path)
        self.check_inputs()
    def select_yolo_model(self):
        path = filedialog.askopenfilename(title="Seleziona modello YOLO", filetypes=[("YOLO Model", "*.pt")])
        if path: self.yolo_model_path.set(path)
        self.check_inputs()
            
    def toggle_yolo_path(self, value):
        if value == "YOLO": self.yolo_label.grid(); self.yolo_path_label.grid(); self.yolo_button.grid()
        else: self.yolo_label.grid_remove(); self.yolo_path_label.grid_remove(); self.yolo_button.grid_remove()
        self.check_inputs()

    def check_inputs(self):
        input_ok = os.path.isdir(self.input_dir.get())
        output_ok = os.path.isdir(self.output_dir.get())
        yolo_ok = (self.detection_method.get() != "YOLO") or os.path.isfile(self.yolo_model_path.get())
        self.run_button.configure(state="normal" if input_ok and output_ok and yolo_ok else "disabled")

    def start_analysis_thread(self):
        self.run_button.configure(state="disabled")
        self.console.configure(state="normal")
        self.console.delete("1.0", tkinter.END)
        self.console.configure(state="disabled")
        threading.Thread(target=self.run_full_analysis, daemon=True).start()

    def run_full_analysis(self):
        """Orchestra l'esecuzione sequenziale degli script di analisi in un thread separato."""
        success = False
        error_message = ""
        try:
            print("--- ANALISI AVVIATA ---\n")
            
            args_trim = type('Args', (), {'input_video': os.path.join(self.input_dir.get(), 'video.mp4'), 'output_dir': self.output_dir.get()})
            trim_video.main(args_trim)
            
            args_detect = type('Args', (), {'input_dir': self.input_dir.get(), 'output_dir': self.output_dir.get(), 'use_yolo': (self.detection_method.get() == "YOLO"), 'yolo_model': self.yolo_model_path.get()})
            detect_and_save_ball.main(args_detect)

            args_report = type('Args', (), {
                'analysis_dir': self.output_dir.get(), 
                'output_dir': self.output_dir.get(), 
                'input_dir_for_pupil': self.input_dir.get(), 
                'run_fragmentation_analysis': self.run_fragmentation_analysis.get(), 
                'run_excursion_analysis': self.run_excursion_analysis.get()
            })
            generate_report.main(args_report)
            
            print("\n====== ANALISI COMPLETATA CON SUCCESSO ======")
            success = True

        except Exception as e:
            error_message = str(e)
            print(f"\n====== ERRORE DURANTE L'ANALISI ======\n{e}")
            traceback.print_exc()
        finally:
            # --- MODIFICA ---
            # Chiama la funzione di finalizzazione nel thread principale della GUI
            self.after(0, self.analysis_finished, success, error_message)

    # --- NUOVA FUNZIONE ---
    def analysis_finished(self, success, error_message):
        """
        Viene eseguito nel thread principale della GUI al termine dell'analisi.
        Riabilita il pulsante e mostra un messaggio di completamento o errore.
        """
        self.run_button.configure(state="normal")
        if success:
            messagebox.showinfo(
                "Analisi Completata",
                f"L'analisi è terminata con successo.\n\nI risultati sono stati salvati in:\n{self.output_dir.get()}"
            )
        else:
            messagebox.showerror(
                "Errore di Analisi",
                "Si è verificato un errore durante l'analisi.\n\n"
                f"Dettagli: {error_message}\n\n"
                "Controllare il log nella finestra principale per ulteriori informazioni."
            )
            
if __name__ == "__main__":
    MainApp().mainloop()
