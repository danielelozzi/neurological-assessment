import pandas as pd
import numpy as np
import os
import cv2
import re # Importa il modulo re per la pulizia dei nomi delle colonne
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import interp1d

PUPIL_COL_NAME = 'pupil_diameter_mean'

def get_video_dimensions(video_path):
    if not os.path.exists(video_path): return 1920, 1080
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return 1920, 1080
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return w, h

def load_manual_events(df_main, manual_events_path):
    """Carica e applica gli eventi (trial) da un file CSV fornito dall'utente."""
    print(f"INFO: Caricamento eventi manuali da '{os.path.basename(manual_events_path)}'...")
    try:
        df_events = pd.read_csv(manual_events_path)
        required_cols = ['segment_name', 'direction_simple', 'start_frame', 'end_frame']
        if not all(col in df_events.columns for col in required_cols):
            raise ValueError(f"Il file CSV deve contenere le colonne: {required_cols}")
    except Exception as e:
        raise Exception(f"Errore nella lettura del file CSV degli eventi: {e}")

    df_main['direction'] = ''
    df_main['trial_id'] = 0
    df_main['direction_simple'] = ''
    trial_counter = 0

    for _, event in df_events.iterrows():
        trial_counter += 1
        mask = (df_main['frame'] >= event['start_frame']) & (df_main['frame'] <= event['end_frame'])
        df_main.loc[mask, 'trial_id'] = trial_counter
        df_main.loc[mask, 'direction_simple'] = event['direction_simple']
        df_main.loc[mask, 'direction'] = f"center_to_{event['direction_simple']}"

    df_main['ball_speed'] = np.sqrt(df_main['ball_center_x_norm'].diff()**2 + df_main['ball_center_y_norm'].diff()**2)
    df_main['gaze_speed'] = np.sqrt(df_main['gaze_x_norm'].diff()**2 + df_main['gaze_y_norm'].diff()**2)
    df_main.loc[df_main['trial_id'] != df_main['trial_id'].shift(1), ['ball_speed', 'gaze_speed']] = np.nan
    
    print(f"INFO: Caricati e applicati {len(df_events)} eventi manuali.")
    return df_main

def calculate_movement_data(df):
    """Calcola automaticamente i trial basandosi sul movimento della palla."""
    print("INFO: Calcolo automatico di 'direction' e 'trial_id'...")
    def get_zone(x, y):
        if pd.isna(x) or pd.isna(y): return 'other'
        if 0.40 < x < 0.60 and 0.40 < y < 0.60: return 'center'
        if y <= 0.40: return 'up'
        if y >= 0.60: return 'down'
        if x <= 0.40: return 'left'
        if x >= 0.60: return 'right'
        return 'other'
    df['zone'] = df.apply(lambda row: get_zone(row['ball_center_x_norm'], row['ball_center_y_norm']), axis=1)
    df['direction'], df['trial_id'], df['direction_simple'] = '', 0, ''
    trial_counter, in_trial = 0, False
    current_direction = ''
    for i in range(1, len(df)):
        prev_zone = df.loc[i-1, 'zone']
        curr_zone = df.loc[i, 'zone']
        
        if not in_trial and prev_zone == 'center' and curr_zone not in ['center', 'other']:
            in_trial = True
            trial_counter += 1
            current_direction = curr_zone
        
        if in_trial:
            df.loc[i, 'trial_id'] = trial_counter
            df.loc[i, 'direction'] = f"center_to_{current_direction}"
            df.loc[i, 'direction_simple'] = current_direction
        
        if in_trial and curr_zone == 'center':
            in_trial = False
            current_direction = ''
    
    df['ball_speed'] = np.sqrt(df['ball_center_x_norm'].diff()**2 + df['ball_center_y_norm'].diff()**2)
    df['gaze_speed'] = np.sqrt(df['gaze_x_norm'].diff()**2 + df['gaze_y_norm'].diff()**2)
    df.loc[df['trial_id'] != df['trial_id'].shift(1), ['ball_speed', 'gaze_speed']] = np.nan
    df.drop(columns=['zone'], inplace=True)
    print(f"INFO: Calcolo completato. Trovati {trial_counter} trial.")
    return df

