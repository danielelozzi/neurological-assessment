import os
import cv2
import numpy as np
import pandas as pd

"""
================================================================
SCRIPT PER LA GENERAZIONE DI DATI SINTETICI
================================================================

Obiettivo:
Creare un set di dati completo e controllato per testare la pipeline di analisi.
Questo script genera:
1. Un video (.mp4) con una palla che si muove e testi "FAST"/"SLOW".
2. I file CSV necessari per l'analisi (gaze, pupil, timestamps, surface).
3. Un file template a tempi fissi (.csv) che descrive esattamente gli eventi nel video.
4. Un report Excel (.xlsx) con i risultati attesi, per confrontarlo con l'output del software.

Come usarlo:
1. Esegui questo script.
2. Verrà creata una cartella 'synthetic_data'.
3. Nella GUI del software di analisi:
   - Seleziona 'synthetic_data/input' come cartella di Input.
   - Seleziona una cartella di output a tua scelta (es. 'synthetic_data/analysis_output').
   - Clicca su "Carica Template a Tempi Fissi" e seleziona 'synthetic_data/input/template_tempi_fissi.csv'.
   - Quando richiesto, inserisci il frame di ONSET, che per questo script è sempre 150.
   - Avvia l'analisi completa.
4. Confronta il 'final_report.xlsx' generato con 'synthetic_data/expected_output/report_atteso.xlsx'.
   I valori dovrebbero essere identici o molto simili.
"""

# --- CONFIGURAZIONE ---

# Parametri Video
WIDTH, HEIGHT = 1280, 720
FPS = 30
VIDEO_DURATION_S = 120  # Durata totale del video in secondi

# Parametri Palla
BALL_RADIUS = 30
BALL_COLOR = (255, 0, 255)  # Magenta

# Parametri di temporizzazione (in frame)
ONSET_FRAME = 150  # Frame di inizio del segmento FAST (il nostro "zero" relativo)

# Durate dei segmenti
FAST_SEGMENT_DURATION_FRAMES = 32 * FPS
SLOW_SEGMENT_DURATION_FRAMES = 70 * FPS

# Pausa tra i segmenti
PAUSE_BETWEEN_SEGMENTS_FRAMES = 7 * FPS

# Calcolo dei punti chiave assoluti
FAST_START_FRAME = ONSET_FRAME
FAST_END_FRAME = FAST_START_FRAME + FAST_SEGMENT_DURATION_FRAMES
SLOW_START_FRAME = FAST_END_FRAME + PAUSE_BETWEEN_SEGMENTS_FRAMES
SLOW_END_FRAME = SLOW_START_FRAME + SLOW_SEGMENT_DURATION_FRAMES

# Testo OCR
FAST_TEXT_FRAME_START = ONSET_FRAME - (5 * FPS) # Il testo "1" appare 5 secondi prima
FAST_TEXT_FRAME_END = ONSET_FRAME # e scompare all'onset

# Parametri di movimento
TRIAL_DURATION_FRAMES = 2 * FPS  # 2 secondi per movimento
TRIAL_PAUSE_FRAMES = 1 * FPS     # 1 secondo di pausa

# Posizioni target (normalizzate)
CENTER_POS = np.array([0.5, 0.5])
RIGHT_POS = np.array([0.85, 0.5])
LEFT_POS = np.array([0.15, 0.5])
UP_POS = np.array([0.5, 0.15])
DOWN_POS = np.array([0.5, 0.85])

DIRECTIONS = {
    "right": (CENTER_POS, RIGHT_POS),
    "left": (CENTER_POS, LEFT_POS),
    "up": (CENTER_POS, UP_POS),
    "down": (CENTER_POS, DOWN_POS),
}

# Sequenza dei trial
TRIAL_SEQUENCE = ['right', 'left', 'up', 'down'] * 15 # Sequenza ripetuta

# Parametri Dati Sintetici
PERFECT_GAZE = True  # Se True, lo sguardo segue la palla perfettamente. Se False, aggiunge rumore.
GAZE_NOISE_STD_DEV = 0.01 # Deviazione standard del rumore dello sguardo (se PERFECT_GAZE=False)

# Cartelle di output
BASE_DIR = "synthetic_data"
INPUT_DIR = os.path.join(BASE_DIR, "input")
EXPECTED_OUTPUT_DIR = os.path.join(BASE_DIR, "expected_output")


def draw_text(frame, text, position, font_scale=2, color=(255, 255, 255), thickness=3):
    """Disegna testo centrato sul frame."""
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = (frame.shape[0] + text_size[1]) // 2
    cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness)


