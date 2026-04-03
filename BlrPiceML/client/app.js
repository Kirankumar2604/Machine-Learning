const locationSelect = document.getElementById("location");
const form = document.getElementById("predict-form");
const priceEl = document.getElementById("price");
const statusEl = document.getElementById("status");
const predictBtn = document.getElementById("predict-btn");

const API_BASE_CANDIDATES = [
  "",
  "http://127.0.0.1:8080",
  "http://localhost:8080",
  "http://127.0.0.1:5000",
  "http://localhost:5000",
];

let activeApiBase = "";

const setStatus = (message) => {
  if (statusEl) statusEl.textContent = message;
};

const buildUrl = (base, path) => {
  if (!base) return path;
  return `${base}${path}`;
};

async function apiFetch(path, options = {}) {
  const bases = [activeApiBase, ...API_BASE_CANDIDATES].filter(
    (base, index, arr) => arr.indexOf(base) === index
  );

  let lastError;

  for (const base of bases) {
    try {
      const response = await fetch(buildUrl(base, path), options);
      if (response.ok) {
        activeApiBase = base;
      }
      return response;
    } catch (error) {
      lastError = error;
    }
  }

  throw lastError || new Error("Unable to connect to API");
}

const formatINR = (valueLakhs) => {
  if (!Number.isFinite(valueLakhs)) return "-";

  const rupees = valueLakhs * 100000;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(rupees);
};

async function loadLocations() {
  setStatus("Loading locations...");

  try {
    const response = await apiFetch("/get_location_names");
    if (!response.ok) {
      throw new Error("Could not fetch locations");
    }

    const data = await response.json();
    const locations = data.locations || [];
    const uiLocations = document.getElementById("uiLocations");

    const populateSelect = (selectEl) => {
      if (!selectEl) return;
      selectEl.innerHTML = '<option value="">Select location</option>';

      for (const location of locations) {
        const option = new Option(location, location);
        selectEl.appendChild(option);
      }
    };

    populateSelect(locationSelect);
    populateSelect(uiLocations);

    setStatus("");
  } catch (error) {
    setStatus("Failed to load locations. Start backend and open app on http://127.0.0.1:8080/");
  }
}

function onPageLoad() {
  console.log("document loaded");
  loadLocations();
}

async function handleSubmit(event) {
  event.preventDefault();

  const payload = {
    location: locationSelect.value,
    total_sqft: Number(document.getElementById("total_sqft").value),
    bath: Number(document.getElementById("bath").value),
    bhk: Number(document.getElementById("bhk").value),
  };

  if (!payload.location) {
    setStatus("Please select a location.");
    return;
  }

  predictBtn.disabled = true;
  predictBtn.textContent = "Predicting...";
  setStatus("");

  try {
    const response = await apiFetch("/predict_home_price", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Prediction failed");
    }

    priceEl.textContent = formatINR(data.predicted_price);
    setStatus("Prediction generated successfully.");
  } catch (error) {
    priceEl.textContent = "-";
    setStatus(error.message || "Prediction request failed.");
  } finally {
    predictBtn.disabled = false;
    predictBtn.textContent = "Predict Price";
  }
}

if (form) {
  form.addEventListener("submit", handleSubmit);
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", onPageLoad);
} else {
  onPageLoad();
}
