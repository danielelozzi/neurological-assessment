import tkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import sys
import webbrowser
import traceback
import torch
import csv
import pandas as pd # Aggiunto per scrivere il CSV
from types import SimpleNamespace
import trim_video
import detect_and_save_ball
import generate_report
from interactive_selector import InteractiveVideoSelector


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
        self.geometry("800x1250") # Altezza leggermente aumentata per i nuovi pulsanti
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- HEADER E BRANDING ---
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(header_frame, text="Strumento di Analisi Neuro-Visuale", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(anchor="w", padx=10, pady=(10,0))
        lab_link = ctk.CTkLabel(header_frame, text="LabSCoC - Laboratorio di Scienze Cognitive e del Comportamento e Dr. Daniele Lozzi", text_color="#5DADE2", cursor="hand2")
        lab_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://labscoc.wordpress.com/"))
        lab_link.pack(anchor="w", padx=10)
        github_link = ctk.CTkLabel(header_frame, text="Pagina GitHub del Progetto", text_color="#5DADE2", cursor="hand2")
        github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/danielelozzi/neurological-assessment"))
        github_link.pack(anchor="w", padx=10, pady=(0,10))

        # --- FRAME PRINCIPALE ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        # --- VARIABILI DI STATO ---
        self.input_dir = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.yolo_model_path = ctk.StringVar()
        self.detection_method = ctk.StringVar(value="YOLO")
        self.run_fragmentation_analysis = ctk.BooleanVar(value=False)
        self.run_excursion_analysis = ctk.BooleanVar(value=False)
        self.manual_segments_mode = ctk.BooleanVar(value=False)
        self.manual_events_mode = ctk.BooleanVar(value=False)
        self.manual_events_path = ctk.StringVar()
        self.fast_start_frame = ctk.StringVar()
        self.fast_end_frame = ctk.StringVar()
        self.slow_start_frame = ctk.StringVar()
        self.slow_end_frame = ctk.StringVar()

        for var in [self.input_dir, self.output_dir, self.yolo_model_path, self.manual_events_path,
                    self.fast_start_frame, self.fast_end_frame, self.slow_start_frame, self.slow_end_frame]:
            var.trace_add("write", self.check_inputs_callback)

        # --- Sezione Input/Output ---
        ctk.CTkLabel(main_frame, text="1. Cartella Input:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(main_frame, textvariable=self.input_dir).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_input_dir, width=100).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="2. Cartella Output:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(main_frame, textvariable=self.output_dir).grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_output_dir, width=100).grid(row=1, column=2, padx=10, pady=10)

        # --- Sezione Rilevamento Automatico ---
        self.auto_detection_frame = ctk.CTkFrame(main_frame)
        self.auto_detection_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        self.auto_detection_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.auto_detection_frame, text="3. Metodo Rilevamento Palla:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkSegmentedButton(self.auto_detection_frame, values=["YOLO", "Hough Circle"], variable=self.detection_method, command=self.check_inputs_callback).grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky="w")
        self.yolo_label = ctk.CTkLabel(self.auto_detection_frame, text="4. Modello YOLO (.pt):")
        self.yolo_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.yolo_path_entry = ctk.CTkEntry(self.auto_detection_frame, textvariable=self.yolo_model_path)
        self.yolo_path_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(self.auto_detection_frame, text="Seleziona...", command=self.select_yolo_model, width=100).grid(row=1, column=2, padx=10, pady=10)

        # --- Sezione Opzioni Manuali ---
        manual_options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        manual_options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # Pulsanti per la selezione interattiva
        interactive_buttons_frame = ctk.CTkFrame(manual_options_frame)
        interactive_buttons_frame.pack(fill="x", pady=(5, 15))
        
        self.interactive_segments_button = ctk.CTkButton(interactive_buttons_frame, text="Definisci Segmenti FAST/SLOW (Interattivo)", command=self.define_segments_interactively)
        self.interactive_segments_button.pack(fill="x", padx=20, pady=5)

        self.interactive_events_button = ctk.CTkButton(interactive_buttons_frame, text="Definisci Eventi UP/DOWN/LEFT/RIGHT (Interattivo)", command=self.define_events_interactively)
        self.interactive_events_button.pack(fill="x", padx=20, pady=5)
        
        # Checkbox per i segmenti manuali (testuale)
        self.manual_segments_check = ctk.CTkCheckBox(manual_options_frame, text="Definisci Segmenti Manualmente (Testuale)", variable=self.manual_segments_mode, command=self.toggle_manual_segments_frame)
        self.manual_segments_check.pack(anchor="w", padx=5, pady=(10,0))
        
        # Frame per l'inserimento manuale dei segmenti
        self.manual_segments_frame = ctk.CTkFrame(manual_options_frame)
        self.manual_segments_frame.columnconfigure(1, weight=1)
        ctk.CTkLabel(self.manual_segments_frame, text="Segmento 'Fast':").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(self.manual_segments_frame, textvariable=self.fast_start_frame, placeholder_text="Frame Inizio").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(self.manual_segments_frame, textvariable=self.fast_end_frame, placeholder_text="Frame Fine").grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(self.manual_segments_frame, text="Segmento 'Slow':").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(self.manual_segments_frame, textvariable=self.slow_start_frame, placeholder_text="Frame Inizio").grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkEntry(self.manual_segments_frame, textvariable=self.slow_end_frame, placeholder_text="Frame Fine").grid(row=1, column=2, padx=5, pady=5, sticky="ew")

        # Checkbox per gli eventi manuali (CSV)
        self.manual_events_check = ctk.CTkCheckBox(manual_options_frame, text="Carica Eventi da File CSV", variable=self.manual_events_mode, command=self.toggle_manual_events_frame)
        self.manual_events_check.pack(anchor="w", padx=5, pady=(10,0))

        # Frame per la selezione del file CSV
        self.manual_events_frame = ctk.CTkFrame(manual_options_frame)
        self.manual_events_frame.columnconfigure(0, weight=1)
        self.manual_events_entry = ctk.CTkEntry(self.manual_events_frame, textvariable=self.manual_events_path)
        self.manual_events_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.manual_events_button = ctk.CTkButton(self.manual_events_frame, text="Seleziona...", width=100, command=self.select_manual_events_file)
        self.manual_events_button.grid(row=0, column=1, padx=10, pady=10)

        # --- Sezione Analisi Aggiuntive ---
        analyses_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        analyses_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(analyses_frame, text="Analisi Aggiuntive:").pack(anchor="w", padx=5, pady=(10,0))
        ctk.CTkCheckBox(analyses_frame, text="Genera grafici 'Frammentazione'", variable=self.run_fragmentation_analysis).pack(anchor="w", padx=25, pady=5)
        ctk.CTkCheckBox(analyses_frame, text="Calcola metrica 'Escursione'", variable=self.run_excursion_analysis).pack(anchor="w", padx=25, pady=5)

        # --- Console e Pulsante Avvio ---
        console_frame = ctk.CTkFrame(self)
        console_frame.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(console_frame, text="Log di Analisi:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        self.console = ctk.CTkTextbox(console_frame, state="disabled")
        self.console.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        sys.stdout = StdoutRedirector(self.console)
        sys.stderr = StdoutRedirector(self.console)
        
        self.run_button = ctk.CTkButton(self, text="Avvia Analisi Completa", command=self.start_analysis_thread, height=40, font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.run_button.grid(row=4, column=0, padx=20, pady=20, sticky="ew")
        
        # --- Inizializzazione ---
        self.check_hardware_acceleration()
        self.toggle_manual_segments_frame()
        self.toggle_manual_events_frame()
        self.check_inputs()

    def define_segments_interactively(self):
        video_path = os.path.join(self.input_dir.get(), 'video.mp4')
        if not os.path.exists(video_path):
            messagebox.showerror("Errore", "Seleziona una cartella di Input valida contenente 'video.mp4'.")
            return

        selector = InteractiveVideoSelector(self, video_path, event_types=['fast', 'slow'], title="Definisci Segmenti")
        self.wait_window(selector)

        if selector.result:
            segments = {item['label']: (item['start'], item['end']) for item in selector.result}
            if 'fast' in segments:
                self.fast_start_frame.set(str(segments['fast'][0]))
                self.fast_end_frame.set(str(segments['fast'][1]))
            if 'slow' in segments:
                self.slow_start_frame.set(str(segments['slow'][0]))
                self.slow_end_frame.set(str(segments['slow'][1]))
            
            self.manual_segments_mode.set(True) # Attiva la modalità manuale testuale
            print("Segmenti 'fast' e 'slow' definiti interattivamente.")
        else:
            print("Definizione interattiva dei segmenti annullata.")

    def define_events_interactively(self):
        video_path = os.path.join(self.input_dir.get(), 'video.mp4')
        if not os.path.exists(video_path):
            messagebox.showerror("Errore", "Seleziona una cartella di Input valida contenente 'video.mp4'.")
            return

        event_types = ['right', 'left', 'up', 'down']
        selector = InteractiveVideoSelector(self, video_path, event_types=event_types, title="Definisci Eventi di Movimento")
        self.wait_window(selector)

        if selector.result and len(selector.result) > 0:
            save_path = filedialog.asksaveasfilename(
                title="Salva file eventi CSV",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                initialfile="manual_events.csv"
            )
            if save_path:
                df_data = []
                for event in selector.result:
                    segment_name = 'unknown'
                    try:
                        fs, fe = int(self.fast_start_frame.get()), int(self.fast_end_frame.get())
                        ss, se = int(self.slow_start_frame.get()), int(self.slow_end_frame.get())
                        if fs <= event['start'] <= fe: segment_name = 'fast'
                        elif ss <= event['start'] <= se: segment_name = 'slow'
                    except (ValueError, TclError):
                        pass

                    df_data.append({
                        'segment_name': segment_name,
                        'direction_simple': event['label'],
                        'start_frame': event['start'],
                        'end_frame': event['end']
                    })
                
                df = pd.DataFrame(df_data)
                df.to_csv(save_path, index=False)
                self.manual_events_path.set(save_path)
                self.manual_events_mode.set(True)
                print(f"File eventi creato e salvato in: {save_path}")
        else:
            print("Definizione interattiva degli eventi annullata o nessun evento definito.")

    def toggle_manual_segments_frame(self):
        if self.manual_segments_mode.get():
            self.manual_segments_frame.pack(fill="x", expand=True, padx=20, pady=5)
        else:
            self.manual_segments_frame.pack_forget()
        self.check_inputs()

    def toggle_manual_events_frame(self):
        if self.manual_events_mode.get():
            self.manual_events_frame.pack(fill="x", expand=True, padx=20, pady=5)
        else:
            self.manual_events_frame.pack_forget()
        self.check_inputs()

    def select_manual_events_file(self):
        path = filedialog.askopenfilename(title="Seleziona file eventi CSV", filetypes=[("CSV Files", "*.csv")])
        if path: self.manual_events_path.set(path)
    
    def check_inputs_callback(self, *args):
        self.check_inputs()

    def check_inputs(self):
        input_ok = os.path.isdir(self.input_dir.get())
        output_ok = os.path.isdir(self.output_dir.get())
        
        manual_segments_ok = not self.manual_segments_mode.get()
        if self.manual_segments_mode.get():
            try:
                fs = int(self.fast_start_frame.get() or 0)
                fe = int(self.fast_end_frame.get() or 0)
                ss = int(self.slow_start_frame.get() or 0)
                se = int(self.slow_end_frame.get() or 0)
                if (fe > fs) and (se > ss):
                    manual_segments_ok = True
            except (ValueError, tkinter.TclError):
                manual_segments_ok = False
        
        manual_events_ok = not self.manual_events_mode.get() or os.path.isfile(self.manual_events_path.get())
        
        auto_detect_ok = os.path.isfile(self.yolo_model_path.get()) if self.detection_method.get() == "YOLO" else True

        final_ok = input_ok and output_ok and manual_segments_ok and manual_events_ok and auto_detect_ok
            
        self.run_button.configure(state="normal" if final_ok else "disabled")

    def start_analysis_thread(self):
        self.run_button.configure(state="disabled")
        analysis_thread = threading.Thread(target=self.run_full_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()

# In main_gui.py

    def run_full_analysis(self):
        """Esegue l'intera pipeline di analisi."""
        success = False
        error_message = ""
        try:
            print("--- ANALISI AVVIATA ---\n")
            
            # --- FASE 1: Definizione Punti di Taglio ---
            cut_points_path = os.path.join(self.output_dir.get(), 'cut_points.csv')
            if self.manual_segments_mode.get():
                print("Modalità manuale attiva: creo 'cut_points.csv' dai valori inseriti nella GUI...")
                with open(cut_points_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['segment_name', 'start_frame', 'end_frame'])
                    writer.writerow(['fast', self.fast_start_frame.get(), self.fast_end_frame.get()])
                    writer.writerow(['slow', self.slow_start_frame.get(), self.slow_end_frame.get()])
                print("'cut_points.csv' creato con successo.")
            else:
                print("Modalità automatica: avvio 'trim_video.py' per trovare i punti di taglio...")
                # --- CORREZIONE QUI: Usa SimpleNamespace ---
                args_trim = SimpleNamespace(
                    input_video=os.path.join(self.input_dir.get(), 'video.mp4'),
                    output_dir=self.output_dir.get()
                )
                trim_video.main(args_trim)

            # --- FASE 2: Rilevamento palla e sguardi ---
            print("\n--- Avvio 'detect_and_save_ball.py' ---")
            # --- CORREZIONE QUI: Usa SimpleNamespace ---
            args_detect = SimpleNamespace(
                input_dir=self.input_dir.get(), 
                output_dir=self.output_dir.get(), 
                use_yolo=(self.detection_method.get() == "YOLO"), 
                yolo_model=self.yolo_model_path.get()
            )
            detect_and_save_ball.main(args_detect)

            # --- FASE 3: Generazione Report ---
            print("\n--- Avvio 'generate_report.py' ---")
            manual_events_file = self.manual_events_path.get() if self.manual_events_mode.get() else None
            # --- CORREZIONE QUI: Usa SimpleNamespace ---
            args_report = SimpleNamespace(
                analysis_dir=self.output_dir.get(), 
                output_dir=self.output_dir.get(), 
                input_dir_for_pupil=self.input_dir.get(), 
                run_fragmentation_analysis=self.run_fragmentation_analysis.get(), 
                run_excursion_analysis=self.run_excursion_analysis.get(),
                manual_events_path=manual_events_file
            )
            generate_report.main(args_report)
            
            print("\n====== ANALISI COMPLETATA CON SUCCESSO ======")
            success = True

        except Exception as e:
            error_message = str(e)
            print(f"\n====== ERRORE DURANTE L'ANALISI ======\n{e}")
            traceback.print_exc()
        finally:
            self.after(0, self.analysis_finished, success, error_message)

    def select_input_dir(self):
        path = filedialog.askdirectory(title="Seleziona cartella input")
        if path: self.input_dir.set(path)

    def select_output_dir(self):
        path = filedialog.askdirectory(title="Seleziona cartella output")
        if path: self.output_dir.set(path)

    def select_yolo_model(self):
        path = filedialog.askopenfilename(title="Seleziona modello YOLO", filetypes=[("YOLO Model", "*.pt")])
        if path: self.yolo_model_path.set(path)

    def analysis_finished(self, success, error_message):
        self.check_inputs()
        if success:
            messagebox.showinfo("Analisi Completata", f"L'analisi è terminata con successo.\nI risultati sono nella cartella di output:\n{self.output_dir.get()}")
        else:
            messagebox.showerror("Errore di Analisi", f"Si è verificato un errore durante l'analisi.\n\nDettagli: {error_message}\n\nControllare il log per ulteriori informazioni.")

    def check_hardware_acceleration(self):
        print("--- CONTROLLO ACCELERAZIONE HARDWARE ---")
        try:
            if torch.cuda.is_available():
                print(f"✅ Trovata GPU compatibile con CUDA: {torch.cuda.get_device_name(0)}")
            elif torch.backends.mps.is_available():
                print("✅ Trovato backend 'Metal' di Apple per l'accelerazione GPU.")
            else:
                print("⚠️ ATTENZIONE: Nessuna GPU accelerata (CUDA/MPS) trovata. L'analisi potrebbe essere più lenta.")
        except Exception as e:
            print(f"ERRORE durante il controllo hardware: {e}\n")

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()