def add_pupil_data(df_main, base_dir):
    """Aggiunge i dati sul diametro pupillare al dataframe principale."""
    pupil_path = os.path.join(base_dir, '3d_eye_states.csv') # Modificato da pupil.csv
    if not os.path.exists(pupil_path):
        print("ATTENZIONE: File '3d_eye_states.csv' non trovato. L'analisi pupillometrica sarà saltata.")
        return df_main

    print("INFO: Aggiunta dei dati pupillari...")
    df_pupil = pd.read_csv(pupil_path)
    
    if 'timestamp [ns]' not in df_pupil.columns:
        print("ATTENZIONE: Colonna 'timestamp [ns]' non trovata in 3d_eye_states.csv.")
        return df_main
    
    df_pupil.rename(columns={'timestamp [ns]': 'pupil_timestamp_ns'}, inplace=True)
    df_pupil['pupil_timestamp_dt'] = pd.to_datetime(df_pupil['pupil_timestamp_ns'], unit='ns')
    
    # Pulizia dei nomi delle colonne per facilitare la ricerca
    df_pupil.columns = [re.sub(r'[^a-zA-Z0-9_\[\]]', '', col).strip() for col in df_pupil.columns]
    
    # Colonne per il diametro pupillare nel nuovo file
    left_pupil_col = 'pupil diameter left [mm]'
    right_pupil_col = 'pupil diameter right [mm]'

    if left_pupil_col in df_pupil.columns and right_pupil_col in df_pupil.columns:
        df_pupil[PUPIL_COL_NAME] = df_pupil[[left_pupil_col, right_pupil_col]].mean(axis=1)
    elif left_pupil_col in df_pupil.columns:
        df_pupil[PUPIL_COL_NAME] = df_pupil[left_pupil_col]
    elif right_pupil_col in df_pupil.columns:
        df_pupil[PUPIL_COL_NAME] = df_pupil[right_pupil_col]
    else:
        print("ATTENZIONE: Colonne diametro pupillare ('pupil diameter left [mm]' o 'pupil diameter right [mm]') non trovate in 3d_eye_states.csv.")
        return df_main

    # --- CORREZIONE: Usa il timestamp preciso se disponibile, altrimenti usa il frame come fallback ---
    if 'world_timestamp_ns' in df_main.columns:
        print("INFO: Trovata colonna 'world_timestamp_ns'. Utilizzo timestamp preciso per il merge.")
        df_main['world_timestamp_dt'] = pd.to_datetime(df_main['world_timestamp_ns'], unit='ns')
    else:
        print("ATTENZIONE: Colonna 'world_timestamp_ns' non trovata. Uso il numero di frame come proxy per il timestamp (meno preciso).")
        df_main['world_timestamp_dt'] = pd.to_datetime(df_main['frame'].astype(int)) # Fallback
    
    merged_df = pd.merge_asof(
        df_main.sort_values('world_timestamp_dt'),
        df_pupil[['pupil_timestamp_dt', PUPIL_COL_NAME]].sort_values('pupil_timestamp_dt'),
        left_on='world_timestamp_dt',
        right_on='pupil_timestamp_dt',
        direction='nearest',
        tolerance=pd.Timedelta('100ms')
    )
    return merged_df

def generate_gaze_heatmap(df_gaze, width, height, output_path):
    """Genera una heatmap delle posizioni dello sguardo."""
    if df_gaze[['gaze_x_norm', 'gaze_y_norm']].isnull().all().all():
        return
    plt.figure(figsize=(width/100, height/100))
    sns.kdeplot(
        x=df_gaze['gaze_x_norm'] * width,
        y=df_gaze['gaze_y_norm'] * height,
        fill=True, cmap="rocket", thresh=0.05,
    )
    plt.title(f"Heatmap Sguardo - {os.path.basename(output_path)}")
    plt.xlim(0, width)
    plt.ylim(height, 0)
    plt.savefig(output_path, dpi=150)
    plt.close()

def generate_pupillometry_plot(df_trials, pupil_col, output_path):
    """Genera un grafico della variazione pupillare media per trial."""
    if pupil_col not in df_trials.columns or df_trials[pupil_col].isnull().all():
        return
        
    df_trials = df_trials.dropna(subset=[pupil_col, 'trial_id'])
    if df_trials.empty:
        return

    # Normalizzazione temporale per ogni trial
    normalized_trials = []
    for trial_id in df_trials['trial_id'].unique():
        trial_data = df_trials[df_trials['trial_id'] == trial_id].copy()
        trial_data['time_norm'] = np.linspace(0, 1, len(trial_data))
        normalized_trials.append(trial_data)
    
    if not normalized_trials:
        return
        
    df_norm = pd.concat(normalized_trials)
    
    plt.figure()
    sns.lineplot(data=df_norm, x='time_norm', y=pupil_col, ci='sd')
    plt.title(f"Andamento Pupillare Medio per Trial - {os.path.basename(output_path)}")
    plt.xlabel("Tempo Normalizzato del Trial")
    plt.ylabel("Diametro Pupillare Medio (mm)")
    plt.grid(True)
    plt.savefig(output_path)
    plt.close()

