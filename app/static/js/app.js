document.addEventListener("DOMContentLoaded", function(){
    const form = document.getElementById("parseForm");

    form.addEventListener("submit", function(e){
        e.preventDefault();

        const text = document.getElementById("text").value;

        fetch("/smart_parse", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: text})
        })
        .then(res => res.json())
        .then(data => {
            displayResults(data);
        })
        .catch(err => {
            console.error(err);
            alert("Fehler beim Verarbeiten des Textes.")
        })
    })

    function displayResults(events){
        const container = document.getElementById("results");
        container.innerHTML = "";

        if(!events || events.length === 0){
            container.innerHTML = "<p>Keine Termine erkannt.</p>";
            return;
        }

        events.forEach(event => {
            const div = document.createElement("div");
            div.classList.add("event-card");

            div.innerHTML = `
                <h3>Termin</h3>
                <p><strong>Titel:</strong> ${event.title}</p>
                <p><strong>Start:</strong> ${event.start_date}</p>
                <p><strong>Ende:</strong> ${event.end_date}</p>
                <p><strong>Start Zeit:</strong> ${event.start_time}</p>
                <p><strong>Ende Zeit:</strong> ${event.end_time}</p>
                <p><strong>Trainer:</strong> ${event.trainer}</p>
                <p><strong>Ort:</strong> ${event.location}</p>
                <p><strong>Text:</strong> ${event.raw}</p>

            `
            container.appendChild(div);
        })
    }
})