# main_gui.py
import tkinter
import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import sys
import webbrowser

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
        self.title("LabSCoC - Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)")
        self.geometry("800x850") # Aumentata l'altezza per il nuovo testo
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- VARIABILI DI STATO ---
        self.input_dir = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.yolo_model_path = ctk.StringVar()
        self.detection_method = ctk.StringVar(value="YOLO")

        # --- HEADER E BRANDING ---
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(header_frame, text="Strumento di Analisi Neuro-Visuale", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        
        lab_link = ctk.CTkLabel(header_frame, text="LabSCoC - Laboratorio di Scienze Cognitive e del Comportamento", text_color="#5DADE2", cursor="hand2")
        lab_link.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="w")
        lab_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://labscoc.wordpress.com/"))

        github_link = ctk.CTkLabel(header_frame, text="Pagina GitHub del Progetto", text_color="#5DADE2", cursor="hand2")
        github_link.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="w")
        github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/danielelozzi/neurological-assessment"))


        # --- FRAME PRINCIPALE DEI CONTROLLI ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        # Input Directory
        ctk.CTkLabel(main_frame, text="1. Cartella Input (Dati Pupil Lab Neon con April Tag Mark Mapper):").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.input_dir_label = ctk.CTkLabel(main_frame, textvariable=self.input_dir, text_color="gray")
        self.input_dir_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_input_dir).grid(row=0, column=2, padx=10, pady=10)

        # --- NUOVA SEZIONE: DESCRIZIONE FILE INPUT ---
        input_info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        input_info_frame.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="ew")
        
        info_text = (
            "La cartella deve contenere i seguenti file scaricati da Pupil Cloud (dopo l'enrichment 'Marker Mapper'):\n"
            "• video.mp4: La registrazione video della scena.\n"
            "• gaze.csv: I dati grezzi dello sguardo.\n"
            "• world_timestamps.csv: I timestamp per la sincronizzazione video-sguardo.\n"
            "• surface_positions.csv: Le coordinate della superficie tracciata dagli AprilTag."
        )
        
        info_label = ctk.CTkLabel(input_info_frame, text=info_text, text_color="gray", justify="left", font=ctk.CTkFont(size=11))
        info_label.pack(anchor="w")
        # --- FINE NUOVA SEZIONE ---

        # Output Directory
        ctk.CTkLabel(main_frame, text="2. Cartella Output:").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.output_dir_label = ctk.CTkLabel(main_frame, textvariable=self.output_dir, text_color="gray")
        self.output_dir_label.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_output_dir).grid(row=2, column=2, padx=10, pady=10)

        # Detection Method
        ctk.CTkLabel(main_frame, text="3. Metodo di Rilevamento:").grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.segmented_button = ctk.CTkSegmentedButton(main_frame, values=["YOLO", "Hough Circle"], variable=self.detection_method, command=self.toggle_yolo_path)
        self.segmented_button.grid(row=3, column=1, columnspan=2, padx=10, pady=10, sticky="w")
        
        # YOLO Model Path (condizionale)
        self.yolo_label = ctk.CTkLabel(main_frame, text="4. Modello YOLO (.pt):")
        self.yolo_path_label = ctk.CTkLabel(main_frame, textvariable=self.yolo_model_path, text_color="gray")
        self.yolo_button = ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_yolo_model)
        
        self.yolo_label.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.yolo_path_label.grid(row=4, column=1, padx=10, pady=10, sticky="ew")
        self.yolo_button.grid(row=4, column=2, padx=10, pady=10)


        # --- CONSOLE DI OUTPUT ---
        console_frame = ctk.CTkFrame(self)
        console_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        console_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(console_frame, text="Log di Analisi:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(5,0))
        self.console = ctk.CTkTextbox(console_frame, height=200, state="disabled")
        self.console.pack(fill="x", expand=True, padx=10, pady=10)
        
        # Redirigi stdout e stderr
        sys.stdout = StdoutRedirector(self.console)
        sys.stderr = StdoutRedirector(self.console)


        # --- PULSANTE DI AVVIO ---
        self.run_button = ctk.CTkButton(self, text="Avvia Analisi Completa", command=self.start_analysis_thread, height=40, font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.run_button.grid(row=3, column=0, padx=20, pady=20, sticky="ew")
        
        self.check_inputs()

    def select_input_dir(self):
        path = filedialog.askdirectory(title="Seleziona la cartella contenente i dati di Tobii")
        if path:
            self.input_dir.set(path)
            self.check_inputs()

    def select_output_dir(self):
        path = filedialog.askdirectory(title="Seleziona la cartella dove salvare i risultati")
        if path:
            self.output_dir.set(path)
            self.check_inputs()

    def select_yolo_model(self):
        path = filedialog.askopenfilename(title="Seleziona il modello YOLO", filetypes=[("YOLO Model", "*.pt")])
        if path:
            self.yolo_model_path.set(path)
            self.check_inputs()
            
    def toggle_yolo_path(self, value):
        if value == "YOLO":
            self.yolo_label.grid()
            self.yolo_path_label.grid()
            self.yolo_button.grid()
        else:
            self.yolo_label.grid_remove()
            self.yolo_path_label.grid_remove()
            self.yolo_button.grid_remove()
        self.check_inputs()

    def check_inputs(self):
        """Abilita il pulsante di avvio solo se tutti gli input necessari sono presenti."""
        input_ok = os.path.isdir(self.input_dir.get())
        output_ok = os.path.isdir(self.output_dir.get())
        yolo_ok = (self.detection_method.get() == "Hough Circle") or \
                  (self.detection_method.get() == "YOLO" and os.path.isfile(self.yolo_model_path.get()))
        
        if input_ok and output_ok and yolo_ok:
            self.run_button.configure(state="normal")
        else:
            self.run_button.configure(state="disabled")

    def start_analysis_thread(self):
        """Avvia l'analisi in un thread separato per non bloccare la GUI."""
        self.run_button.configure(state="disabled")
        self.console.configure(state="normal")
        self.console.delete("1.0", tkinter.END)
        self.console.configure(state="disabled")
        
        thread = threading.Thread(target=self.run_full_analysis)
        thread.daemon = True
        thread.start()

    def run_full_analysis(self):
        """Orchestra l'esecuzione sequenziale degli script di analisi."""
        try:
            print("--- ANALISI AVVIATA ---\n")
            
            # --- FASE 1: TRIM VIDEO ---
            print("\n--- FASE 1: Taglio dei segmenti video ---\n")
            args_trim = type('Args', (), {})()
            args_trim.input_video = os.path.join(self.input_dir.get(), 'video.mp4')
            args_trim.output_dir = self.output_dir.get()
            trim_video.main(args_trim)
            print("\n--- FASE 1 COMPLETATA ---\n")
            
            # --- FASE 2: DETECT AND SAVE BALL ---
            print("\n--- FASE 2: Rilevamento palla e analisi sguardo ---\n")
            args_detect = type('Args', (), {})()
            args_detect.input_dir = self.input_dir.get()
            args_detect.output_dir = self.output_dir.get()
            args_detect.use_yolo = (self.detection_method.get() == "YOLO")
            args_detect.yolo_model = self.yolo_model_path.get()
            detect_and_save_ball.main(args_detect)
            print("\n--- FASE 2 COMPLETATA ---\n")

            # --- FASE 3: GENERATE REPORT ---
            print("\n--- FASE 3: Generazione report finale ---\n")
            args_report = type('Args', (), {})()
            args_report.analysis_dir = self.output_dir.get()
            args_report.output_dir = self.output_dir.get()
            generate_report.main(args_report)
            print("\n--- FASE 3 COMPLETATA ---\n")
            
            print("\n====== ANALISI COMPLETATA CON SUCCESSO ======")
            print(f"Tutti i file di output sono stati salvati in: {self.output_dir.get()}")

        except Exception as e:
            print(f"\n====== ERRORE DURANTE L'ANALISI ======")
            print(f"Si è verificato un errore: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.run_button.configure(state="normal")


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()