def generate_data():
    """Funzione principale che genera tutti i file sintetici."""
    print("--- Avvio generazione dati sintetici ---")
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(EXPECTED_OUTPUT_DIR, exist_ok=True)

    # --- 1. Preparazione Video e Dati Frame per Frame ---
    video_path = os.path.join(INPUT_DIR, "video.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, FPS, (WIDTH, HEIGHT))

    total_frames = VIDEO_DURATION_S * FPS
    ball_pos_norm = np.array(CENTER_POS)

    # Liste per i dati CSV
    world_timestamps_data = []
    surface_positions_data = []
    gaze_data = []
    eye_states_data = []
    template_events = []
    
    # Aggiungiamo i segmenti al template
    template_events.append(['segment', 'fast', 0, FAST_SEGMENT_DURATION_FRAMES])
    template_events.append(['segment', 'slow', SLOW_START_FRAME - ONSET_FRAME, SLOW_END_FRAME - ONSET_FRAME])

    current_trial_idx = 0
    frame_in_trial = -1

    print("Generazione video e dati frame per frame...")
    for i in range(total_frames):
        frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
        timestamp_ns = i * (10**9 // FPS)

        # Gestione movimento palla e trial
        is_in_fast_segment = FAST_START_FRAME <= i < FAST_END_FRAME
        is_in_slow_segment = SLOW_START_FRAME <= i < SLOW_END_FRAME

        if is_in_fast_segment or is_in_slow_segment:
            if frame_in_trial == -1: # Inizio di una pausa o del primo trial
                frame_in_trial = 0
                
                # Calcolo start/end del prossimo trial
                trial_start_abs = i
                trial_end_abs = trial_start_abs + TRIAL_DURATION_FRAMES
                
                # Aggiungi al template
                direction = TRIAL_SEQUENCE[current_trial_idx]
                segment_name = 'fast' if is_in_fast_segment else 'slow'
                
                # Solo se il trial finisce dentro il segmento
                if (is_in_fast_segment and trial_end_abs < FAST_END_FRAME) or \
                   (is_in_slow_segment and trial_end_abs < SLOW_END_FRAME):
                    
                    template_events.append([
                        'trial',
                        direction,
                        trial_start_abs - ONSET_FRAME,
                        trial_end_abs - ONSET_FRAME
                    ])

            if 0 <= frame_in_trial < TRIAL_DURATION_FRAMES: # Siamo in un trial
                direction = TRIAL_SEQUENCE[current_trial_idx]
                start_pos, end_pos = DIRECTIONS[direction]
                
                # Interpolazione lineare
                progress = frame_in_trial / (TRIAL_DURATION_FRAMES - 1)
                ball_pos_norm = start_pos + (end_pos - start_pos) * progress

            else: # Siamo in pausa tra i trial
                ball_pos_norm = np.array(CENTER_POS)

            # Avanzamento contatori
            frame_in_trial += 1
            if frame_in_trial >= TRIAL_DURATION_FRAMES + TRIAL_PAUSE_FRAMES:
                frame_in_trial = -1 # Fine ciclo trial+pausa
                current_trial_idx += 1

        else: # Non siamo in nessun segmento
            ball_pos_norm = np.array(CENTER_POS)
            frame_in_trial = -1

        # Disegna la palla
        ball_pos_px = (int(ball_pos_norm[0] * WIDTH), int(ball_pos_norm[1] * HEIGHT))
        cv2.circle(frame, ball_pos_px, BALL_RADIUS, BALL_COLOR, -1)

        # Disegna testo OCR
        if FAST_TEXT_FRAME_START <= i < FAST_TEXT_FRAME_END:
            draw_text(frame, "1", (WIDTH // 2, HEIGHT // 2))

        out.write(frame)

        # --- Popola dati per CSV ---
        world_timestamps_data.append({'world_index': i, 'timestamp [ns]': timestamp_ns})
        
        # Superficie statica (tutto lo schermo)
        surface_positions_data.append({
            'world_index': i, 'surface_name': 'screen',
            'tl x [px]': 0, 'tl y [px]': 0,
            'tr x [px]': WIDTH, 'tr y [px]': 0,
            'br x [px]': WIDTH, 'br y [px]': HEIGHT,
            'bl x [px]': 0, 'bl y [px]': HEIGHT,
        })

        # Dati di sguardo
        gaze_x, gaze_y = ball_pos_norm
        if not PERFECT_GAZE:
            gaze_x += np.random.normal(0, GAZE_NOISE_STD_DEV)
            gaze_y += np.random.normal(0, GAZE_NOISE_STD_DEV)
        
        gaze_data.append({
            'timestamp [ns]': timestamp_ns,
            'gaze detected on surface': True,
            'gaze position on surface x [normalized]': gaze_x,
            'gaze position on surface y [normalized]': gaze_y,
        })

        # Dati pupillari per 3d_eye_states.csv (rumore casuale)
        pupil_diameter_left = 3.5 + np.random.normal(0, 0.1)
        pupil_diameter_right = 3.55 + np.random.normal(0, 0.1) # Leggermente diverso
        eye_states_data.append({
            'timestamp [ns]': timestamp_ns,
            'pupil diameter left [mm]': pupil_diameter_left,
            'pupil diameter right [mm]': pupil_diameter_right
        })

    out.release()
    print(f"Video '{video_path}' generato.")

    # --- 2. Salvataggio file CSV ---
    print("Salvataggio file CSV...")
    pd.DataFrame(world_timestamps_data).to_csv(os.path.join(INPUT_DIR, 'world_timestamps.csv'), index=False)
    pd.DataFrame(surface_positions_data).to_csv(os.path.join(INPUT_DIR, 'surface_positions.csv'), index=False)
    pd.DataFrame(gaze_data).to_csv(os.path.join(INPUT_DIR, 'gaze.csv'), index=False)
    pd.DataFrame(eye_states_data).to_csv(os.path.join(INPUT_DIR, '3d_eye_states.csv'), index=False)
    
    df_template = pd.DataFrame(template_events, columns=['event_type', 'direction', 'relative_start', 'relative_end'])
    template_path = os.path.join(INPUT_DIR, 'template_tempi_fissi.csv')
    df_template.to_csv(template_path, index=False)
    print(f"File CSV e template '{os.path.basename(template_path)}' salvati in '{INPUT_DIR}'.")

    # --- 3. Generazione Report Atteso ---
    print("Generazione report con i risultati attesi...")
    
    # Calcola il numero di trial per segmento
    df_template_trials = df_template[df_template['event_type'] == 'trial'].copy()
    df_template_trials['segment'] = np.where(df_template_trials['relative_start'] < FAST_SEGMENT_DURATION_FRAMES, 'fast', 'slow')
    
    summary_by_dir_fast = df_template_trials[df_template_trials['segment'] == 'fast'].groupby('direction').size().reset_index(name='trial_count')
    summary_by_dir_slow = df_template_trials[df_template_trials['segment'] == 'slow'].groupby('direction').size().reset_index(name='trial_count')

    # Per il soggetto perfetto, molte metriche sono costanti
    gaze_in_box_perc = 100.0 if PERFECT_GAZE else np.nan # Non possiamo prevederlo con rumore
    excursion_success_perc = 100.0 if PERFECT_GAZE else np.nan
    directional_excursion_success_perc = 100.0 if PERFECT_GAZE else np.nan

    # Riepilogo per direzione
    for df_sum in [summary_by_dir_fast, summary_by_dir_slow]:
        df_sum.rename(columns={'direction': 'direction_simple'}, inplace=True)
        df_sum['avg_gaze_in_box_perc'] = gaze_in_box_perc
        df_sum['avg_gaze_speed'] = np.nan # Troppo complesso da calcolare a priori
        df_sum['avg_pupil_diameter'] = np.nan # Casuale
        df_sum['excursion_success_perc'] = excursion_success_perc
        df_sum['avg_excursion_perc_frames'] = 1.0 if PERFECT_GAZE else np.nan
        df_sum['directional_excursion_success_perc'] = directional_excursion_success_perc
        df_sum['avg_directional_excursion_reached'] = 1.0 if PERFECT_GAZE else np.nan

    # Riepilogo generale
    general_summary_data = [
        {
            'segmento': 'fast',
            'gaze_in_box_perc_totale': gaze_in_box_perc,
            'velocita_sguardo_media': np.nan,
            'numero_trial_validi': summary_by_dir_fast['trial_count'].sum(),
            'diametro_pupillare_medio': np.nan,
            'escursione_successo_perc': excursion_success_perc,
            'escursione_perc_frames_media': 1.0 if PERFECT_GAZE else np.nan,
            'escursione_direzionale_successo_perc': directional_excursion_success_perc,
            'escursione_direzionale_raggiunta_perc_media': 1.0 if PERFECT_GAZE else np.nan
        },
        {
            'segmento': 'slow',
            'gaze_in_box_perc_totale': gaze_in_box_perc,
            'velocita_sguardo_media': np.nan,
            'numero_trial_validi': summary_by_dir_slow['trial_count'].sum(),
            'diametro_pupillare_medio': np.nan,
            'escursione_successo_perc': excursion_success_perc,
            'escursione_perc_frames_media': 1.0 if PERFECT_GAZE else np.nan,
            'escursione_direzionale_successo_perc': directional_excursion_success_perc,
            'escursione_direzionale_raggiunta_perc_media': 1.0 if PERFECT_GAZE else np.nan
        }
    ]
    df_general_summary = pd.DataFrame(general_summary_data)

    # Scrittura del file Excel
    expected_report_path = os.path.join(EXPECTED_OUTPUT_DIR, "report_atteso.xlsx")
    with pd.ExcelWriter(expected_report_path, engine='xlsxwriter') as writer:
        df_general_summary.to_excel(writer, sheet_name="Riepilogo_Generale", index=False)
        summary_by_dir_fast.to_excel(writer, sheet_name="Riepilogo_fast", index=False)
        summary_by_dir_slow.to_excel(writer, sheet_name="Riepilogo_slow", index=False)
        # I fogli di dettaglio sono omessi perché troppo complessi da replicare

    print(f"Report atteso salvato in '{expected_report_path}'.")
    print("\n--- Generazione completata con successo! ---")

if __name__ == "__main__":
    generate_data()