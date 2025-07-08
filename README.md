 Strumento di Analisi dei dati dell'Assessment Neurologico Computerizzato (CNA) - LabSCoC (Laboratorio di Scienze Cognitive e del Comportamento)

- **Sito Web Lab**: [labscoc.wordpress.com](https://labscoc.wordpress.com/)
- **Repository GitHub**: [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare in relazione al movimento di una palla. 

L'intero processo è gestito da un'unica **interfaccia grafica (GUI)** che orchestra l'elaborazione dei dati, dal taglio dei video grezzi fino alla generazione di un report statistico finale. 

---

## 🎯 Obiettivo del Software

L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie.  Partendo dai dati grezzi elaborati da Pupil Cloud, il software:
1.  **Identifica e isola** i segmenti di interesse del test ("fast" e "slow"). 
2.  **Rileva la palla** e ne traccia il movimento nel video. 
3.  **Sincronizza i dati dello sguardo** con la posizione della palla. 
4.  **Calcola metriche chiave** come la velocità dello sguardo, la velocità della palla e la percentuale di tempo in cui lo sguardo è correttamente sulla palla. [cite: 3, 6]
5.  **Produce un report Excel dettagliato** e visualizzazioni grafiche (heatmap, grafici pupillometrici) per un'analisi approfondita. [cite: 3, 6]

---

## 📋 Prerequisiti: Acquisizione e Preparazione dei Dati

Prima di utilizzare questo software, è necessario acquisire e preparare i dati seguendo una procedura specifica con gli strumenti di Pupil Labs.

1.  **Registrazione Video**: Utilizzare gli occhiali **Pupil Labs Neon** per registrare la sessione di test durante la proiezione del file PowerPoint *Saccadici_renato_aggiornato.pptx*.
2.  **Definizione della Superficie (AprilTag)**: Posizionare degli **AprilTag** ai quattro angoli dello schermo del Pc. Questi marcatori permettono al software di Pupil Labs di tracciare la superficie e mappare le coordinate dello sguardo su di essa.
    * Per maggiori dettagli, consultare la documentazione ufficiale: [**Pupil Labs Surface Tracker**](https://docs.pupil-labs.com/neon/neon-player/surface-tracker/).
3.  **Caricamento su Pupil Cloud**: Una volta completata la registrazione, caricare i dati sulla piattaforma **Pupil Cloud**.
4.  **Enrichment con Marker Mapper**: All'interno di Pupil Cloud, avviare l'enrichment **Marker Mapper**. Questo processo analizza il video, rileva gli AprilTag e genera il file `surface_positions.csv`, che contiene le coordinate della superficie per ogni frame.
    * Guida all'utilizzo del Marker Mapper: [**Pupil Cloud Marker Mapper**](https://docs.pupil-labs.com/neon/pupil-cloud/enrichments/marker-mapper/#setup).
5.  **Download dei Dati**: Al termine dell'enrichment, **scaricare l'intera cartella dei dati** dal progetto su Pupil Cloud. Questa cartella conterrà tutti i file necessari per l'analisi (`video.mp4`, `gaze.csv`, `surface_positions.csv`, `world_timestamps.csv`, etc.).

---

## 🛠️ Installazione

Per utilizzare il software, sono necessarie alcune librerie Python. È fortemente consigliato creare un ambiente virtuale per gestire le dipendenze. 

1.  **Crea un ambiente virtuale**: 
    ```bash
    python -m venv venv
    source venv/bin/activate  # Su Windows: venv\Scripts\activate
    ```

2.  **Installa le librerie richieste**: 
    ```bash
    pip install customtkinter opencv-python pandas numpy matplotlib seaborn scipy easyocr ultralytics xlsxwriter
    ```

---

## 🚀 Utilizzo

L'intera pipeline viene eseguita tramite l'interfaccia grafica. 

1.  **Avvia la GUI**: 
    Esegui il seguente comando dalla directory principale del progetto: 
    ```bash
    python main_gui.py
    ```

2.  **Configura l'Analisi**:
    Dalla finestra dell'applicazione, segui questi passaggi: 

    * **1. Seleziona la Cartella Input**: Clicca su "Seleziona..." e scegli la **cartella scaricata da Pupil Cloud** dopo aver eseguito l'enrichment con Marker Mapper. 

    * **2. Seleziona la Cartella Output**: Clicca su "Seleziona..." e scegli una cartella (anche vuota) dove verranno salvati **tutti i risultati** dell'analisi (video tagliati, report, grafici). 

    * **3. Scegli il Metodo di Rilevamento**: 
        * **YOLO**: Più moderno e accurato, ma richiede un file modello (`.pt`). 
        * **Hough Circle**: Meno accurato, ma non richiede file esterni. 

    * **4. Seleziona il Modello YOLO (se necessario)**: Se hai scelto YOLO, un'opzione aggiuntiva apparirà.  Clicca su "Seleziona..." per trovare e caricare il tuo file modello `.pt`. 

3.  **Avvia l'Analisi**:
    Una volta configurati tutti i percorsi, il pulsante **"Avvia Analisi Completa"** diventerà cliccabile.  Premilo per iniziare il processo. 

4.  **Monitora il Progresso**:
    Puoi seguire ogni fase dell'elaborazione nel riquadro **"Log di Analisi"** in tempo reale. 

---

## 📊 Output del Progetto

Al termine dell'analisi, troverai i seguenti file nella cartella di Output che hai scelto:

* **`final_report.xlsx`**: Il report quantitativo finale con tutte le metriche chiave, suddiviso per protocollo ("fast", "slow") e direzione del movimento. 
* **`output_final_analysis.mp4`**: Un video di riferimento con le annotazioni del rilevamento della palla e dello sguardo, utile per una revisione qualitativa. 
* **`output_final_analysis_analysis.csv`**: I dati grezzi, frame per frame, calcolati dalla pipeline. 
* **`cut_points.csv`**: I frame di inizio/fine dei segmenti "fast" e "slow". 
* **`trimmed_video_fast.mp4` / `trimmed_video_slow.mp4`**: I clip video dei singoli protocolli. 
* **Cartella `plots_and_heatmaps/`**: Contiene le visualizzazioni grafiche, incluse le heatmap dello sguardo e i grafici sulla pupillometria. 