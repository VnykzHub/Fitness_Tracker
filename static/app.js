const $ = (id) => document.getElementById(id);
const today = new Date().toISOString().slice(0, 10);
$("date").value = today;

async function postJson(url, body) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

$("logToday").onclick = async () => {
  const payload = {
    date: $("date").value,
    weight: parseFloat($("weight").value || "0"),
    calories: parseInt($("calories").value || "0", 10),
    protein: parseInt($("protein").value || "0", 10),
    workout_done: $("workout").checked,
    consistency_score: parseFloat($("consistency").value || "0"),
    notes: $("notes").value,
  };
  const out = await postJson("/api/log/today", payload);
  $("logMsg").innerText = out.message;
};

$("logMeal").onclick = async () => {
  const payload = {
    date: $("date").value,
    meal_name: $("mealName").value,
    calories: parseInt($("mealCals").value || "0", 10),
    protein: parseInt($("mealProtein").value || "0", 10),
    source: "manual",
  };
  await postJson("/api/log/meal", payload);
  alert("Meal saved");
};

$("logThought").onclick = async () => {
  await postJson("/api/log/thought", { date: $("date").value, text: $("notes").value });
  alert("Thought saved");
};

$("uploadPhoto").onclick = async () => {
  const file = $("photo").files[0];
  if (!file) {
    alert("Pick photo first");
    return;
  }
  const fd = new FormData();
  fd.append("date_value", $("date").value);
  fd.append("caption", $("caption").value);
  fd.append("photo", file);
  await fetch("/api/log/photo", { method: "POST", body: fd });
  loadMilestone();
};

async function loadMilestone() {
  const m = await fetch("/api/milestone?days=30").then((r) => r.json());
  $("milestone").innerText = JSON.stringify(m, null, 2);
  $("montage").src = `/api/montage?days=30&t=${Date.now()}`;
}

$("refreshMilestone").onclick = loadMilestone;
loadMilestone();

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js");
}
