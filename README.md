# Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA)

**LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)**  

**Sito Web Lab:** [labscoc.wordpress.com](https://labscoc.wordpress.com)  

**PIs:** Prof. Giuseppe Curcio, Prof. Simone Migliore

**Concettualizzazione:** Dr. Massimo Marano  

**Codice:** Dr. Daniele Lozzi  

**Verifica dei dati**: Dr.ssa Ilaria Di Pompeo, Dr.ssa Martina Marcaccio


Questo repository contiene una pipeline software completa per l'analisi del movimento oculare e della pupillometria in relazione al movimento di un cerchio su uno schermo. L'intero processo è gestito da un'unica interfaccia grafica (GUI) che orchestra l'elaborazione dei dati.

## 🎯 Obiettivo del Software
L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Il software offre diverse modalità di lavoro per massima flessibilità, da quella completamente automatica a quella interamente manuale e interattiva.

## 🚀 Modalità di Lavoro

**ATTUALMENTE SI CONSIGLIA DI USARE LA MODALITà HOUGH CIRCLE**

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

La GUI è organizzata in sezioni per gestire i dati in modo intuitivo. Di seguito sono descritte le principali modalità di lavoro manuali e ibride.

---

### Template Verificato (Saccadici Renato)

È stato creato e validato da tre esperti un template a tempi relativi basato sulla presentazione `Saccadici_renato_aggiornato.pptx`. Questo template è stato progettato per essere utilizzato con la modalità "Template a Tempi Fissi" (descritta di seguito) per garantire la massima coerenza e riproducibilità delle analisi per questo specifico paradigma.

### A. Template a Tempi Fissi (Consigliato per Paradigmi Standard)
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
    - **Crea il File Eventi**: Genera un nuovo file CSV (es. `manual_events_fixed.csv`) nella cartella di output con i tempi assoluti di ogni trial (movimento).
    - **Imposta gli Eventi**: Compila automaticamente il percorso di questo nuovo file. Il programma userà questo file per l'analisi.

A questo punto, l'intera analisi è pre-configurata con la massima precisione. Basta cliccare su "Avvia Analisi Completa".

---

### B. Definizione Interattiva
Questa modalità ti dà il pieno controllo visivo sull'analisi.

#### 1. Definire i Segmenti (Fast/Slow)
- Clicca il pulsante **"Definisci Segmenti FAST/SLOW (Interattivo)"**.
- Si aprirà un video player che ti permetterà di scorrere il video, definire l'inizio e la fine per i segmenti "fast" e "slow" e confermare.
- Una volta chiusa la finestra, i campi interni del programma verranno compilati e l'analisi userà questi valori, saltando la ricerca automatica.

#### 2. Definire gli Eventi di Movimento (Trial)
- Clicca il pulsante **"Definisci Eventi UP/DOWN/LEFT/RIGHT (Interattivo)"**.
- Si aprirà il video player. Potrai definire l'inizio e la fine di ogni trial, etichettandolo (es. "right", "left").
- Al termine, il programma ti chiederà di **salvare le annotazioni in un file .csv** (es. `manual_events.csv`).
- Il percorso di questo file verrà inserito automaticamente nella GUI, pronto per essere usato nell'analisi.

---

### C. Caricare e Salvare File di Eventi
Questa modalità è utile per riutilizzare definizioni già create o per preparare l'analisi in anticipo.

#### 1. Caricare/Salvare Segmenti (Fast/Slow)
- **Carica**: Usa **"Carica Segmenti FAST/SLOW (da CSV)"** per caricare un file `.csv` con i frame di inizio e fine dei segmenti.
- **Salva**: Usa **"Salva Segmenti FAST/SLOW (CSV Assoluto)"** per salvare i segmenti attualmente definiti (automaticamente o manualmente) in un file `.csv`.

#### 2. Caricare Eventi di Movimento (Trial)
- Prepara un file `.csv` con le specifiche di ogni trial (vedi formato sotto).
- Clicca su **"Carica Eventi U/D/L/R (da CSV)"** e seleziona il tuo file.
- Il programma salterà l'identificazione automatica dei movimenti e userà i dati del tuo file.

#### 3. Salvare un Template Relativo
- Dopo aver completato un'analisi (definendo segmenti e trial), puoi salvarla come un nuovo template riutilizzabile tramite **"Salva Template Relativo Corrente (in CSV)"**. Il software ti chiederà di definire un punto "zero" (onset) e convertirà tutti i tempi assoluti in relativi.

---

### D. Formati dei File CSV

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

### E. Parametri di Analisi
La GUI presenta una sezione dedicata ai "Parametri di Analisi" che permette di affinare il comportamento degli algoritmi:

- **Padding Box Inseguimento (%)**: Controlla la dimensione dell'area di tolleranza usata per determinare se lo sguardo è "sulla palla" (`gaze_in_box`). Un valore più alto rende l'analisi più permissiva (box più grande), mentre un valore più basso la rende più conservativa (box più piccolo). Il default è 20%.

- **Soglia Successo Escursione (%)**: Definisce la percentuale minima di tempo che lo sguardo deve passare all'interno del box di inseguimento affinché un trial sia considerato "di successo" per la metrica `escursione_successo_perc`. Il default è 80%.

- **Soglia Bordo Esc. Direzionale (%)**: Definisce un margine di tolleranza per la metrica di "Escursione Direzionale". Questo valore (espresso come percentuale della dimensione dello schermo) viene usato per creare una "linea del traguardo" dinamica. Un valore più alto rende il test più permissivo, spostando la linea verso il centro. Il default è 15%.

Questi parametri vengono passati agli script di analisi quando si clicca su "Avvia Analisi Completa".

> **Nota**: Se si desidera calcolare le metriche di escursione, è necessario spuntare la casella "Calcola metriche 'Escursione' e 'Escursione Direzionale'".


---

## ⚙️ Acquisizione e Preparazione dei Dati

Per garantire che i dati siano compatibili con la pipeline di analisi, è fondamentale seguire una procedura di registrazione e processamento standardizzata.

### 0. Organizzazione Automatica dei Dati (Novità)

Per semplificare al massimo la preparazione dei dati, è stato aggiunto un pulsante **"✨ 0. Organizza Dati da ZIP"** all'inizio della GUI. Questa funzione automatizza l'intero processo di preparazione della cartella di input.

**Come funziona:**
1.  **Scarica i Dati**: Scarica da Pupil Cloud i due archivi `.zip` necessari ("Timeseries CSV and Scene Video" e "QR Marker Mapper data") e salvali nella stessa cartella sul tuo computer. **Non è necessario scompattarli manualmente**.
2.  **Clicca il Pulsante**: Avvia il software di analisi e clicca su **"✨ 0. Organizza Dati da ZIP"**.
3.  **Seleziona la Cartella**: Seleziona la cartella in cui hai salvato i due file `.zip`.
4.  **Fatto!**: Il software eseguirà automaticamente i seguenti passaggi:
    - Scompatterà i file `.zip`.
    - Identificherà e prenderà solo i file necessari (`video.mp4`, `gaze.csv`, ecc.).
    - Rinominerà il video in `video.mp4`.
    - Creerà una nuova cartella chiamata **`input_data`** (nella stessa posizione dei file ZIP) contenente tutti i file pronti per l'analisi.
5.  A questo punto, puoi usare il pulsante "Seleziona..." per impostare questa nuova cartella `input_data` come **"Cartella Input"** e procedere con l'analisi.

### 1. Setup per la Registrazione (Pupil Neon + PowerPoint)

Questa sezione descrive come impostare l'ambiente per una corretta acquisizione dei dati.

1.  **Preparazione dello Schermo**:
    *   Apri la presentazione PowerPoint (es. `Saccadici_renato_aggiornato.pptx`) sul computer che verrà utilizzato per il test.
    *   **Applica quattro AprilTag** ai quattro angoli dello schermo. Questi marker sono essenziali perché permettono a Pupil Cloud di identificare l'area dello schermo e correggere la prospettiva. Assicurati che siano ben visibili e non coperti.

2.  **Avvio della Registrazione**:
    *   Fai indossare al partecipante gli occhiali **Pupil Labs Neon**.
    *   Avvia la registrazione tramite l'app Neon sul dispositivo companion (smartphone).
    *   Avvia la presentazione PowerPoint in modalità "Presentazione" a schermo intero.

3.  **Esecuzione del Test**:
    *   Il partecipante deve seguire le istruzioni a schermo, in particolare il movimento della palla.

4.  **Fine della Registrazione**:
    *   Al termine della presentazione, interrompi la registrazione dall'app Neon.
    *   Carica la registrazione su **Pupil Cloud**.

### 2. Processamento su Pupil Cloud e Download dei Dati

Una volta che la registrazione è su Pupil Cloud, deve essere processata per generare i file necessari all'analisi.

1.  **Applica l'Enrichment "Marker Mapper"**:
    *   All'interno del progetto su Pupil Cloud, seleziona la registrazione e vai alla sezione "Enrichments".
    *   Aggiungi e avvia l'enrichment **Marker Mapper**. Questo algoritmo utilizzerà gli AprilTag per mappare lo sguardo sulla superficie dello schermo.

2.  **Scarica i Dati Corretti**:
    *   Dopo che l'enrichment ha terminato, scarica i dati. È fondamentale scaricare due pacchetti separati:
        *   **Time Series Data**: Contiene il video principale e i dati temporali.
        *   **QR Marker Mapper data**: Contiene i dati dello sguardo già mappati sulla superficie dello schermo.
    *   Decomprimi entrambi gli archivi e unisci i file richiesti in un'unica **cartella di input** per il nostro software.

### 3. File Richiesti nella Cartella di Input

La cartella che fornirai al software di analisi deve contenere i seguenti file:

- **`video.mp4`**: Dalla cartella "Time Series Data".
- **`gaze.csv`**: Dalla cartella "QR Marker Mapper data".
- **`world_timestamps.csv`**: Dalla cartella "Time Series Data".
- **`surface_positions.csv`**: Dalla cartella "QR Marker Mapper data".
- **`3d_eye_states.csv`** (Opzionale): Dalla cartella "Time Series Data". Necessario solo per l'analisi pupillometrica.

> **Nota**: Se il file `3d_eye_states.csv` non è presente, il software funzionerà comunque ma salterà tutte le metriche relative al diametro pupillare.


## 🛠️ Installazione ⚙️
To run the project from source or contribute to development, you'll need Python 3 and several libraries.

1. **Install Anaconda**: [Link](https://www.anaconda.com/)
2. *(Optional)* Install CUDA Toolkit: For GPU acceleration with NVIDIA. [Link](https://developer.nvidia.com/cuda-downloads)
3. **Create a virtual environment**:

Open Anaconda Prompt

```bash
conda create --name neurological-assessment
conda activate neurological-assessment
conda install pip
conda install git
git clone https://github.com/danielelozzi/neurological-assessment.git
```
4. **Install the required libraries**:

enter in the neurological-assessment folder

```bash
cd neurological-assessment
```

install requirements

```bash
pip install -r requirements.txt
```
5. **(optional) Install Pytorch CUDA**:

[https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

```bash
<command>
```
---

## How to Use the Application from Source 🚀
### Launch the GUI:
```bash
# Navigate to the desktop_app folder
cd neurological-assessment
conda activate neurological-assessment
python main_gui.py
```

---



## 📊 Output del Progetto

Il software genera una serie di file nella cartella di output specificata, fornendo un'analisi completa.

- **`final_report.xlsx`**: Il file più importante, un report Excel con metriche dettagliate e di riepilogo. (Vedi dettagli sotto)
- **`final_video_fast.mp4` / `final_video_slow.mp4`**: Video dei segmenti "fast" e "slow" con overlay dei dati di sguardo (posizione, tracciamento della palla).
- **`output_final_analysis_analysis.csv`**: Un file CSV contenente i dati grezzi calcolati, frame per frame, che costituisce la base per il report finale.
- **`cut_points.csv`**: Un file CSV che memorizza i frame di inizio e fine dei segmenti "fast" e "slow", sia che siano stati trovati automaticamente o definiti manualmente.
- **`analysis_parameters.csv`**: Un file CSV che salva tutti i parametri impostati nella GUI al momento dell'analisi, per garantire la riproducibilità.
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
| **`escursione_successo_perc`** | **Cosa misura:** La percentuale di trial considerati "di successo". Un trial è un successo se l'inseguimento della palla è stato sufficientemente preciso per la maggior parte del tempo. <br> **Come si calcola:** Per ogni trial, si calcola la percentuale di frame in cui lo sguardo è rimasto nel box di tolleranza. Se questa percentuale supera la "Soglia Successo Escursione" (impostata nella GUI, default 80%), il trial è un successo. Questa metrica è la percentuale di trial che hanno soddisfatto tale criterio. <br> **Formula:** `(Numero di trial di successo / Numero totale di trial) * 100` |
| **`escursione_perc_frames_media`** | **Cosa misura:** La percentuale media di completamento dell'inseguimento (inseguimento della palla) per ogni trial. A differenza di `gaze_in_box_perc_totale`, questa metrica calcola prima la performance per ogni singolo trial e poi ne fa la media. <br> **Come si calcola:** Per ogni trial, si calcola la percentuale di frame in cui lo sguardo era nel box. Questa colonna è la media di tali percentuali su tutti i trial del segmento. È presente solo se l'analisi "Escursione" è attiva. |
| **`escursione_direzionale_successo_perc`** | **Cosa misura:** La percentuale di trial in cui lo sguardo ha raggiunto la destinazione finale del movimento. <br> **Come si calcola:** Per ogni trial, il software identifica la posizione più estrema raggiunta dalla palla e definisce una "linea del traguardo" dinamica. Un trial è un successo se lo sguardo, in almeno un frame, supera questa linea (considerando il margine di tolleranza impostato nella GUI). |
| **`escursione_direzionale_raggiunta_perc_media`** | **Cosa misura:** La media del successo direzionale, espressa come valore tra 0 e 1. <br> **Come si calcola:** È la media della colonna `directional_excursion_reached` (che vale 1 per successo, 0 per fallimento). Il valore è numericamente equivalente a `escursione_direzionale_successo_perc / 100`. |
| **`diametro_pupillare_medio`** | **Cosa misura:** Il diametro medio della pupilla (in mm) durante tutti i trial del segmento. <br> **Come si calcola:** È la media della colonna `pupil_diameter_mean`. Questa metrica è presente solo se i dati pupillari sono disponibili. |

---

#### Differenza tra `gaze_in_box_perc_totale` e `escursione_successo_perc`

È importante capire la sottile ma fondamentale differenza tra queste due metriche:

- **`gaze_in_box_perc_totale` (Performance a livello di frame)**: Misura la performance "grezza" e continua. Risponde alla domanda: "Considerando tutti i momenti di inseguimento, per quale percentuale di tempo totale lo sguardo era sul bersaglio?". Un valore del 90% qui significa che su 1000 frame totali di inseguimento, lo sguardo era nel box per 900 frame.
  - **Formula:** `(Numero totale di frame con gaze_in_box=True / Numero totale di frame di tutti i trial) * 100`

- **`escursione_successo_perc` (Performance a livello di trial)**: Misura la consistenza della performance. Risponde alla domanda: "Quanti trial sono stati eseguiti in modo sufficientemente buono?". Un valore del 90% qui significa che 9 trial su 10 hanno superato la soglia di precisione (es. 80% del tempo sul bersaglio). Un trial potrebbe avere una performance del 79% (fallimento) e un altro del 100% (successo). Questa metrica cattura la capacità di completare con successo un intero movimento.
  - **Formula:** `(Numero di trial con performance >= Soglia / Numero totale di trial) * 100`

In sintesi, la prima è una media "temporale" su tutti i frame, mentre la seconda è una media "discreta" sul numero di trial riusciti.

---

#### 2. Fogli: `Riepilogo_fast` e `Riepilogo_slow`

Questi fogli "spaccano" i dati del riepilogo generale, mostrando le performance per ogni singola direzione di movimento. Questo permette di identificare eventuali asimmetrie o difficoltà specifiche (es. il partecipante segue bene a destra ma male in alto). Le colonne sono le stesse del riepilogo generale, ma calcolate raggruppando per direzione.

| Colonna | Descrizione e Metodo di Calcolo |
| :--- | :--- |
| **`direction_simple`** | La direzione del movimento (`right`, `left`, `up`, `down`). |
| **`avg_gaze_in_box_perc`** | **Cosa misura:** La percentuale di tempo in cui lo sguardo era sulla palla, ma mediata solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_in_box` per tutti i frame dei trial che vanno in quella direzione, moltiplicata per 100. |
| **`avg_gaze_speed`** | **Cosa misura:** La velocità media dello sguardo solo per i trial di una specifica direzione. <br> **Come si calcola:** È la media di `gaze_speed` per tutti i frame dei trial che vanno in quella direzione. |
| **`trial_count`** | **Cosa misura:** Il numero di trial eseguiti in quella specifica direzione. <br> **Come si calcola:** Conteggio dei trial unici per quella direzione. |
| **`diametro_pupillare_medio`** | **Cosa misura:** Il diametro medio della pupilla (in mm) durante tutti i trial del segmento. <br> **Come si calcola:** È la media della colonna `pupil_diameter_mean`. Questa metrica è presente solo se i dati pupillari sono disponibili. |
| **`excursion_success_perc`** | **Cosa misura:** La percentuale di trial di successo (inseguimento) per una specifica direzione. <br> **Come si calcola:** Percentuale di trial in quella direzione che superano la "Soglia Successo Escursione". |
| **`avg_excursion_perc_frames`** | **Cosa misura:** La percentuale media di completamento dell'inseguimento per i trial di una specifica direzione. <br> **Come si calcola:** Media delle percentuali di completamento per ogni trial di quella direzione. |
| **`directional_excursion_success_perc`** | **Cosa misura:** La percentuale di trial di successo (raggiungimento destinazione) per una specifica direzione. <br> **Come si calcola:** Percentuale di trial in quella direzione in cui lo sguardo ha superato la linea del traguardo dinamica. |
| **`avg_directional_excursion_reached`** | **Cosa misura:** La media del successo direzionale per i trial di una specifica direzione. <br> **Come si calcola:** Media di `directional_excursion_reached` per i trial di quella direzione. |

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
| **`excursion_success`** | Valore booleano (`True`/`False`) che indica se il trial a cui questo frame appartiene è stato un successo di inseguimento (è lo stesso valore per tutti i frame dello stesso `trial_id`). |
| **`directional_excursion_reached`** | Valore numerico (1.0/0.0) che indica se il trial a cui questo frame appartiene ha raggiunto la destinazione. |
| **`directional_excursion_success`** | Valore booleano (`True`/`False`) che indica se il trial a cui questo frame appartiene è stato un successo di raggiungimento della destinazione. |

---

## 📚 Appendice A: Analisi Dettagliata di un Flusso di Lavoro

Questa sezione descrive in dettaglio il flusso di elaborazione dati per uno scenario specifico e consigliato:

-   **Metodo di Input**: Template a Tempi Relativi (`Carica Template a Tempi Fissi`).
-   **Definizione Onset**: Inserimento manuale del frame di inizio.
-   **Rilevamento Palla**: Trasformata di Hough (`Hough Circle`).

### Fase 1: Configurazione e Preparazione (GUI)

L'utente avvia l'analisi attraverso l'interfaccia grafica (`main_gui.py`).

1.  **Caricamento Template**: L'utente clicca su **"Carica Template a Tempi Fissi (da CSV)"**.
    -   **File Input**: Viene selezionato un file CSV (es. `template_relativo.csv`).
    -   **Colonne Lette**: `event_type`, `direction`, `relative_start`, `relative_end`.

2.  **Definizione Onset**: Il software chiede come definire il punto "zero" del template. L'utente sceglie **"Inserisci Manualmente"**.
    -   **Input Utente**: Viene inserito un numero intero, che rappresenta il frame di inizio del segmento `fast` nel video. Chiamiamo questo valore `onset_frame`.

3.  **Calcolo Tempi Assoluti**: Il software ora traduce il template relativo in tempi assoluti per il video corrente.
    -   Legge il file template riga per riga.
    -   Per ogni riga, calcola i frame assoluti con le seguenti formule:
        -   `start_frame_assoluto = relative_start + onset_frame`
        -   `end_frame_assoluto = relative_end + onset_frame`

4.  **Generazione File Intermedi**:
    -   **`manual_events_fixed.csv`**: Viene creato un nuovo file CSV nella cartella di output. Questo file contiene solo gli eventi di tipo `trial` (i movimenti U/D/L/R) con i loro tempi assoluti appena calcolati. Le colonne sono: `segment_name`, `direction_simple`, `start_frame`, `end_frame`. Questo file diventa la "verità assoluta" per la definizione dei trial.
    -   **`cut_points.csv`**: Poiché i campi dei segmenti `fast` e `slow` sono stati popolati nella GUI, il software salta la ricerca automatica (OCR) e scrive direttamente questo file nella cartella di output. Contiene i frame di inizio e fine dei due segmenti principali. Colonne: `segment_name`, `start_frame`, `end_frame`.

5.  **Avvio Analisi**: L'utente clicca su **"Avvia Analisi Completa"**.

### Fase 2: Rilevamento e Sincronizzazione (`detect_and_save_ball.py`)

Questo script è il cuore dell'analisi frame per frame.

1.  **Allineamento Dati**:
    -   **File Input**: `world_timestamps.csv` e `gaze.csv`.
    -   **Colonne Lette**:
        -   Da `world_timestamps.csv`: `world_index` (o `# frame_idx`), `timestamp [ns]`.
        -   Da `gaze.csv`: `timestamp [ns]`, `gaze detected on surface`, `gaze position on surface x [normalized]`, `gaze position on surface y [normalized]`.
    -   **Processo**: Esegue un `pandas.merge_asof` tra i due file, usando i timestamp come chiave. Questo allinea ogni frame del video (`world_index`) con il dato di sguardo (`gaze`) più vicino nel tempo (con una tolleranza di 100ms). Il risultato è un dataframe `aligned_gaze_data` che contiene, per ogni frame, le coordinate dello sguardo corrispondenti.

2.  **Ciclo di Analisi sui Segmenti**:
    -   Lo script legge `cut_points.csv` per sapere quali intervalli di frame analizzare (es. da frame 150 a 9750 per il segmento `fast`).
    -   Per ogni frame all'interno di questi intervalli:
        a.  **Correzione Prospettiva**:
            -   **File Input**: `surface_positions.csv`.
            -   **Colonne Lette**: `world_index`, `tl x/y [px]`, `tr x/y [px]`, `br x/y [px]`, `bl x/y [px]`.
            -   **Processo**: Trova le coordinate dei 4 AprilTag per il frame corrente e usa `cv2.getPerspectiveTransform` e `cv2.warpPerspective` per "raddrizzare" l'immagine, isolando solo lo schermo.

        b.  **Rilevamento Palla (Hough Circle)**:
            -   **Ottimizzazione Parametri (una tantum)**: Al primo frame valido di un segmento, lo script esegue la funzione `find_optimal_hough_params`. Questa funzione testa diverse combinazioni di parametri per `cv2.HoughCircles` (`param1`, `param2`, `minRadius`, `maxRadius`) fino a trovare una configurazione che rileva **esattamente un cerchio**. Questi parametri ottimali vengono poi usati per tutto il resto del segmento.
            -   **Rilevamento**: Sul frame raddrizzato, esegue `cv2.HoughCircles` con i parametri ottimali per trovare la posizione `(x, y)` e il raggio `r` della palla.
            -   **Normalizzazione**: Converte le coordinate in pixel della palla in coordinate normalizzate (da 0 a 1) dividendo per la larghezza e l'altezza del frame raddrizzato.

        c.  **Calcolo `gaze_in_box`**:
            -   **Processo**: Determina se lo sguardo si trova sulla palla.
            -   **Formula**:
                1.  Crea un "bounding box" attorno alla palla rilevata.
                2.  Aumenta le dimensioni di questo box in base al parametro `Padding Box Inseguimento (%)` impostato nella GUI.
                3.  Converte le coordinate normalizzate dello sguardo (`gaze_x_norm`, `gaze_y_norm`) in coordinate pixel.
                4.  Controlla se le coordinate pixel dello sguardo cadono all'interno del box allargato.
            -   **Output**: Una colonna booleana `gaze_in_box` (`True` o `False`).

3.  **Salvataggio Risultati Intermedi**:
    -   **File Output**: `output_final_analysis_analysis.csv`.
    -   **Colonne Scritte**: Per ogni frame analizzato, salva una riga contenente `frame`, `ball_center_x_norm`, `ball_center_y_norm`, `gaze_x_norm`, `gaze_y_norm`, `gaze_in_box`, `segment_name`, e altre.

### Fase 3: Generazione Report e Metriche (`generate_report.py`)

Questo script prende i dati grezzi calcolati nella fase precedente e li trasforma in metriche significative.

1.  **Caricamento Dati**:
    -   **File Input**: `output_final_analysis_analysis.csv` e `manual_events_fixed.csv`.

2.  **Etichettatura dei Trial**:
    -   **Processo**: Lo script **salta completamente l'identificazione automatica dei trial**. Usa `manual_events_fixed.csv` come unica fonte di verità.
    -   Per ogni riga in `manual_events_fixed.csv` (es. `right, start: 350, end: 430`), assegna l'etichetta `direction_simple: 'right'` e un `trial_id` univoco a tutti i frame compresi tra 350 e 430 nel dataframe principale.

3.  **Aggiunta Dati Pupillari**:
    -   **File Input**: `3d_eye_states.csv` (se presente).
    -   **Colonne Lette**: `timestamp [ns]`, `pupil diameter left [mm]`, `pupil diameter right [mm]`.
    -   **Processo**: Calcola il diametro medio tra occhio destro e sinistro (`pupil_diameter_mean`). Esegue un `merge_asof` con il dataframe principale usando i timestamp per sincronizzare il dato pupillare con ogni frame.

4.  **Calcolo Metriche di Performance** (se le opzioni sono attive nella GUI):
    -   **`escursione_successo_perc`**:
        -   **Formula per Trial**: Per ogni `trial_id`, calcola `mean(gaze_in_box)`.
        -   **Formula per Successo**: Il trial è un successo se `mean(gaze_in_box) >= Soglia Successo Escursione` (es. 0.80).
        -   **Metrica Finale**: `(Numero di trial di successo / Numero totale di trial) * 100`.

    -   **`escursione_direzionale_successo_perc`**:
        -   **Processo per Trial**: Per ogni `trial_id`:
            1.  Identifica la direzione (es. `right`).
            2.  Trova la posizione più estrema raggiunta dalla palla in quella direzione (es. `max(ball_center_x_norm)`).
            3.  **Definisce una "linea del traguardo" virtuale**: Questa linea non è fissa, ma viene calcolata dinamicamente. Si prende il bordo più esterno della palla nella direzione del movimento (es. il bordo destro per un movimento a destra) e lo si sposta leggermente verso il centro usando il valore della `Soglia Bordo Esc. Direzionale (%)`.
                - **Esempio (movimento a destra)**: Se il bordo destro della palla arriva al 92% dello schermo e la soglia è 15%, la linea del traguardo sarà `0.92 - 0.15 = 0.77`.
            4.  **Verifica**: Controlla se lo sguardo (`gaze_x_norm`) ha mai superato questa linea del traguardo durante il trial. Se sì, il trial è un successo per questa metrica.
        -   **Metrica Finale**: `(Numero di trial con traguardo raggiunto / Numero totale di trial) * 100`.

5.  **Aggregazione e Scrittura Report**:
    -   **Processo**: Raggruppa i dati per segmento (`fast`, `slow`) e per direzione (`up`, `down`, etc.).
    -   Calcola le medie e le percentuali per tutte le metriche.
    -   **File Output**: `final_report.xlsx`.
    -   **Fogli Creati**:
        -   `Riepilogo_Generale`: Confronto delle metriche aggregate tra i segmenti `fast` e `slow`.
        -   `Riepilogo_fast` / `Riepilogo_slow`: Metriche aggregate per ogni direzione, all'interno di un segmento.
        -   `Dettagli_fast` / `Dettagli_slow`: Dati grezzi, frame per frame, per ogni trial.

6.  **Salvataggio Dati Finali**:
    -   **File Output**: `output_final_analysis_with_metrics.csv`.
    -   **Contenuto**: Il dataframe completo con tutte le colonne calcolate, pronto per la fase successiva.

### Fase 4: Generazione Video con Overlay (`generate_video.py`)

Questo script finale crea una visualizzazione dei risultati.

1.  **Caricamento Dati**:
    -   **File Input**: `output_final_analysis_with_metrics.csv`, `video.mp4`, `surface_positions.csv`.

2.  **Ciclo di Disegno**:
    -   Crea un video writer per ogni segmento (`final_video_fast.mp4`, `final_video_slow.mp4`).
    -   Per ogni riga del file CSV (corrispondente a un frame):
        a.  Esegue la correzione della prospettiva come nella Fase 2.
        b.  Disegna sul frame raddrizzato:
            -   Un **cerchio** per la posizione dello sguardo (`gaze_x_norm`, `gaze_y_norm`). Il colore è giallo se `gaze_in_box` è `True`, altrimenti rosso.
            -   Un **rettangolo blu** per il box di inseguimento allargato.
            -   **Testo informativo**: Percentuale di inseguimento, successo del trial, nome dell'evento, etc., leggendo le colonne calcolate nella Fase 3.
            -   Una **linea gialla** per la soglia dell'escursione direzionale, se applicabile.

3.  **Salvataggio Video**:
    -   **File Output**: `final_video_fast.mp4`, `final_video_slow.mp4`.
    -   I video finali contengono tutti gli overlay visivi, fornendo un riscontro immediato e qualitativo dell'analisi quantitativa.

---

## 📚 Appendice B: Gestione dei Dati Mancanti

Il software è progettato per essere robusto e gestire in modo controllato i casi in cui i dati di input sono incompleti. Ecco come vengono gestiti i diversi scenari di dati mancanti:

#### Scenario 1: La palla non viene rilevata in un frame

Questo può accadere a causa di riflessi, occlusioni o parametri di rilevamento non ottimali per quel frame specifico.

-   **Script Coinvolto**: `detect_and_save_ball.py`
-   **Comportamento**: L'analisi **non si interrompe**. Per quel frame, le colonne relative alla posizione della palla (`ball_center_x_norm`, etc.) vengono salvate con un valore `NaN` (Not a Number). Di conseguenza, la metrica `gaze_in_box` per quel frame sarà `False`.
-   **Risultato**: Il frame viene incluso nell'analisi, ma contribuirà negativamente alle metriche di inseguimento che si basano sulla posizione della palla.

#### Scenario 2: I dati dello sguardo (`gaze`) mancano per un frame

Questo si verifica quando l'eye tracker perde temporaneamente il tracciamento.

-   **Script Coinvolto**: `detect_and_save_ball.py`
-   **Comportamento**: All'inizio dell'analisi di ogni frame, lo script verifica la presenza di dati di sguardo validi. Se mancano, l'intero frame viene **saltato** (`continue`).
-   **Risultato**: Nessuna riga per quel frame viene scritta nel file di output `output_final_analysis_analysis.csv`. Il frame viene di fatto escluso da tutte le analisi successive.

#### Scenario 3: Mancano sia la palla che lo sguardo in un frame

-   **Script Coinvolto**: `detect_and_save_ball.py`
-   **Comportamento**: Il controllo sulla presenza dei dati di sguardo ha la precedenza. Poiché i dati dello sguardo mancano, il frame viene saltato prima ancora che lo script tenti di rilevare la palla.
-   **Risultato**: Il frame viene escluso da tutte le analisi, come nello Scenario 2.

#### Scenario 4: I dati della palla sono vuoti per un intero trial

Questo è lo scenario più critico, che si verifica se l'algoritmo non riesce a rilevare la palla in nessuno dei frame che compongono un trial.

-   **Script Coinvolto**: `generate_report.py`
-   **Comportamento**: Grazie a controlli di robustezza specifici (es. `if group['ball_center_y_norm'].isnull().all()`), lo script rileva che per un intero trial i dati della palla sono `NaN`. Invece di generare un errore, considera il trial un fallimento per le metriche che dipendono dalla posizione della palla (come `directional_excursion`).
-   **Risultato**: L'analisi **non si interrompe**. Quel trial specifico verrà registrato nel report finale come un fallimento per quella metrica (es. `directional_excursion_success` sarà `False`), ma non influenzerà il calcolo degli altri trial validi.
