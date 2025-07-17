# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

### LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)

* **Sito Web Lab**: [labscoc.wordpress.com](https://labscoc.wordpress.com/)

* **Repository GitHub**: [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo. L'intero processo è gestito da un'unica **interfaccia grafica (GUI)** che orchestra l'elaborazione dei dati, dal taglio dei video grezzi fino alla generazione di un report statistico e visuale completo.

## 🎯 Obiettivo del Software

L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Partendo dai dati grezzi, il software esegue i seguenti passaggi:

1. **Identifica i Segmenti di Test**: Utilizzando OCR, individua automaticamente i segmenti "fast" e "slow".

2. **Corregge la Prospettiva**: Applica una correzione basata su AprilTag, isolando l'area dello schermo.

3. **Rileva e Sincronizza**: Rileva il cerchio, tracciandone il movimento e sincronizzando i dati di sguardo e pupilla.

4. **Analizza e Visualizza**: Calcola metriche chiave (velocità, tempo sul target, diametro pupillare), esegue validazioni e scrive in sovrimpressione la direzione del movimento sui video finali.

5. **Genera l'Output**: Produce video, un report Excel dettagliato e grafici, incluse le analisi opzionali.

## 📋 Prerequisiti

È necessario acquisire i dati con **Pupil Labs Neon**, usare gli **AprilTag** e processare la registrazione su **Pupil Cloud** con l'enrichment **Marker Mapper**. La cartella scaricata da Pupil Cloud deve contenere:

* `video.mp4`

* `gaze.csv`

* `world_timestamps.csv`

* `surface_positions.csv`

* **(Opzionale)** `3d_eye_states.csv` per l'analisi pupillometrica.

## 🛠️ Installazione

È fortemente consigliato creare un ambiente virtuale.


1. Crea e attiva l'ambiente virtuale
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate

2. Installa le librerie
pip install customtkinter opencv-python pandas numpy matplotlib seaborn scipy easyocr ultralytics xlsxwriter


## 🚀 Utilizzo

1. **Avvia la GUI**: `python main_gui.py`

2. **Configura l'Analisi**:

   * **1. Cartella Input**: Scegli la cartella dati di Pupil Cloud.

   * **2. Cartella Output**: Scegli dove salvare i risultati.

   * **3. Metodo di Rilevamento**: YOLO (raccomandato) o Hough Circle.

   * **4. Modello YOLO**: Se necessario, carica il file del modello `.pt`.

   * **5. Analisi Aggiuntive**: Seleziona le caselle per attivare le analisi opzionali di **Frammentazione** e/o **Escursione**.

3. **Avvia l'Analisi** con il pulsante principale.

## 📊 Output del Progetto

* **`final_report.xlsx`**: Report Excel con metriche dettagliate e di riepilogo. Se attivata, include la colonna `excursion_success` (True/False) nei fogli di dettaglio e la percentuale di successo (`excursion_success_perc`) nei riepiloghi.

* **`final_video_fast.mp4` / `final_video_slow.mp4`**: Video finali con overlay dello sguardo e della direzione del movimento.

* **`output_final_analysis_analysis.csv`**: Dati grezzi calcolati, frame per frame.

* **`cut_points.csv`**: Frame di inizio/fine dei segmenti, calcolati tramite OCR.

* **Cartella `plots_and_heatmaps/`**: Contiene le visualizzazioni grafiche:

  * **Heatmap** dello sguardo.

  * Grafici dell'andamento della **pupillometria**.

  * **(Opzionale) Analisi di Frammentazione**: Grafici (`fragmentation_plot_*.png`) che mostrano la distanza euclidea tra sguardi consecutivi, un indicatore della fluidità del movimento.

  * **(Opzionale) Analisi di Escursione**: Una metrica nel report Excel che indica se lo sguardo ha raggiunto la zona target finale per ogni movimento, misurando il completamento della traiettoria.
