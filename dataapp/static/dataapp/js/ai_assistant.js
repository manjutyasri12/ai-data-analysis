(function () {
    const shell = document.querySelector(".assistant-shell");
    const form = document.getElementById("ai-chat-form");
    const input = document.getElementById("ai-chat-input");
    const log = document.getElementById("ai-chat-log");
    const status = document.getElementById("ai-chat-status");
    const clearButton = document.getElementById("ai-chat-clear");
    const askButton = form ? form.querySelector(".ask-button") : null;
    const endpoint = shell ? shell.dataset.aiChatUrl : "/ai-chat/";

    const friendlyMessages = {
        missing_api_key: "Gemini API key is missing. Add GEMINI_API_KEY to your .env file.",
        invalid_api_key: "Gemini API key is invalid. Check GEMINI_API_KEY in your .env file.",
        quota_exceeded: "Gemini quota exceeded. Please wait or check your Google AI billing/quota.",
        gemini_unavailable: "Gemini is unavailable right now. Please try again shortly.",
        empty_question: "Please type a question before asking Gemini.",
        dataset_not_loaded: "Dataset not loaded. Please upload a CSV dataset first.",
        timeout: "Gemini took too long to respond. Try a shorter question.",
        package_missing: "Gemini package is unavailable. Install google-generativeai.",
        invalid_payload: "The chat request was invalid. Refresh the page and try again.",
        empty_response: "Gemini returned an empty response. Please try again.",
        incomplete_response: "Gemini stopped before completing the answer. Please ask a narrower question.",
        missing_statistics: "Statistics are not available yet. Open the Statistics page after uploading a dataset.",
        missing_models: "Model results are not available yet. Train models first, then ask Gemini again.",
    };

    function getCsrfToken() {
        const field = document.querySelector("input[name='csrfmiddlewaretoken']");
        if (field && field.value) {
            return field.value;
        }
        const cookie = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith("csrftoken="));
        return cookie ? decodeURIComponent(cookie.split("=")[1]) : "";
    }

    function escapeHtml(value) {
        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function setStatus(message) {
        if (status) {
            status.textContent = message;
        }
    }

    function scrollToBottom() {
        if (log) {
            log.scrollTop = log.scrollHeight;
        }
    }

    function appendMessage(role, message, isError) {
        if (!log) return null;
        const row = document.createElement("div");
        row.className = `chat-message chat-message-${role}`;

        const bubble = document.createElement("div");
        bubble.className = "chat-bubble";
        bubble.innerHTML = isError ? `<span class="chat-error">${escapeHtml(message)}</span>` : escapeHtml(message);

        row.appendChild(bubble);
        log.appendChild(row);
        scrollToBottom();
        return row;
    }

    function appendLoading() {
        if (!log) return null;
        const row = document.createElement("div");
        row.className = "chat-message chat-message-ai";
        row.innerHTML = `
            <div class="chat-bubble">
                <span class="loading-dots" aria-label="Gemini is thinking">
                    <span></span><span></span><span></span>
                </span>
            </div>
        `;
        log.appendChild(row);
        scrollToBottom();
        return row;
    }

    function errorMessage(data, fallback) {
        if (data && data.status && friendlyMessages[data.status]) {
            return friendlyMessages[data.status];
        }
        return (data && (data.error || data.response)) || fallback || "Gemini is unavailable right now. Please try again shortly.";
    }

    async function askGemini(question) {
        const controller = new AbortController();
        const timeoutId = window.setTimeout(() => controller.abort(), 60000);
        let response;
        try {
            response = await fetch(endpoint, {
                method: "POST",
                credentials: "same-origin",
                signal: controller.signal,
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCsrfToken(),
                },
                body: JSON.stringify({ question }),
            });
        } catch (error) {
            if (error.name === "AbortError") {
                throw new Error(friendlyMessages.timeout);
            }
            throw new Error("Network error. Please try again.");
        } finally {
            window.clearTimeout(timeoutId);
        }

        const data = await response.json().catch(() => null);
        if (!response.ok || !data || !data.success) {
            throw new Error(errorMessage(data));
        }
        const answer = data.answer || data.response || "";
        if (!answer.trim()) {
            throw new Error(friendlyMessages.empty_response);
        }
        return answer;
    }

    function setBusy(isBusy) {
        if (askButton) {
            askButton.disabled = isBusy;
            askButton.textContent = isBusy ? "Asking..." : "Ask AI";
        }
        if (input) {
            input.disabled = isBusy;
        }
    }

    if (form) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const question = input ? input.value.trim() : "";
            if (!question) {
                setStatus(friendlyMessages.empty_question);
                appendMessage("ai", friendlyMessages.empty_question, true);
                return;
            }

            appendMessage("user", question);
            input.value = "";
            setBusy(true);
            setStatus("Gemini is thinking...");
            const loading = appendLoading();

            try {
                const answer = await askGemini(question);
                if (loading) loading.remove();
                appendMessage("ai", answer);
                setStatus("Gemini answered successfully.");
            } catch (error) {
                if (loading) loading.remove();
                appendMessage("ai", error.message, true);
                setStatus(error.message);
            } finally {
                setBusy(false);
                if (input) input.focus();
            }
        });
    }

    document.querySelectorAll(".quick-question").forEach(function (button) {
        button.addEventListener("click", function () {
            if (!input) return;
            input.value = button.dataset.prompt || button.textContent.trim();
            input.focus();
        });
    });

    if (clearButton) {
        clearButton.addEventListener("click", function () {
            if (log) {
                log.innerHTML = "";
            }
            setStatus("Chat cleared.");
            if (input) input.focus();
        });
    }
})();