def validate_movement_sequence(df, seq, name):
    """Verifica che la sequenza di movimenti rilevata corrisponda a quella attesa."""
    if not seq: return
    detected_seq = df.drop_duplicates('trial_id')['direction_simple'].tolist()
    print(f"\nINFO: Validazione sequenza per segmento '{name}':")
    print(f"  - Sequenza Attesa  ({len(seq)}): {seq}")
    print(f"  - Sequenza Rilevata ({len(detected_seq)}): {detected_seq}")
    if detected_seq != seq[:len(detected_seq)]:
        print("  - ⚠️ ATTENZIONE: La sequenza rilevata non corrisponde a quella attesa.")
    else:
        print("  - ✅ La sequenza rilevata corrisponde a quella attesa.")

# In generate_report.py


def generate_fragmentation_plots(df_main, df_cuts, output_dir):
    """
    Genera grafici della frammentazione dello sguardo, evidenziando i periodi di ogni trial.
    """
    print("\nINFO: Avvio generazione grafici 'Frammentazione' con trigger degli eventi...")
    sns.set_theme(style="whitegrid")
    
    # --- CORREZIONE QUI ---
    # Convertiamo i colori in un formato (tupla di float) che Matplotlib capisce.
    # (R/255, G/255, B/255, Alpha)
    direction_colors = {
        'up':    (1.0, 0.70, 0.73, 0.3), # Rosa pastello
        'down':  (0.73, 0.88, 1.0, 0.3),  # Azzurro pastello
        'left':  (0.73, 1.0, 0.79, 0.3),  # Verde pastello
        'right': (1.0, 0.87, 0.73, 0.3)  # Arancione pastello
    }

    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        start_frame, end_frame = cut_row['start_frame'], cut_row['end_frame']
        
        df_segment = df_main[(df_main['frame'] >= start_frame) & (df_main['frame'] <= end_frame)].copy()
        
        if df_segment.empty or df_segment['gaze_speed'].isnull().all():
            continue

        plt.figure(figsize=(16, 7))
        
        sns.lineplot(data=df_segment, x='frame', y='gaze_speed', lw=1, label='Velocità Sguardo', zorder=2)
        
        trials_in_segment = df_segment[df_segment['trial_id'] > 0].groupby('trial_id')
        handled_directions_legend = set()

        for trial_id, trial_df in trials_in_segment:
            if trial_df.empty:
                continue
                
            trial_start_frame = trial_df['frame'].min()
            trial_end_frame = trial_df['frame'].max()
            direction = trial_df['direction_simple'].iloc[0]
            
            color = direction_colors.get(direction, (0.78, 0.78, 0.78, 0.3)) # Grigio per default
            label = f'Trial ({direction})' if direction not in handled_directions_legend else None
            
            plt.axvspan(trial_start_frame, trial_end_frame, color=color, label=label, zorder=1)
            handled_directions_legend.add(direction)

        plt.title(f"Frammentazione Sguardo con Eventi - Segmento '{segment_name}'", fontsize=16)
        plt.xlabel("Frame Video", fontsize=12)
        plt.ylabel("Velocità Sguardo (distanza/frame)", fontsize=12)
        plt.xlim(df_segment['frame'].min(), df_segment['frame'].max())
        
        if handled_directions_legend:
            plt.legend()
        
        plot_path = os.path.join(output_dir, f"fragmentation_plot_with_events_{segment_name}.png")
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  - Grafico di frammentazione con eventi salvato in: {plot_path}")

