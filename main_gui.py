import tkinter
import customtkinter as ctk
from tkinter import filedialog, messagebox, TclError, simpledialog
import os
import threading
import sys
import webbrowser
import traceback
import torch
import csv
import pandas as pd
from types import SimpleNamespace

# Importa le funzioni main dagli altri script
import trim_video
import detect_and_save_ball
import generate_report
# MODIFICA: Importa entrambe le classi dal selettore interattivo
from interactive_selector import InteractiveVideoSelector, SingleFrameSelector

class StdoutRedirector:
    # ... (questa classe rimane invariata)
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.configure(state="normal")
        self.text_widget.insert(tkinter.END, string)
        self.text_widget.see(tkinter.END)
        self.text_widget.configure(state="disabled")
    def flush(self):
        pass

# NUOVO: Una piccola classe per la finestra di dialogo di scelta
class OnsetChoiceDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Scelta Onset")
        self.geometry("350x150")
        self.transient(parent)
        self.grab_set()

        self.result = None # 'manual', 'interactive', o None

        label = ctk.CTkLabel(self, text="Come vuoi definire il frame di Onset?", font=ctk.CTkFont(size=14))
        label.pack(pady=20)

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10)

        manual_button = ctk.CTkButton(button_frame, text="Inserisci Manualmente", command=self.on_manual)
        manual_button.pack(side="left", padx=10)

        interactive_button = ctk.CTkButton(button_frame, text="Seleziona da Video", command=self.on_interactive)
        interactive_button.pack(side="left", padx=10)
    
    def on_manual(self):
        self.result = 'manual'
        self.destroy()

    def on_interactive(self):
        self.result = 'interactive'
        self.destroy()

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        # ... (tutta la configurazione della finestra e dei widget rimane uguale fino alla funzione load_fixed_template)
        # --- CONFIGURAZIONE FINESTRA ---
        self.title("LabSCoC - Strumento di Analisi CNA")
        self.geometry("850x900")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkScrollableFrame(self)
        container.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(container)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        header_frame.grid_columnconfigure(0, weight=1)
        title_label = ctk.CTkLabel(header_frame, text="Strumento di Analisi Neuro-Visuale", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(anchor="w", padx=10, pady=(10,0))
        lab_link = ctk.CTkLabel(header_frame, text="LabSCoC - Laboratorio di Scienze Cognitive e del Comportamento e Dr. Daniele Lozzi", text_color="#5DADE2", cursor="hand2")
        lab_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://labscoc.wordpress.com/"))
        lab_link.pack(anchor="w", padx=10)
        github_link = ctk.CTkLabel(header_frame, text="Pagina GitHub del Progetto", text_color="#5DADE2", cursor="hand2")
        github_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/danielelozzi/neurological-assessment"))
        github_link.pack(anchor="w", padx=10, pady=(0,10))

        main_frame = ctk.CTkFrame(container)
        main_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)

        self.input_dir = ctk.StringVar()
        self.output_dir = ctk.StringVar()
        self.yolo_model_path = ctk.StringVar()
        self.detection_method = ctk.StringVar(value="YOLO")
        self.run_fragmentation_analysis = ctk.BooleanVar(value=False)
        self.run_excursion_analysis = ctk.BooleanVar(value=False)
        self.manual_events_path = ctk.StringVar()
        self.fast_start_frame = ctk.StringVar()
        self.bbox_padding_perc = ctk.StringVar(value="20") # Default 20%
        self.excursion_threshold_perc = ctk.StringVar(value="80") # Default 80%
        self.fast_end_frame = ctk.StringVar()
        self.slow_start_frame = ctk.StringVar()
        self.slow_end_frame = ctk.StringVar()

        for var in [self.input_dir, self.output_dir, self.yolo_model_path, self.manual_events_path,
                    self.fast_start_frame, self.fast_end_frame, self.slow_start_frame, self.slow_end_frame]:
            var.trace_add("write", self.check_inputs_callback)

        ctk.CTkLabel(main_frame, text="1. Cartella Input:").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(main_frame, textvariable=self.input_dir).grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_input_dir, width=100).grid(row=0, column=2, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="2. Cartella Output:").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        ctk.CTkEntry(main_frame, textvariable=self.output_dir).grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        ctk.CTkButton(main_frame, text="Seleziona...", command=self.select_output_dir, width=100).grid(row=1, column=2, padx=10, pady=10)

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

        manual_options_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        manual_options_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        
        # --- NUOVA STRUTTURA PULSANTI ---
        
        # 1. Template Relativi
        template_frame = ctk.CTkFrame(manual_options_frame)
        template_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(template_frame, text="Template Relativi", font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
        ctk.CTkButton(template_frame, text="Carica Template a Tempi Fissi (da CSV)", command=self.load_fixed_template).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(template_frame, text="Salva Template Relativo Corrente (in CSV)", command=self.save_relative_template).pack(fill="x", padx=10, pady=(5,10))

        # 2. Eventi Assoluti (Carica/Salva)
        absolute_frame = ctk.CTkFrame(manual_options_frame)
        absolute_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(absolute_frame, text="Eventi Assoluti (Carica/Salva)", font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
        ctk.CTkButton(absolute_frame, text="Carica Segmenti FAST/SLOW (da CSV)", command=self.load_main_events_from_file).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(absolute_frame, text="Carica Eventi U/D/L/R (da CSV)", command=self.select_manual_events_file).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(absolute_frame, text="Salva Segmenti FAST/SLOW (CSV Assoluto)", command=self.save_main_events_to_file).pack(fill="x", padx=10, pady=(5,10))
        # Nota: Il salvataggio degli eventi U/D/L/R è gestito dal flusso interattivo

        # 3. Definizione Interattiva
        interactive_frame = ctk.CTkFrame(manual_options_frame)
        interactive_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(interactive_frame, text="Definizione Interattiva", font=ctk.CTkFont(weight="bold")).pack(pady=(5,0))
        ctk.CTkButton(interactive_frame, text="Definisci Segmenti FAST/SLOW (Interattivo)", command=self.define_segments_interactively).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(interactive_frame, text="Definisci Eventi U/D/L/R (Interattivo)", command=self.define_events_interactively).pack(fill="x", padx=10, pady=(5,10))

        # --- FINE NUOVA STRUTTURA (i campi di testo manuali sono stati rimossi come richiesto) ---
        
        # --- NUOVA SEZIONE PARAMETRI ---
        params_frame = ctk.CTkFrame(main_frame)
        params_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        params_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(params_frame, text="Parametri di Analisi", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=(10,0), sticky="w")
        
        ctk.CTkLabel(params_frame, text="Padding Box Inseguimento (%):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(params_frame, textvariable=self.bbox_padding_perc, width=80).grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        ctk.CTkLabel(params_frame, text="Soglia Successo Escursione (%):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkEntry(params_frame, textvariable=self.excursion_threshold_perc, width=80).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        analyses_frame = ctk.CTkFrame(main_frame)
        analyses_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(analyses_frame, text="Analisi Aggiuntive:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10,0))
        ctk.CTkCheckBox(analyses_frame, text="Genera grafici 'Frammentazione'", variable=self.run_fragmentation_analysis).pack(anchor="w", padx=25, pady=2)
        ctk.CTkCheckBox(analyses_frame, text="Calcola metriche 'Escursione' e 'Escursione Direzionale'", variable=self.run_excursion_analysis).pack(anchor="w", padx=25, pady=(2,10))

        console_frame = ctk.CTkFrame(container)
        console_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_rowconfigure(2, weight=1)
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(console_frame, text="Log di Analisi:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        self.console = ctk.CTkTextbox(console_frame, state="disabled", height=200)
        self.console.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        sys.stdout = StdoutRedirector(self.console)
        sys.stderr = StdoutRedirector(self.console)
        
        self.run_button = ctk.CTkButton(self, text="Avvia Analisi Completa", command=self.start_analysis_thread, height=40, font=ctk.CTkFont(size=14, weight="bold"), state="disabled")
        self.run_button.grid(row=1, column=0, padx=20, pady=20, sticky="ew")
        
        self.check_hardware_acceleration()
        self.check_inputs()

    # --- MODIFICA: La funzione per il template ora offre una scelta ---
    def load_fixed_template(self):
        video_path = os.path.join(self.input_dir.get(), 'video.mp4')
        if not os.path.isdir(self.output_dir.get()) or not os.path.exists(video_path):
            messagebox.showerror("Errore", "Seleziona prima una cartella di Input e Output valide.")
            return

        template_path = filedialog.askopenfilename(
            title="Seleziona il file template CSV con i tempi relativi",
            filetypes=[("CSV Files", "*.csv")]
        )
        if not template_path:
            return

        # --- NUOVO: Validazione delle colonne del file template ---
        try:
            df_check = pd.read_csv(template_path)
            required_cols = ['event_type', 'direction', 'relative_start', 'relative_end']
            if not all(col in df_check.columns for col in required_cols):
                messagebox.showerror(
                    "Formato File non Valido",
                    f"Il file selezionato non è un template valido.\n\nDeve contenere le colonne: {required_cols}\n\n"
                    "Se stai cercando di caricare un file di eventi già definiti (es. 'manual_events.csv'), usa l'opzione 'Carica Eventi U/D/L/R (da CSV)'."
                )
                return
        except Exception as e:
            messagebox.showerror("Errore Lettura File", f"Impossibile leggere o validare il file CSV:\n{e}")
            return
        
        # Tentativo di caricare anche gli eventi "main" dal template
        try:
            print(f"INFO: Tentativo di caricamento eventi 'main' da '{template_path}'...")
            df_template_main = pd.read_csv(template_path)
            df_segments = df_template_main[df_template_main['event_type'] == 'segment'].copy()
        except Exception as e:
            print(f"ATTENZIONE: Errore nel caricamento degli eventi 'main' dal template: {e}")

            # Chiedi all'utente COME vuole inserire l'onset
        choice_dialog = OnsetChoiceDialog(self)
        self.wait_window(choice_dialog)
        choice = choice_dialog.result

        onset_frame = None
        if choice == 'manual':
            onset_frame = simpledialog.askinteger(
                "Inserisci Onset",
                "Inserisci il numero del frame di INIZIO del segmento 'fast':",
                parent=self
            )
        elif choice == 'interactive':
            selector = SingleFrameSelector(self, video_path, title="Seleziona il frame di ONSET per FAST")
            self.wait_window(selector)
            onset_frame = selector.result

        if onset_frame is None:
            print("INFO: Caricamento template annullato.")
            return

        try:
            print(f"INFO: Caricamento del template da '{template_path}' con onset al frame {onset_frame}...")
            df_template = pd.read_csv(template_path)
            
            df_template['start_frame'] = df_template['relative_start'] + onset_frame
            df_template['end_frame'] = df_template['relative_end'] + onset_frame

            df_segments = df_template[df_template['event_type'] == 'segment'].copy()
            fast_segment = df_segments[df_segments['direction'] == 'fast'].iloc[0]
            slow_segment = df_segments[df_segments['direction'] == 'slow'].iloc[0]
            
            self.fast_start_frame.set(str(int(fast_segment['start_frame'])))
            self.fast_end_frame.set(str(int(fast_segment['end_frame'])))
            self.slow_start_frame.set(str(int(slow_segment['start_frame'])))
            self.slow_end_frame.set(str(int(slow_segment['end_frame'])))
            print("INFO: Campi dei segmenti compilati e modalità manuale attivata.")
            df_trials = df_template[df_template['event_type'] == 'trial'].copy()
            df_trials['segment_name'] = df_trials.apply(
                lambda row: 'fast' if (row['start_frame'] >= fast_segment['start_frame'] and row['start_frame'] < fast_segment['end_frame']) else 'slow',
                axis=1
            )
            df_trials.rename(columns={'direction': 'direction_simple'}, inplace=True)
            
            output_csv_path = os.path.join(self.output_dir.get(), "manual_events_fixed.csv")
            df_trials[['segment_name', 'direction_simple', 'start_frame', 'end_frame']].to_csv(output_csv_path, index=False)
            
            self.manual_events_path.set(output_csv_path)
            print(f"INFO: File 'manual_events_fixed.csv' generato in '{output_csv_path}' e modalità manuale attivata.")

        except Exception as e:
            messagebox.showerror("Errore nel Template", f"Impossibile processare il file template:\n{e}")
            traceback.print_exc()

    # --- Il resto delle funzioni (define_segments_interactively, ecc.) rimane invariato ---
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
            
            print("Segmenti 'fast' e 'slow' definiti interattivamente.")
        else:
            print("Definizione interattiva dei segmenti annullata.")

    def save_relative_template(self):
        """
        Salva un template con tempi relativi basandosi sui valori correnti nella GUI.
        Chiede all'utente di specificare l'onset per il calcolo.
        """
        try:
            # 1. Verifica che ci siano dati da cui partire
            fs = int(self.fast_start_frame.get())
            fe = int(self.fast_end_frame.get())
            ss = int(self.slow_start_frame.get())
            se = int(self.slow_end_frame.get())
            
            if not os.path.exists(self.manual_events_path.get()):
                messagebox.showerror("Dati Mancanti", "Per creare un template relativo, devi prima definire e caricare un file di eventi U/D/L/R (es. 'manual_events.csv').")
                return

            # 2. Chiedi l'onset (che sarà il nostro "zero")
            onset_frame = simpledialog.askinteger(
                "Definisci Onset per Template",
                "Quale frame deve essere considerato il punto '0' per i tempi relativi?\n(Solitamente l'inizio del segmento FAST)",
                initialvalue=fs,
                parent=self
            )
            if onset_frame is None:
                print("INFO: Creazione template relativo annullata.")
                return

            # 3. Chiedi dove salvare il file
            save_path = filedialog.asksaveasfilename(
                title="Salva Template Relativo",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv")],
                initialfile="relative_template.csv"
            )
            if not save_path:
                return

            # 4. Calcola e scrivi i dati
            template_data = []
            # Aggiungi segmenti
            template_data.append({'event_type': 'segment', 'direction': 'fast', 'relative_start': fs - onset_frame, 'relative_end': fe - onset_frame})
            template_data.append({'event_type': 'segment', 'direction': 'slow', 'relative_start': ss - onset_frame, 'relative_end': se - onset_frame})

            # Aggiungi trial
            df_trials_abs = pd.read_csv(self.manual_events_path.get())
            for _, row in df_trials_abs.iterrows():
                template_data.append({
                    'event_type': 'trial',
                    'direction': row['direction_simple'],
                    'relative_start': row['start_frame'] - onset_frame,
                    'relative_end': row['end_frame'] - onset_frame
                })
            
            df_template = pd.DataFrame(template_data)
            df_template.to_csv(save_path, index=False)

            print(f"INFO: Template relativo salvato con successo in: {save_path}")
            messagebox.showinfo("Successo", f"Template relativo salvato in:\n{save_path}")

        except (ValueError, TclError):
            messagebox.showerror("Errore", "I valori dei frame per i segmenti FAST/SLOW non sono numeri validi.")
        except Exception as e:
            messagebox.showerror("Errore", f"Impossibile creare il template relativo:\n{e}")
            traceback.print_exc()

    def save_main_events_to_file(self):
        save_path = filedialog.asksaveasfilename(
            title="Salva file eventi MAIN (FAST/SLOW) CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            initialfile="manual_main_events.csv"
        )
        if save_path:
            try:
                fs = int(self.fast_start_frame.get())
                fe = int(self.fast_end_frame.get())
                ss = int(self.slow_start_frame.get())
                se = int(self.slow_end_frame.get())

                with open(save_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['segment_name', 'start_frame', 'end_frame'])
                    writer.writerow(['fast', fs, fe])
                    writer.writerow(['slow', ss, se])

                print(f"INFO: File eventi MAIN creato e salvato in: {save_path}")
            except ValueError:
                messagebox.showerror("Errore", "Valori di frame FAST/SLOW non validi.")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante il salvataggio del file: {e}")

        else:
            print("INFO: Salvataggio eventi MAIN annullato.")

    def load_main_events_from_file(self):
        load_path = filedialog.askopenfilename(
            title="Carica file eventi MAIN (FAST/SLOW) CSV",
            filetypes=[("CSV Files", "*.csv")]
        )
        if load_path:
            try:
                df = pd.read_csv(load_path)
                fast_segment = df[df['segment_name'] == 'fast'].iloc[0]
                slow_segment = df[df['segment_name'] == 'slow'].iloc[0]

                self.fast_start_frame.set(str(int(fast_segment['start_frame'])))
                self.fast_end_frame.set(str(int(fast_segment['end_frame'])))
                self.slow_start_frame.set(str(int(slow_segment['start_frame'])))
                self.slow_end_frame.set(str(int(slow_segment['end_frame'])))
                
                print(f"INFO: Segmenti FAST/SLOW caricati da '{load_path}'.")
            except Exception as e:
                messagebox.showerror("Errore di Caricamento", f"Impossibile leggere il file dei segmenti:\n{e}")

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
                print(f"File eventi creato e salvato in: {save_path}")
        else:
            print("Definizione interattiva degli eventi annullata o nessun evento definito.")

    def select_manual_events_file(self):
        path = filedialog.askopenfilename(title="Seleziona file eventi CSV", filetypes=[("CSV Files", "*.csv")])
        if path: 
            self.manual_events_path.set(path)
            print(f"INFO: File eventi U/D/L/R impostato su: {path}")
    
    def check_inputs_callback(self, *args):
        self.check_inputs()

    def check_inputs(self):
        input_ok = os.path.isdir(self.input_dir.get())
        output_ok = os.path.isdir(self.output_dir.get())
        
        # I campi dei segmenti sono validi se sono vuoti (modalità auto) o se contengono numeri validi
        manual_segments_ok = False
        try:
            fs = self.fast_start_frame.get()
            fe = self.fast_end_frame.get()
            ss = self.slow_start_frame.get()
            se = self.slow_end_frame.get()
            if all(v == "" for v in [fs, fe, ss, se]): # Tutti vuoti -> OK (auto)
                manual_segments_ok = True
            elif all(v.isdigit() for v in [fs, fe, ss, se]) and int(fe) > int(fs) and int(se) > int(ss): # Tutti numeri validi -> OK (manuale)
                manual_segments_ok = True
        except (ValueError, tkinter.TclError):
            manual_segments_ok = False
        
        auto_detect_ok = os.path.isfile(self.yolo_model_path.get()) if self.detection_method.get() == "YOLO" else True

        final_ok = input_ok and output_ok and manual_segments_ok and auto_detect_ok
            
        self.run_button.configure(state="normal" if final_ok else "disabled")

    def start_analysis_thread(self):
        self.run_button.configure(state="disabled")
        analysis_thread = threading.Thread(target=self.run_full_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()

    def run_full_analysis(self):
        success = False
        error_message = ""
        try:
            print("--- ANALISI AVVIATA ---\n")
            
            # Determina se usare i segmenti manuali o automatici
            use_manual_segments = False
            try:
                if all(v.isdigit() for v in [self.fast_start_frame.get(), self.fast_end_frame.get(), self.slow_start_frame.get(), self.slow_end_frame.get()]):
                    use_manual_segments = True
            except TclError:
                pass

            cut_points_path = os.path.join(self.output_dir.get(), 'cut_points.csv')
            if use_manual_segments:
                print("Modalità manuale segmenti attiva: creo 'cut_points.csv' dai valori inseriti nella GUI...")
                with open(cut_points_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['segment_name', 'start_frame', 'end_frame'])
                    writer.writerow(['fast', self.fast_start_frame.get(), self.fast_end_frame.get()])
                    writer.writerow(['slow', self.slow_start_frame.get(), self.slow_end_frame.get()])
                print("'cut_points.csv' creato con successo.")
            else:
                print("Modalità automatica segmenti: avvio 'trim_video.py'...")
                args_trim = SimpleNamespace(
                    input_video=os.path.join(self.input_dir.get(), 'video.mp4'),
                    output_dir=self.output_dir.get()
                )
                trim_video.main(args_trim)

            print("\n--- Avvio 'detect_and_save_ball.py' ---")
            args_detect = SimpleNamespace(
                input_dir=self.input_dir.get(),
                output_dir=self.output_dir.get(),
                use_yolo=(self.detection_method.get() == "YOLO"),
                yolo_model=self.yolo_model_path.get(),
                # Aggiungo il nuovo parametro per il padding
                bbox_padding_factor=1.0 + (float(self.bbox_padding_perc.get()) / 100.0)
            )
            detect_and_save_ball.main(args_detect)

            print("\n--- Avvio 'generate_report.py' ---")
            # Determina se usare il file di eventi manuali
            manual_events_file = self.manual_events_path.get()
            if not os.path.isfile(manual_events_file):
                manual_events_file = None
            args_report = SimpleNamespace(
                analysis_dir=self.output_dir.get(),
                output_dir=self.output_dir.get(),
                input_dir_for_pupil=self.input_dir.get(),
                run_fragmentation_analysis=self.run_fragmentation_analysis.get(),
                run_excursion_analysis=self.run_excursion_analysis.get(),
                manual_events_path=manual_events_file,
                # Aggiungo i nuovi parametri per le soglie
                excursion_success_threshold=float(self.excursion_threshold_perc.get()) / 100.0
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