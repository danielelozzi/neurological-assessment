# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

**LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)**  
**Sito Web Lab:** [labscoc.wordpress.com](https://labscoc.wordpress.com)

**Repository GitHub:** [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)  
**Concettualizzazione:** Dr. Massimo Marano

---

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo. L'intero processo è gestito da un'unica interfaccia grafica (GUI) che orchestra l'elaborazione dei dati.

## 🎯 Obiettivo del Software
L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Il software offre diverse modalità di lavoro per massima flessibilità, da quella completamente automatica a quella interamente manuale e interattiva.

## 🚀 Modalità di Lavoro

### 1. Modalità Automatica (Default)
Questa è la modalità standard. Il software esegue l'intera pipeline con il minimo intervento manuale:

- **Identifica i Segmenti di Test**: Utilizzando OCR, individua automaticamente l'inizio dei segmenti "fast" e "slow".
- **Corregge la Prospettiva**: Isola l'area dello schermo tramite AprilTag.
- **Rileva e Sincronizza**: Rileva il cerchio (con YOLO o Hough), tracciandone il movimento e sincronizzando i dati di sguardo e pupilla.
- **Identifica gli Eventi**: Riconosce automaticamente l'inizio e la fine di ogni movimento della palla (destra, sinistra, ecc.).
- **Genera l'Output**: Produce video con overlay, un report Excel dettagliato e grafici.

> **NOTA SUL FALLBACK**: Se la ricerca automatica dei segmenti (fase 1) non riesce, il programma aprirà automaticamente una **finestra video interattiva** per permetterti di definire manualmente l'inizio dei segmenti "fast" e "slow".

### 2. Modalità Ibrida e Manuale
Per un controllo granulare, è possibile definire manualmente sia i segmenti che gli eventi di movimento direttamente dalla GUI, anche in modo combinato.

---

#### A. Definire i Segmenti (Fast/Slow)
Hai tre modi per definire i punti di inizio e fine dei segmenti principali.

* **Metodo 1: Interattivo (Consigliato)**
    * Clicca il pulsante **"Definisci Segmenti FAST/SLOW (Interattivo)"** sulla GUI.
    * Si aprirà un video player che ti permetterà di scorrere il video, trovare i punti esatti di inizio e fine per "fast" e "slow" e salvarli.
    * Una volta chiusa la finestra, i campi di testo nella GUI verranno compilati automaticamente.

* **Metodo 2: Testuale**
    * Attiva la checkbox **"Definisci Segmenti Manualmente (Testuale)"**.
    * Appariranno quattro campi per inserire i numeri di frame esatti di INIZIO e FINE per i segmenti.
    * Questa modalità salta completamente la ricerca automatica.

* **Metodo 3: Fallback Automatico**
    * Lascia tutte le opzioni manuali disattivate. Se la ricerca OCR automatica fallisce, il programma ti mostrerà automaticamente il selettore video interattivo, come descritto nel Metodo 1.

---

#### B. Definire gli Eventi di Movimento (Trial)
Hai due modi per specificare ogni singolo movimento (destra, sinistra, ecc.) all'interno dei segmenti.

* **Metodo 1: Interattivo (Consigliato)**
    * Clicca il pulsante **"Definisci Eventi UP/DOWN/LEFT/RIGHT (Interattivo)"**.
    * Si aprirà il video player. Potrai definire l'inizio e la fine di ogni trial, etichettandolo (es. "right", "left").
    * Al termine, il programma ti chiederà di **salvare le annotazioni in un file .csv**.
    * Il percorso di questo file verrà inserito automaticamente nella GUI, pronto per essere usato nell'analisi.

* **Metodo 2: Tramite File CSV**
    * Prepara un file `.csv` con le specifiche di ogni trial.
    * Attiva la checkbox **"Carica Eventi da File CSV"** e seleziona il tuo file.
    * Il programma salterà l'identificazione automatica dei movimenti e userà i dati del tuo file per generare il report.

##### Formato del file CSV per eventi manuali:
Il file deve contenere le seguenti colonne: `segment_name`, `direction_simple`, `start_frame`, `end_frame`.

- **segment_name**: `fast` o `slow`
- **direction_simple**: `right`, `left`, `up`, o `down`
- **start_frame**: Il numero del frame in cui inizia il movimento
- **end_frame**: Il numero del frame in cui termina il movimento

**Esempio (`miei_eventi.csv`)**:
```csv
segment_name,direction_simple,start_frame,end_frame
fast,right,5010,5090
fast,left,5150,5230
slow,right,10200,10350
```

---

## 📋 Prerequisiti
È necessario acquisire i dati con **Pupil Labs Neon**, usare gli **AprilTag** e processare la registrazione su **Pupil Cloud** con l'enrichment *Marker Mapper*. La cartella scaricata da Pupil Cloud deve contenere i file:

- `video.mp4`
- `gaze.csv`
- `world_timestamps.csv`
- `surface_positions.csv`

## 🛠️ Installazione

Crea un ambiente conda:
```bash
conda create --name cna-env python=3.10 -y
conda activate cna-env
```

Installa le librerie:
```bash
pip install -r requirements.txt
```

## 📊 Output del Progetto

- `final_report.xlsx`: Report Excel con metriche dettagliate e di riepilogo
- `final_video_fast.mp4` / `final_video_slow.mp4`: Video finali con overlay dei dati di sguardo
- `output_final_analysis_analysis.csv`: Dati grezzi calcolati, frame per frame
- `cut_points.csv`: Frame di inizio/fine dei segmenti (calcolati automaticamente o inseriti manualmente)
- Cartella `plots_and_heatmaps/`: Visualizzazioni grafiche (heatmap, grafici pupillometrici, ecc.)