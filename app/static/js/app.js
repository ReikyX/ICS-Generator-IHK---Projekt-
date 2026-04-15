document.addEventListener("DOMContentLoaded", function(){
    const form = document.getElementById("parseForm");
    const textArea = document.getElementById("text");
    const resultsContainer = document.getElementById("results");
    const downloadBtn = document.getElementById("downloadIcsBtn");

    const state = {
        lastParsedEvents: [],
        lastRawText: ""
    }

    bindEvents();

    function bindEvents(){
        form.addEventListener("submit", handleFormSubmit);

        downloadBtn.disabled = true;
        downloadBtn.addEventListener("click", handleDownloadIcs);
    }

    async function handleFormSubmit(e){
        e.preventDefault();

        const text = textArea.value.trim();
        if(!text){
            alert("Bitte geben Sie einen Text ein.");
            return;
        }

        state.lastRawText = text;

        try {
            const events = await fetchParsedEvents(text);
            state.lastParsedEvents = events;
            downloadBtn.disabled = !events || events.length === 0;

            renderEvents(events);
        } catch (error) {
            console.error("Fehler beim Verarbeiten des Textes:");
            downloadBtn.disabled = true;
        }
    }

    function renderEvents(events){
        resultsContainer.innerHTML = "";
        
        if(!events || events.length === 0){
            resultsContainer.innerHTML = "<p>Keine Termine erkannt.</p>";
            return;
        }

        const fragment = document.createDocumentFragment();

        events.forEach(event => {
            fragment.appendChild(createEventCard(event));
        });
        resultsContainer.appendChild(fragment);
    }

    function createEventCard(event){
        const div = document.createElement("div");
        div.classList.add("event-card");

        div.innerHTML = `
            <h3>${escapeHtml(event.title || "Termin")}</h3>
            <p><strong>Start:</strong> ${(event.start_date)}</p>
            <p><strong>Ende:</strong> ${(event.end_date)}</p>
            <p><strong>Start Zeit:</strong> ${event.start_time || "-"}</p>
            <p><strong>Ende Zeit:</strong> ${event.end_time || "-"}</p>
            <p><strong>Trainer:</strong> ${event.trainer || "-"}</p>
            <p><strong>Ort:</strong> ${event.location || "-"}</p>
            <p><strong>Beschreibung:</strong> ${escapeHtml(event.description || "-")}</p>

            <details>
                <summary>Originaltext</summary>
                <p>${escapeHtml(event.raw || "")}</p>
            </details>
        `;
        return div;
    }

    function escapeHtml(str) {
        return String(str)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#039;");
    }

    async function fetchParsedEvents(text){
        const response = await fetch("/smart_parse", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text })
        });
        if(!response.ok){
            throw new Error("Fehler beim Abrufen der Termine.");
        }

        return await response.json();
    }

    async function handleDownloadIcs(){
        if(!state.lastParsedEvents.length){
            alert("Bitte zuerst Termine erkennen lassen.");
            return;
        }
        try {
            const response = await fetch("/smart_ical", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: state.lastRawText })
            });

            if(!response.ok){
                throw new Error("Fehler beim Generieren der ICS-Datei.");
            }

            const blob = await response.blob();

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");

            a.href = url;
            a.download = "termine.ics";
            document.body.appendChild(a);
            a.click();

            a.remove();
            window.URL.revokeObjectURL(url);

            resetUI();
        }
        catch (error) {
            console.error("Fehler beim Herunterladen der ICS-Datei:", error);
            alert("Fehler beim Herunterladen der ICS-Datei. Bitte versuchen Sie es erneut.");
        }
    }

    function resetUI(){
        state.lastParsedEvents = [];
        state.lastRawText = "";
        document.getElementById("text").value = "";
        textArea.focus();
        resultsContainer.innerHTML = "<p>Export erfolgreich. Sie können neue Termine eingeben.</p>";
        downloadBtn.disabled = true;
    }
});