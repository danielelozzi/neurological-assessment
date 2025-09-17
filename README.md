# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

**LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)**  
**Sito Web Lab:** [labscoc.wordpress.com](https://labscoc.wordpress.com)  
**PIs:** Prof. Giuseppe Curcio, Prof. Simone Migliore
**Concettualizzazione:** Dr. Massimo Marano  
**Codice:** Dr. Daniele Lozzi  

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

### A. Definire i Segmenti (Fast/Slow)
Hai tre modi per definire i punti di inizio e fine dei segmenti principali:

#### Metodo 1: Interattivo (Consigliato)
- Clicca il pulsante **"Definisci Segmenti FAST/SLOW (Interattivo)"** sulla GUI.
- Si aprirà un video player che ti permetterà di scorrere il video, trovare i punti esatti di inizio e fine per "fast" e "slow" e salvarli.
- Una volta chiusa la finestra, i campi di testo nella GUI verranno compilati automaticamente.

#### Metodo 2: Testuale
- Attiva la checkbox **"Definisci Segmenti Manualmente (Testuale)"**.
- Appariranno quattro campi per inserire i numeri di frame esatti di INIZIO e FINE per i segmenti.
- Questa modalità salta completamente la ricerca automatica.

#### Metodo 3: Fallback Automatico
- Lascia tutte le opzioni manuali disattivate. Se la ricerca OCR automatica fallisce, il programma ti mostrerà automaticamente il selettore video interattivo, come descritto nel Metodo 1.

---

### B. Definire gli Eventi di Movimento (Trial)
Hai tre modi per specificare ogni singolo movimento (destra, sinistra, ecc.) all'interno dei segmenti:

#### Metodo 1: Template a Tempi Fissi (Nuovo & Consigliato per Paradigmi Standard)
Questa modalità è la più potente e precisa per analizzare esperimenti che seguono una temporizzazione predefinita e ripetibile. Permette di saltare completamente la ricerca automatica e l'etichettatura manuale, garantendo massima coerenza tra le analisi.

**Come funziona:**
1.  **Crea il Template una Sola Volta**: Per un dato paradigma sperimentale, si crea un unico file CSV (es. `template_standard.csv`) che descrive la temporizzazione di tutti gli eventi. I tempi in questo file sono **relativi** a un punto "zero", che per convenzione è l'inizio del segmento `fast`.
2.  **Carica il Template**: Dalla GUI, clicca su **"Carica Template a Tempi Fissi..."** e seleziona il tuo file template.
3.  **Definisci l'Onset**: Questo è l'unico passaggio manuale richiesto. Il software ti chiederà di specificare a quale frame del video corrisponde il punto "zero" del template (l'**onset**). Puoi farlo in due modi:
    - **Inserisci Manualmente**: Digitando il numero esatto del frame.
    - **Seleziona da Video**: Usando un player interattivo per trovare e cliccare sul frame esatto.
4.  **Configurazione Automatica**: Una volta definito l'onset, il software esegue tutto in automatico:
    - **Calcola i Tempi Assoluti**: Somma il frame di onset a tutti i tempi relativi presenti nel template.
    - **Imposta i Segmenti**: Compila automaticamente i campi di inizio/fine per i segmenti "fast" e "slow" e attiva la modalità "Definisci Segmenti Manualmente".
    - **Crea il File Eventi**: Genera un nuovo file CSV (es. `manual_events_fixed.csv`) nella cartella di output con i tempi assoluti di ogni trial.
    - **Imposta gli Eventi**: Compila automaticamente il percorso di questo nuovo file e attiva la modalità "Carica Eventi da File CSV".

A questo punto, l'intera analisi è pre-configurata con la massima precisione. Basta cliccare su "Avvia Analisi Completa".

---
#### Metodo 2: Interattivo
- Clicca il pulsante **"Definisci Eventi UP/DOWN/LEFT/RIGHT (Interattivo)"**.
- Si aprirà il video player. Potrai definire l'inizio e la fine di ogni trial, etichettandolo (es. "right", "left").
- Al termine, il programma ti chiederà di **salvare le annotazioni in un file .csv**.
- Il percorso di questo file verrà inserito automaticamente nella GUI, pronto per essere usato nell'analisi.

#### Metodo 3: Tramite File CSV
- Prepara un file `.csv` con le specifiche di ogni trial.
- Attiva la checkbox **"Carica Eventi da File CSV"** e seleziona il tuo file.
- Il programma salterà l'identificazione automatica dei movimenti e userà i dati del tuo file per generare il report.

---

### C. Formato dei File CSV

#### 1. Formato per Template a Tempi Fissi
Il file deve contenere le colonne: `event_type`, `direction`, `relative_start`, `relative_end`.

- **event_type**: `segment` (per i blocchi fast/slow) o `trial` (per i movimenti)
- **direction**: `fast`, `slow`, `up`, `down`, `left`, `right`
- **relative_start / relative_end**: I numeri di frame relativi all'inizio dell'esperimento (l'onset)

**Esempio (`template_tempi.csv`)**
```csv
event_type,direction,relative_start,relative_end
segment,fast,0,5000
segment,slow,6000,15000
trial,right,200,450
trial,left,700,950
```

#### 2. Formato per Eventi Manuali
Il file deve contenere le colonne: `segment_name`, `direction_simple`, `start_frame`, `end_frame`.

- **segment_name**: `fast` o `slow`
- **direction_simple**: `right`, `left`, `up`, o `down`
- **start_frame / end_frame**: I numeri di frame assoluti nel video

**Esempio (`manual_events.csv`)**
```csv
segment_name,direction_simple,start_frame,end_frame
fast,right,5010,5090
fast,left,5150,5230
```

---

## 📋 Prerequisiti

È necessario acquisire i dati con **Pupil Labs Neon**, usare gli **AprilTag** e processare la registrazione su **Pupil Cloud** con l'enrichment **Marker Mapper**.  
La cartella scaricata da Pupil Cloud deve contenere i file:

- `video.mp4`
- `gaze.csv`
- `world_timestamps.csv`
- `surface_positions.csv`

---

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

---

## 📊 Output del Progetto

Il software genera una serie di file nella cartella di output specificata, fornendo un'analisi completa.

- **`final_report.xlsx`**: Il file più importante, un report Excel con metriche dettagliate e di riepilogo. (Vedi dettagli sotto)
- **`final_video_fast.mp4` / `final_video_slow.mp4`**: Video dei segmenti "fast" e "slow" con overlay dei dati di sguardo (posizione, tracciamento della palla).
- **`output_final_analysis_analysis.csv`**: Un file CSV contenente i dati grezzi calcolati, frame per frame, che costituisce la base per il report finale.
- **`cut_points.csv`**: Un file CSV che memorizza i frame di inizio e fine dei segmenti "fast" e "slow", sia che siano stati trovati automaticamente o definiti manualmente.
- **Cartella `plots_and_heatmaps/`**: Contiene tutte le visualizzazioni grafiche generate, come:
  - Heatmap dello sguardo per ogni direzione.
  - Grafici dell'andamento pupillare medio.
  - Grafici di frammentazione dello sguardo (se l'opzione è attiva).

### Dettaglio del `final_report.xlsx`

Questo file Excel è il prodotto finale dell'analisi e riassume le performance visuo-motorie del partecipante. È strutturato in diversi fogli di lavoro per fornire sia una visione d'insieme che un'analisi dettagliata per ogni segmento dell'esperimento (`fast` e `slow`).

Il report è composto da 5 fogli di lavoro:

1.  **`Riepilogo_Generale`**: Fornisce una sintesi ad alto livello, confrontando le performance complessive tra i segmenti "fast" e "slow".
2.  **`Riepilogo_fast`**: Contiene le metriche aggregate per ogni direzione di movimento (`up`, `down`, `left`, `right`) all'interno del solo segmento "fast".
3.  **`Dettagli_fast`**: Mostra i dati grezzi, frame per frame, per tutti i trial (movimenti) identificati nel segmento "fast".
4.  **`Riepilogo_slow`**: Simile a `Riepilogo_fast`, ma per il segmento "slow".
5.  **`Dettagli_slow`**: Simile a `Dettagli_fast`, ma per il segmento "slow".

---

#### 1. Foglio: `Riepilogo_Generale`

Questo foglio è il punto di partenza ideale. Offre un confronto diretto delle metriche chiave tra i due segmenti principali dell'esperimento. Ogni riga corrisponde a un segmento (`fast` o `slow`).

| Colonna | Descrizione e Metodo di Calcolo |
| :--- | :--- |
| **`segmento`** | Indica il segmento di riferimento per quella riga (`fast` o `slow`). |
| **`gaze_in_box_perc_totale`** | **Cosa misura:** La percentuale di tempo in cui lo sguardo del partecipante si trovava correttamente sulla palla (all'interno di un'area di tolleranza) durante tutti i trial di quel segmento. <br> **Come si calcola:** È la media della colonna `gaze_in_box` (che vale 1 se lo sguardo è nel box, 0 altrimenti) per tutti i frame che appartengono a un trial valido, moltiplicata per 100. Un valore alto indica un buon inseguimento. |
| **`velocita_sguardo_media`** | **Cosa misura:** La velocità media dello sguardo durante i trial. <br> **Come si calcola:** È la media della colonna `gaze_speed`. La velocità istantanea (`gaze_speed`) è calcolata come la distanza euclidea tra le coordinate normalizzate dello sguardo in due frame consecutivi. |
| **`numero_trial_validi`** | **Cosa misura:** Il numero totale di movimenti (trial) validi che il software ha identificato in quel segmento. <br> **Come si calcola:** È il conteggio dei valori unici di `trial_id` maggiori di zero. |
| **`diametro_pupillare_medio`** | **Cosa misura:** Il diametro medio della pupilla (in mm) durante tutti i trial del segmento. <br> **Come si calcola:** È la media della colonna `pupil_diameter_mean`. Questa metrica è presente solo se i dati pupillari sono disponibili. |
| **`escursione_successo_perc`** | **Cosa misura:** La percentuale di trial considerati "di successo" in termini di completamento della traiettoria. <br> **Come si calcola:** Un trial è un "successo" se la metrica `gaze_in_box` è stata `True` per almeno l'80% della sua durata. Questa colonna mostra la percentuale di trial che hanno superato tale soglia. È presente solo se l'analisi "Escursione" è attiva. |
| **`escursione_perc_frames_media`** | **Cosa misura:** La percentuale media di completamento della traiettoria per ogni trial. <br> **Come si calcola:** Per ogni trial, si calcola la percentuale di frame in cui lo sguardo era nel box. Questa colonna è la media di tali percentuali su tutti i trial del segmento. È presente solo se l'analisi "Escursione" è attiva. |

---

#### 2. Fogli: `Riepilogo_fast` e `Riepilogo_slow`

Questi fogli "spaccano" i dati del riepilogo generale, mostrando le performance per ogni singola direzione di movimento. Questo permette di identificare eventuali asimmetrie o difficoltà specifiche (es. il partecipante segue bene a destra ma male in alto).

| Colonna | Descrizione e Metodo di Calcolo |
| :--- | :--- |
| **`direction_simple`** | La direzione del movimento (`right`, `left`, `up`, `down`). |
| **`avg_gaze_in_box_perc`** | **Cosa misura:** La percentuale di tempo in cui lo sguardo era sulla palla, ma mediata solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_in_box` per tutti i frame dei trial che vanno in quella direzione, moltiplicata per 100. |
| **`avg_gaze_speed`** | **Cosa misura:** La velocità media dello sguardo solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_speed` per tutti i frame dei trial che vanno in quella direzione. |
| **`trial_count`** | **Cosa misura:** Il numero di trial eseguiti in quella specifica direzione. <br> **Come si calcola:** Conteggio dei trial unici per quella direzione. |
| **`avg_pupil_diameter`** | **Cosa misura:** Il diametro pupillare medio solo per i trial di una specifica direzione. <br> **Come si calcola:** Media di `pupil_diameter_mean` per i trial di quella direzione. |
| **`excursion_success_perc`** | **Cosa misura:** La percentuale di trial di successo per una specifica direzione. <br> **Come si calcola:** Percentuale di trial in quella direzione che superano la soglia dell'80% di `gaze_in_box`. |
| **`avg_excursion_perc_frames`** | **Cosa misura:** La percentuale media di completamento della traiettoria per i trial di una specifica direzione. <br> **Come si calcola:** Media delle percentuali di completamento per ogni trial di quella direzione. |

---

#### 3. Fogli: `Dettagli_fast` e `Dettagli_slow`

Questi sono i fogli più granulari e contengono i dati calcolati per ogni singolo frame che fa parte di un trial. Sono utili per analisi approfondite o per debug.

| Colonna | Descrizione |
| :--- | :--- |
| **`frame`** | Il numero del frame nel video originale. |
| **`ball_center_x_norm`, `ball_center_y_norm`** | Coordinate normalizzate (0-1) del centro della palla. |
| **`gaze_x_norm`, `gaze_y_norm`** | Coordinate normalizzate (0-1) del punto di sguardo sulla superficie. |
| **`gaze_in_box`** | Valore booleano (`True`/`False`) che indica se il punto di sguardo (`gaze`) si trova all'interno del rettangolo di tracciamento della palla. |
| **`direction`** | Descrizione completa del movimento (es. `center_to_right`). |
| **`trial_id`** | Un numero intero che identifica univocamente ogni movimento. Tutti i frame con lo stesso `trial_id` appartengono allo stesso evento. |
| **`direction_simple`** | La direzione cardinale del movimento (`right`, `left`, `up`, `down`). |
| **`ball_speed`, `gaze_speed`** | Velocità istantanea della palla e dello sguardo, calcolata tra frame consecutivi. |
| **`pupil_diameter_mean`** | Diametro pupillare (mm) sincronizzato a quel frame. |
| **`excursion_perc_frames`** | Percentuale di completamento del trial a cui questo frame appartiene (è lo stesso valore per tutti i frame dello stesso `trial_id`). |
| **`excursion_success`** | Valore booleano (`True`/`False`) che indica se il trial a cui questo frame appartiene è stato un successo (è lo stesso valore per tutti i frame dello stesso `trial_id`). |
