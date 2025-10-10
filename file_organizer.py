# file_organizer.py

import os
import zipfile
import shutil
import glob
from tkinter import messagebox

def find_file_recursively(root_dir, filename_pattern):
    """
    Cerca un file in modo ricorsivo in una directory usando un pattern (es. '*.mp4' o 'gaze.csv').
    Restituisce il percorso del primo file trovato.
    """
    for root, _, files in os.walk(root_dir):
        for file in files:
            if glob.fnmatch.fnmatch(file, filename_pattern):
                return os.path.join(root, file)
    return None

def organize_files(source_dir):
    """
    Trova i file ZIP in una cartella, li scompatta e organizza i file necessari
    in una nuova cartella 'input_data'.
    """
    print(f"--- Avvio Organizzazione Dati da '{source_dir}' ---")

    # --- NUOVA LOGICA: Cerca i file ZIP specifici ---
    timeseries_zip = None
    qr_zip = None

    for filename in os.listdir(source_dir):
        # Cerca in modo case-insensitive
        if filename.lower().endswith('.zip'):
            if 'timeseries' in filename.lower():
                timeseries_zip = os.path.join(source_dir, filename)
            elif 'qr' in filename.lower():
                qr_zip = os.path.join(source_dir, filename)

    if not timeseries_zip or not qr_zip:
        error_msg = "Impossibile trovare i file ZIP necessari:\n\n"
        if not timeseries_zip:
            error_msg += "- Manca il file ZIP di 'Time Series Data' (deve contenere 'Timeseries' nel nome).\n"
        if not qr_zip:
            error_msg += "- Manca il file ZIP di 'QR Marker Mapper' (deve contenere 'QR' nel nome).\n"
        messagebox.showerror("File ZIP Mancanti", error_msg)
        print(f"ERRORE: {error_msg.replace(chr(10)*2, chr(10))}") # Rimuove doppi a capo per il log
        return

    zip_files = [timeseries_zip, qr_zip]
    print(f"Trovati file ZIP specifici:\n - Time Series: {os.path.basename(timeseries_zip)}\n - QR Marker:   {os.path.basename(qr_zip)}")

    temp_extract_dir = os.path.join(source_dir, "temp_extraction")
    if os.path.exists(temp_extract_dir):
        shutil.rmtree(temp_extract_dir)
    os.makedirs(temp_extract_dir)

    try:
        # --- MODIFICA: Scompatta ogni ZIP nella sua cartella dedicata ---
        time_series_folder = os.path.join(temp_extract_dir, "timeseries_files")
        marker_mapper_folder = os.path.join(temp_extract_dir, "qr_files")
        os.makedirs(time_series_folder)
        os.makedirs(marker_mapper_folder)

        print(f"Scompattando '{os.path.basename(timeseries_zip)}'...")
        with zipfile.ZipFile(timeseries_zip, 'r') as zip_ref:
            zip_ref.extractall(time_series_folder)

        print(f"Scompattando '{os.path.basename(qr_zip)}'...")
        with zipfile.ZipFile(qr_zip, 'r') as zip_ref:
            zip_ref.extractall(marker_mapper_folder)
        # --- FINE MODIFICA ---

        # Crea la cartella di destinazione
        output_data_dir = os.path.join(source_dir, "input_data")
        if os.path.exists(output_data_dir):
            if not messagebox.askyesno("Cartella Esistente", f"La cartella '{output_data_dir}' esiste già.\nVuoi sovrascriverla?"):
                print("INFO: Operazione annullata dall'utente.")
                return
            shutil.rmtree(output_data_dir)
        os.makedirs(output_data_dir)

        # --- MODIFICA: Cerca i file ricorsivamente ---
        # Dizionario dei file da trovare: {nome file: cartella base in cui cercare}
        files_to_find = {
            'gaze.csv': marker_mapper_folder,
            'surface_positions.csv': marker_mapper_folder,
            'world_timestamps.csv': time_series_folder,
            '3d_eye_states.csv': time_series_folder, # Opzionale
        }

        # Trova e copia il video
        video_source_path = find_file_recursively(time_series_folder, '*.mp4')
        if not video_source_path:
            messagebox.showwarning("File Mancante", "Nessun file video (.mp4) trovato nella cartella 'Time Series Data'.")
            print("ATTENZIONE: Nessun video .mp4 trovato.")
        else:
            video_dest_path = os.path.join(output_data_dir, 'video.mp4')
            shutil.copy(video_source_path, video_dest_path)
            print(f"✅ Copiato e rinominato '{os.path.basename(video_source_path)}' in 'video.mp4'")

        # Copia gli altri file
        for dest_name, base_folder in files_to_find.items():
            source_path = find_file_recursively(base_folder, dest_name)
            if os.path.exists(source_path):
                shutil.copy(source_path, os.path.join(output_data_dir, dest_name))
                print(f"✅ Copiato '{dest_name}'")
            elif dest_name != '3d_eye_states.csv':
                messagebox.showwarning("File Mancante", f"Il file richiesto '{dest_name}' non è stato trovato.")
                print(f"ATTENZIONE: File '{dest_name}' non trovato ricorsivamente in '{base_folder}'")
        # --- FINE MODIFICA ---

        messagebox.showinfo("Operazione Completata", f"Dati organizzati con successo!\nLa nuova cartella di input è:\n{output_data_dir}")
        print(f"\n--- Organizzazione completata. Dati pronti in '{output_data_dir}' ---")

    except Exception as e:
        messagebox.showerror("Errore Inaspettato", f"Si è verificato un errore durante l'organizzazione:\n{e}")
        print(f"ERRORE: {e}")
    finally:
        # Pulisci la cartella di estrazione temporanea
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
            print("INFO: Pulizia file temporanei completata.")

if __name__ == '__main__':
    # Esempio di utilizzo (richiede una GUI per selezionare la cartella)
    from tkinter import filedialog
    source = filedialog.askdirectory(title="Seleziona la cartella contenente i file ZIP")
    if source:
        organize_files(source)