def calculate_excursion(df_input, success_threshold):
    """
    Calcola la percentuale di completamento della traiettoria per ogni trial.
    Aggiunge le colonne 'excursion_perc_frames' e 'excursion_success'.
    """
    print("\nINFO: Avvio calcolo metrica 'Escursione' (completamento traiettoria)...")
    
    if 'trial_id' not in df_input.columns or df_input[df_input['trial_id'] > 0].empty:
        print("  - ATTENZIONE: Nessun trial valido trovato per il calcolo dell'escursione.")
        df_input['excursion_perc_frames'] = 0.0
        df_input['excursion_success'] = False
        return df_input

    # Calcola la percentuale di 'gaze_in_box' per ogni trial
    df_trials_only = df_input[df_input['trial_id'] > 0].copy()
    excursion_data = df_trials_only.groupby('trial_id')['gaze_in_box'].mean().reset_index()
    excursion_data.rename(columns={'gaze_in_box': 'excursion_perc_frames'}, inplace=True)
    
    # Definisce il successo se la percentuale supera una soglia (es. 80%)
    excursion_data['excursion_success'] = excursion_data['excursion_perc_frames'] >= success_threshold
    
    # Unisce i risultati al dataframe principale
    df_output = df_input.merge(excursion_data, on='trial_id', how='left')
    
    print(f"  - ✅ Calcolo 'Escursione' completato per {len(excursion_data)} trial.")
    return df_output

def calculate_running_gaze_in_box_percentage(df_input):
    """Calcola la percentuale progressiva di gaze_in_box per ogni trial."""
    if 'trial_id' not in df_input.columns: return df_input
    
    df_input['running_gaze_in_box_perc'] = df_input.groupby('trial_id')['gaze_in_box'].transform(
        lambda x: (x.cumsum() / (np.arange(len(x)) + 1)) * 100
    )
    return df_input

def calculate_directional_excursion(df_input, margin_perc):
    """
    Calcola se lo sguardo ha superato la massima escursione della palla per ogni trial,
    considerando un margine di tolleranza.
    Aggiunge le colonne 'directional_excursion_reached' e 'directional_excursion_success'.
    """
    print("\nINFO: Avvio calcolo metrica 'Escursione Direzionale' (dinamica su escursione palla)...")
    
    if 'trial_id' not in df_input.columns or df_input[df_input['trial_id'] > 0].empty:
        print("  - ATTENZIONE: Nessun trial valido trovato per il calcolo dell'escursione direzionale.")
        df_input['directional_excursion_reached'] = 0.0
        df_input['directional_excursion_success'] = False
        return df_input
    
    df_trials_only = df_input[df_input['trial_id'] > 0].copy()
    
    # Aggiungiamo colonne per la linea di escursione
    df_input['dir_ex_line_coord'] = np.nan

    # Funzione che verrà applicata a ogni gruppo (trial)
    def check_reach(group):
        direction = group['direction_simple'].iloc[0]
        
        if direction == 'up':
            # Trova il punto più alto raggiunto dalla palla
            idx_min = group['ball_center_y_norm'].idxmin()
            ball_top_edge = group.loc[idx_min, 'ball_center_y_norm'] - (group.loc[idx_min, 'ball_h_norm'] / 2)
            # La soglia è il bordo superiore della palla + un margine verso il centro
            threshold_line_norm = ball_top_edge + margin_perc
            # Salva la coordinata della linea per il frame di massima escursione
            group.loc[idx_min, 'dir_ex_line_coord'] = threshold_line_norm * group['frame_height'].iloc[0]
            return (group['gaze_y_norm'] <= threshold_line_norm).any()
            
        elif direction == 'down':
            idx_max = group['ball_center_y_norm'].idxmax()
            ball_bottom_edge = group.loc[idx_max, 'ball_center_y_norm'] + (group.loc[idx_max, 'ball_h_norm'] / 2)
            threshold_line_norm = ball_bottom_edge - margin_perc
            group.loc[idx_max, 'dir_ex_line_coord'] = threshold_line_norm * group['frame_height'].iloc[0]
            return (group['gaze_y_norm'] >= threshold_line_norm).any()

        elif direction == 'left':
            idx_min = group['ball_center_x_norm'].idxmin()
            ball_left_edge = group.loc[idx_min, 'ball_center_x_norm'] - (group.loc[idx_min, 'ball_w_norm'] / 2)
            threshold_line_norm = ball_left_edge + margin_perc
            group.loc[idx_min, 'dir_ex_line_coord'] = threshold_line_norm * group['frame_width'].iloc[0]
            return (group['gaze_x_norm'] <= threshold_line_norm).any()

        elif direction == 'right':
            idx_max = group['ball_center_x_norm'].idxmax()
            ball_right_edge = group.loc[idx_max, 'ball_center_x_norm'] + (group.loc[idx_max, 'ball_w_norm'] / 2)
            threshold_line_norm = ball_right_edge - margin_perc
            group.loc[idx_max, 'dir_ex_line_coord'] = threshold_line_norm * group['frame_width'].iloc[0]
            return (group['gaze_x_norm'] >= threshold_line_norm).any()
            
        return False

    # Applica la funzione e ottieni i successi e le linee
    results = df_trials_only.groupby('trial_id').apply(check_reach)
    dir_excursion_data = results.reset_index(name='directional_excursion_success')
    dir_excursion_data['directional_excursion_reached'] = dir_excursion_data['directional_excursion_success'].astype(float)

    df_output = df_input.merge(dir_excursion_data, on='trial_id', how='left')
    print(f"  - ✅ Calcolo 'Escursione Direzionale' completato per {len(dir_excursion_data)} trial.")
    return df_output

