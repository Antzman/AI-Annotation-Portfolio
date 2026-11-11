document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("[data-quality-form]");
  const scoreOutput = document.querySelector("[data-quality-live-score]");
  const scoreHint = document.querySelector("[data-quality-score-hint]");
  if (!form || !scoreOutput || !scoreHint) return;

  const scoreInputs = Array.from(form.querySelectorAll(".quality-score-input"));
  const updateScore = () => {
    const completeScores = scoreInputs
      .map((input) => {
        const category = input.name.replace("score_", "");
        const explanation = form.querySelector(
          `[name="explanation_${category}"]`,
        );
        const score = Number(input.value);
        return input.value && explanation.value.trim() ? score : null;
      })
      .filter((score) => score !== null);

    if (completeScores.length === scoreInputs.length) {
      const average =
        completeScores.reduce((total, score) => total + score, 0) /
        completeScores.length;
      scoreOutput.textContent = `${average.toFixed(1)} / 10`;
      scoreHint.textContent = "Live mean; save to record this overall score.";
    } else {
      scoreOutput.textContent = `${completeScores.length} of ${scoreInputs.length} ratings complete`;
      scoreHint.textContent =
        "The score is available after all five ratings and explanations are complete.";
    }
  };

  form.addEventListener("input", updateScore);
  form.addEventListener("change", updateScore);
  updateScore();
});
