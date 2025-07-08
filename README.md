# Strumento di Analisi Neuro-Visuale - LabSCoC

Questo repository contiene una pipeline software completa per l'analisi del movimento oculare in relazione al movimento di una palla, sviluppata per il **Laboratorio di Scienze Cognitive e del Comportamento (LabSCoC)**.

L'intero processo è gestito da un'unica **interfaccia grafica (GUI)** che orchestra l'elaborazione dei dati, dal taglio dei video grezzi fino alla generazione di un report statistico finale.

- **Sito Web Lab**: [labscoc.wordpress.com](https://labscoc.wordpress.com/)
- **Repository GitHub**: [github.com/danielelozzi/neurological-assessment](https://github.com/danielelozzi/neurological-assessment)

---

## 🎯 Obiettivo del Software

L'obiettivo è automatizzare e standardizzare l'analisi delle performance visuo-motorie. Partendo dai dati grezzi esportati dagli occhiali Tobii, il software:
1.  **Identifica e isola** i segmenti di interesse del test ("fast" e "slow").
2.  **Rileva la palla** e ne traccia il movimento nel video.
3.  **Sincronizza i dati dello sguardo** con la posizione della palla.
4.  **Calcola metriche chiave** come la velocità dello sguardo, la velocità della palla e la percentuale di tempo in cui lo sguardo è correttamente sulla palla.
5.  **Produce un report Excel dettagliato** e visualizzazioni grafiche (heatmap, grafici pupillometrici) per un'analisi approfondita.

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

L'intera pipeline viene eseguita tramite l'interfaccia grafica. Non è più necessario lanciare gli script singolarmente.

1.  **Avvia la GUI**:
    Esegui il seguente comando dalla directory principale del progetto:
    ```bash
    python main_gui.py
    ```

2.  **Configura l'Analisi**:
    Dalla finestra dell'applicazione, segui questi passaggi:

    * **1. Seleziona la Cartella Input**: Clicca su "Seleziona..." e scegli la cartella che contiene **tutti i file esportati da Tobii** (`video.mp4`, `gaze.csv`, `surface_positions.csv`, etc.).

    * **2. Seleziona la Cartella Output**: Clicca su "Seleziona..." e scegli una cartella (anche vuota) dove verranno salvati **tutti i risultati** dell'analisi (video tagliati, report, grafici).

    * **3. Scegli il Metodo di Rilevamento**:
        * **YOLO**: Più moderno e accurato, ma richiede un file modello (`.pt`).
        * **Hough Circle**: Meno accurato, ma non richiede file esterni.

    * **4. Seleziona il Modello YOLO (se necessario)**: Se hai scelto YOLO, un'opzione aggiuntiva apparirà. Clicca su "Seleziona..." per trovare e caricare il tuo file modello `.pt`.

3.  **Avvia l'Analisi**:
    Una volta configurati tutti i percorsi, il pulsante **"Avvia Analisi Completa"** diventerà cliccabile. Premilo per iniziare il processo.

4.  **Monitora il Progresso**:
    Puoi seguire ogni fase dell'elaborazione nel riquadro **"Log di Analisi"** in tempo reale. La GUI rimarrà reattiva, ma il pulsante di avvio sarà disabilitato fino al termine dell'analisi.

---

## 📊 Output del Progetto

Al termine dell'analisi, troverai i seguenti file nella cartella di Output che hai scelto:

* **`final_report.xlsx`**: Il report quantitativo finale con tutte le metriche chiave, suddiviso per protocollo ("fast", "slow") e direzione del movimento.
* **`output_final_analysis.mp4`**: Un video di riferimento con le annotazioni del rilevamento della palla e dello sguardo, utile per una revisione qualitativa.
* **`output_final_analysis_analysis.csv`**: I dati grezzi, frame per frame, calcolati dalla pipeline.
* **`cut_points.csv`**: I frame di inizio/fine dei segmenti "fast" e "slow".
* **`trimmed_video_fast.mp4` / `trimmed_video_slow.mp4`**: I clip video dei singoli protocolli.
* **Cartella `plots_and_heatmaps/`**: Contiene le visualizzazioni grafiche, incluse le heatmap dello sguardo e i grafici sulla pupillometria.