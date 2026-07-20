const toast = document.querySelector("#toast");

function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("visible");
  window.setTimeout(() => toast.classList.remove("visible"), 2600);
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || "Something went wrong");
  }
  return response.json();
}

document.querySelectorAll(".complete-capsule").forEach((button) => {
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "Saving…";
    try {
      await request(`/api/v1/demo/capsules/${button.dataset.capsuleId}/complete`, {
        method: "POST",
      });
      showToast("Move complete. Your journey is updated.");
      window.setTimeout(() => window.location.reload(), 550);
    } catch (error) {
      showToast(error.message);
      button.disabled = false;
      button.textContent = "Complete move →";
    }
  });
});

document.querySelectorAll("[data-mood-score]").forEach((button) => {
  button.addEventListener("click", async () => {
    const score = Number(button.dataset.moodScore);
    try {
      await request("/api/v1/demo/mood", {
        method: "POST",
        body: JSON.stringify({ score }),
      });
      document.querySelectorAll("[data-mood-score]").forEach((item) =>
        item.classList.toggle("selected", item === button),
      );
      showToast("Energy signal saved privately.");
    } catch (error) {
      showToast(error.message);
    }
  });
});

const journalForm = document.querySelector("#journal-form");
if (journalForm) {
  journalForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = journalForm.querySelector("button");
    const answer = new FormData(journalForm).get("answer");
    button.disabled = true;
    try {
      await request("/api/v1/demo/journal", {
        method: "POST",
        body: JSON.stringify({ answer }),
      });
      journalForm.reset();
      showToast("Reflection saved. Only you can read it.");
    } catch (error) {
      showToast(error.message);
    } finally {
      button.disabled = false;
    }
  });
}

const coachForm = document.querySelector("#coach-form");
if (coachForm) {
  coachForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = coachForm.querySelector("button");
    const answerNode = document.querySelector("#coach-answer");
    const modelNode = document.querySelector("#coach-model");
    const question = new FormData(coachForm).get("question");
    button.disabled = true;
    button.textContent = "Thinking…";
    answerNode.hidden = false;
    answerNode.textContent = "Finding the smallest useful next move…";
    try {
      const payload = await request("/api/v1/demo/coach", {
        method: "POST",
        body: JSON.stringify({ question }),
      });
      answerNode.textContent = payload.answer;
      modelNode.textContent = payload.live_model
        ? `Live response · ${payload.model}`
        : "Demo fallback · add OPENAI_API_KEY for live GPT‑5.6";
      coachForm.reset();
    } catch (error) {
      answerNode.textContent = error.message;
    } finally {
      button.disabled = false;
      button.textContent = "Ask coach ↗";
    }
  });
}

const resetButton = document.querySelector("#reset-demo");
if (resetButton) {
  resetButton.addEventListener("click", async () => {
    resetButton.disabled = true;
    try {
      await request("/api/v1/demo/reset", { method: "POST" });
      showToast("Demo restored to day 18.");
      window.setTimeout(() => window.location.reload(), 450);
    } catch (error) {
      showToast(error.message);
      resetButton.disabled = false;
    }
  });
}