def main(args):
    analysis_path = os.path.join(args.analysis_dir, 'output_final_analysis_analysis.csv')
    cuts_path = os.path.join(args.analysis_dir, 'cut_points.csv')
    df_main = pd.read_csv(analysis_path)

    # Aggiungi dimensioni del frame per calcoli futuri
    w, h = get_video_dimensions(os.path.join(args.input_dir_for_pupil, 'video.mp4'))
    df_main['frame_width'] = w
    df_main['frame_height'] = h

    # --- CORREZIONE: Unisci i dati dei segmenti al dataframe principale ---
    df_cuts = pd.read_csv(cuts_path)
    df_main['segment_name'] = ''
    for _, row in df_cuts.iterrows():
        df_main.loc[(df_main['frame'] >= row['start_frame']) & (df_main['frame'] <= row['end_frame']), 'segment_name'] = row['segment_name']
    df_cuts = pd.read_csv(cuts_path)

    if hasattr(args, 'manual_events_path') and args.manual_events_path and os.path.exists(args.manual_events_path):
        df_main = load_manual_events(df_main, args.manual_events_path)
    else:
        if hasattr(args, 'manual_events_path') and args.manual_events_path:
             print(f"ATTENZIONE: File eventi manuali non trovato in '{args.manual_events_path}'. Eseguo calcolo automatico.")
        df_main = calculate_movement_data(df_main)
    
    df_main = add_pupil_data(df_main, args.input_dir_for_pupil)

    plot_dir = os.path.join(args.output_dir, "plots_and_heatmaps")
    os.makedirs(plot_dir, exist_ok=True)
    writer = pd.ExcelWriter(os.path.join(args.output_dir, 'final_report.xlsx'), engine='xlsxwriter')

    expected_sequences = {'fast': ['right','left','right','up','down','up']*3, 'slow': ['right','left','right','up','down','up','down','up','right','left','right','up','down','up','down','right','left','right','up','down']}
    
    # --- NUOVO: Calcola le metriche sull'intero dataframe prima di splittare ---
    if args.run_excursion_analysis:
        print("\nINFO: Calcolo delle metriche di escursione richiesto.")
        # Calcola le metriche e le unisce al dataframe principale
        df_excursion = calculate_excursion(df_main.copy(), args.excursion_success_threshold)
        df_directional = calculate_directional_excursion(df_main.copy(), args.directional_excursion_edge_threshold)

        # Unisci i risultati usando 'trial_id' come chiave
        df_main = df_main.merge(df_excursion[['trial_id', 'excursion_perc_frames', 'excursion_success']].dropna(subset=['trial_id']).drop_duplicates('trial_id'), on='trial_id', how='left')
        df_main = df_main.merge(df_directional[['trial_id', 'dir_ex_line_coord', 'directional_excursion_reached', 'directional_excursion_success']].dropna(subset=['trial_id']).drop_duplicates('trial_id'), on='trial_id', how='left')

        # Calcola la percentuale di inseguimento progressiva per i video
        df_main = calculate_running_gaze_in_box_percentage(df_main)

    general_summary_list = []

    # Esegui l'analisi di frammentazione sull'intero dataset, se richiesto
    if args.run_fragmentation_analysis:
        generate_fragmentation_plots(df_main, df_cuts, plot_dir)
        
    for _, cut_row in df_cuts.iterrows():
        segment_name = cut_row['segment_name']
        df_segment = df_main[(df_main['frame'] >= cut_row['start_frame']) & (df_main['frame'] <= cut_row['end_frame'])].copy()
        
        if df_segment.empty: continue
        df_center_out = df_segment[df_segment['trial_id'] > 0].copy()
        if df_center_out.empty:
            print(f"INFO: Nessun trial valido trovato nel segmento '{segment_name}'.")
            continue

        if not (hasattr(args, 'manual_events_path') and args.manual_events_path and os.path.exists(args.manual_events_path)):
            validate_movement_sequence(df_center_out, expected_sequences.get(segment_name, []), segment_name)

        # Aggiorna i dataframe di segmento e trial con le nuove colonne (se calcolate)
        df_segment = df_main[(df_main['frame'] >= cut_row['start_frame']) & (df_main['frame'] <= cut_row['end_frame'])].copy()
        df_center_out = df_segment[df_segment['trial_id'] > 0].copy()

        # Dizionario per aggregare i dati
        agg_dict = {
            'avg_gaze_in_box_perc': ('gaze_in_box', 'mean'),
            'avg_gaze_speed': ('gaze_speed', 'mean'),
            'trial_count': ('trial_id', 'nunique')
        }
        if PUPIL_COL_NAME in df_center_out and df_center_out[PUPIL_COL_NAME].notna().any():
            agg_dict['avg_pupil_diameter'] = (PUPIL_COL_NAME, 'mean')
        
        # Aggiungi le metriche di escursione al dizionario se presenti
        if 'excursion_success' in df_center_out.columns:
            agg_dict['excursion_success_perc'] = ('excursion_success', 'mean')
        if 'excursion_perc_frames' in df_center_out.columns:
            agg_dict['avg_excursion_perc_frames'] = ('excursion_perc_frames', 'mean')
        if 'directional_excursion_success' in df_center_out.columns:
            agg_dict['directional_excursion_success_perc'] = ('directional_excursion_success', 'mean')
        if 'directional_excursion_reached' in df_center_out.columns:
            agg_dict['avg_directional_excursion_reached'] = ('directional_excursion_reached', 'mean')

        summary = df_center_out.groupby('direction_simple').agg(**agg_dict).reset_index()
        summary['avg_gaze_in_box_perc'] *= 100
        if 'directional_excursion_success_perc' in summary: summary['directional_excursion_success_perc'] *= 100
        if 'excursion_success_perc' in summary: summary['excursion_success_perc'] *= 100

        summary.to_excel(writer, sheet_name=f"Riepilogo_{segment_name}", index=False)
        df_center_out.to_excel(writer, sheet_name=f"Dettagli_{segment_name}", index=False)

        gen_sum = {
            'segmento': segment_name,
            'gaze_in_box_perc_totale': df_center_out['gaze_in_box'].mean() * 100,
            'velocita_sguardo_media': df_center_out['gaze_speed'].mean(),
            'numero_trial_validi': df_center_out['trial_id'].nunique()
        }
        if PUPIL_COL_NAME in df_center_out and df_center_out[PUPIL_COL_NAME].notna().any():
            gen_sum['diametro_pupillare_medio'] = df_center_out[PUPIL_COL_NAME].mean()
        if 'excursion_success' in df_center_out.columns:
            gen_sum['escursione_successo_perc'] = df_center_out['excursion_success'].mean() * 100
            gen_sum['escursione_perc_frames_media'] = df_center_out['excursion_perc_frames'].mean()
        if 'directional_excursion_success' in df_center_out.columns:
            gen_sum['escursione_direzionale_successo_perc'] = df_center_out['directional_excursion_success'].mean() * 100
            gen_sum['escursione_direzionale_raggiunta_perc_media'] = df_center_out['directional_excursion_reached'].mean()
        general_summary_list.append(gen_sum)

        for direction in summary['direction_simple'].unique():
            df_dir = df_center_out[df_center_out['direction_simple'] == direction]
            generate_gaze_heatmap(df_dir, w, h, os.path.join(plot_dir, f"heatmap_{segment_name}_{direction}.png"))
            if PUPIL_COL_NAME in df_dir.columns and df_dir[PUPIL_COL_NAME].notna().any():
                generate_pupillometry_plot(df_dir, PUPIL_COL_NAME, os.path.join(plot_dir, f"pupillometry_{segment_name}_{direction}.png"))

    if general_summary_list:
        pd.DataFrame(general_summary_list).to_excel(writer, sheet_name="Riepilogo_Generale", index=False)
    
    writer.close()

    # --- NUOVO: Salva il dataframe completo di metriche per la generazione video ---
    final_csv_path = os.path.join(args.output_dir, 'output_final_analysis_with_metrics.csv')
    df_main.to_csv(final_csv_path, index=False)
    print(f"\nINFO: Dati di analisi completi con metriche salvati in '{final_csv_path}'")

    print("\nINFO: Report Excel 'final_report.xlsx' generato con successo.")