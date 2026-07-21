document.addEventListener("DOMContentLoaded", () => {
    const songInput = document.getElementById("song-search");
    const resultsBox = document.getElementById("song-results");

    const spotifyUriInput = document.getElementById("spotify-uri");
    const spotifyArtistInput = document.getElementById("spotify-artist");
    const spotifyImageInput = document.getElementById("spotify-image");

    songInput.addEventListener("input", () => {
        const query = songInput.value.trim();

        // Clear drop down and hide if search string is less than 2 characters
        if (query.length < 2) {
            resultsBox.innerHTML = "";
            resultsBox.style.display = "none";
            return;
        }

        // Call Flask search-song route with encoded user query
        fetch(`search-song?q=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(songs => {
                resultsBox.innerHTML = "";

                if (songs.length === 0) {
                    resultsBox.style.display = "none";
                    return;
                }

                songs.forEach(song => {
                    const item = document.createElement("div");
                    item.className = "song-result";

                    // Conditionally render album image asset securely
                    const imgTag = song.image ? `<img src="${song.image}" alt="Album art">` : "";

                    item.innerHTML = ` 
                        ${imgTag}
                        <div>
                            <div class="song-title">${song.name}</div>
                            <div class="song-artist text-muted small">${song.artist}</div>
                        </div>
                    `;
                    
                    item.addEventListener("click", () => {
                        songInput.value = song.name;
                        spotifyUriInput.value = song.uri;
                        spotifyArtistInput.value = song.artist;
                        spotifyImageInput.value = song.image || "";

                        resultsBox.innerHTML = "";
                        resultsBox.style.display = "none";
                    });

                    resultsBox.appendChild(item);                        
                });
                
                resultsBox.style.display = "block";
            })
            .catch(error => {
                console.error("Song search error: ", error);
                resultsBox.innerHTML = "";
                resultsBox.style.display = "none";
            });
    });
});



document.addEventListener("DOMContentLoaded", () => {
    const micBtn = document.getElementById("mic-btn");
    const notesField = document.getElementById("notes-field");
    const micStatus = document.getElementById("mic-status");

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        micBtn.disabled = true;
        micBtn.title = "Speech-to-text not supported in this browser";
        micBtn.classList.add("opacity-50");
        return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    let listening = false;
    let baseText = "";

    function formatText(text) {
        let formatted = text
            // Replace spoken punctuation
            .replace(/\bperiod\b/gi, ".")
            .replace(/\bcomma\b/gi, ",")
            .replace(/\bquestion mark\b/gi, "?")
            .replace(/\bexclamation point\b/gi, "!")
            .replace(/\bnew line\b/gi, "\n")
            .replace(/\bnew paragraph\b/gi, "\n\n");

            formatted = formatted
                .replace(/\s+([.,?!])/g, "$1") // "word . " -> "word."
                .replace(/([.,?!])(?=[^\s])/g, "$1 ");
                
        // Capitalize the first letter of sentences
        formatted = formatted.replace(/(^\s*|[.!?]\s+)([a-z])/g, (match, separator, letter) => {
            return separator + letter.toUpperCase();
        });

        return formatted;
    }

    micBtn.addEventListener("click", () => {
        if (listening) {
            recognition.stop();
            return;
        }
        baseText = notesField.value ? notesField.value + " " : "";
        recognition.start();
    });

    recognition.addEventListener("start", () => {
        listening = true;
        micBtn.classList.remove("btn-outline-secondary");
        micBtn.classList.add("btn-danger");
        micStatus.style.display = "block";
    });

    recognition.addEventListener("end", () => {
        listening = false;
        micBtn.classList.remove("btn-danger");
        micBtn.classList.add("btn-outline-secondary");
        micStatus.style.display = "none";
    });

    recognition.addEventListener("error", (event) => {
        console.error("Speech recognition error:", event.error);
        listening = false;
        micBtn.classList.remove("btn-danger");
        micBtn.classList.add("btn-outline-secondary");
        micStatus.style.display = "none";
    });

    recognition.addEventListener("result", (event) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript + " ";
            } else {
                interimTranscript += transcript;
            }
        }

        const rawOutput = baseText + finalTranscript + interimTranscript;
        notesField.value = formatText(rawOutput);

        if (finalTranscript) {
            baseText += finalTranscript;
        }
    });
});