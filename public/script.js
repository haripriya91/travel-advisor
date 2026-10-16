
let conversationId = null;
let busy = false;
let currentItinerary = null;
let activeView = "chat";
let toastTimeout = null;

const $ = (id) => document.getElementById(id);

const messagesEl = $("messages");
const conversationsEl = $("conversations");
const form = $("chatForm");
const input = $("messageInput");
const statusEl = $("status");
const itineraryEl = $("itinerary");
const itinerarySection = $("itinerarySection");
const sendButton = $("sendButton");
const newTripButton = $("newTrip");

const chatTab = $("chatTab");
const itineraryTab = $("itineraryTab");
const weatherTab = $("weatherTab");
const currencyTab = $("currencyTab");
const weatherSection = $("weatherSection");
const currencySection = $("currencySection");

const weatherForm = $("weatherForm");
const currencyForm = $("currencyForm");

const chatView = $("chatView");
const usageSection = $("usageSection");
const itineraryBadge = $("itineraryBadge");
const backToChat = $("backToChat");
const toast = $("toast");

const refreshUsageButton = $("refreshUsage");
const sidebarUsageButton = $("sidebarUsageButton");
const downloadButton = $("downloadMarkdown");


// -------------------------------------------
// API helper
// -------------------------------------------

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;

    try {
      const error = await response.json();

      detail = typeof error.detail === "string"
        ? error.detail
        : JSON.stringify(error.detail || error);
    } catch (_) {
      // Keep the HTTP error message.
    }

    throw new Error(detail);
  }

  return response.json();
}


// -------------------------------------------
// UI helpers
// -------------------------------------------

function addText(parent, tag, value, className = "") {
  const element = document.createElement(tag);
  element.textContent = value ?? "";

  if (className) {
    element.className = className;
  }

  parent.appendChild(element);
  return element;
}

function setBusy(value) {
  busy = value;

  sendButton.disabled = value;
  newTripButton.disabled = value;
  input.disabled = value;

  if (value) {
    statusEl.textContent =
      "TravelAdvisor is planning your journey...";
  } else if (
    statusEl.textContent ===
    "TravelAdvisor is planning your journey..."
  ) {
    statusEl.textContent = "";
  }
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;

  clearTimeout(toastTimeout);

  toastTimeout = setTimeout(() => {
    toast.hidden = true;
  }, 4500);
}

function showView(view) {
  activeView = view;

  const tabs = document.querySelector(".tabs");
  tabs.hidden = view === "usage";

  chatView.hidden = view !== "chat";
  itinerarySection.hidden = view !== "itinerary";
  weatherSection.hidden = view !== "weather";
  currencySection.hidden = view !== "currency";
  usageSection.hidden = view !== "usage";

  chatTab.classList.toggle("active", view === "chat");
  itineraryTab.classList.toggle("active", view === "itinerary");
  weatherTab.classList.toggle("active", view === "weather");
  currencyTab.classList.toggle("active", view === "currency");

  sidebarUsageButton.classList.toggle("active", view === "usage");

  if (view === "usage") {
    loadUsage();
  }

  if (view === "itinerary" && !currentItinerary) {
    showView("chat");
    showToast("Your itinerary will appear once it's ready.");
  }
}

// -------------------------------------------
// Tab navigation
// -------------------------------------------

chatTab.addEventListener("click", () => {
  showView("chat");
});

itineraryTab.addEventListener("click", () => {
  showView("itinerary");
});

sidebarUsageButton.addEventListener("click", () => {
  showView("usage");
});

backToChat.addEventListener("click", () => {
  showView("chat");
});

refreshUsageButton.addEventListener("click", () => {
  loadUsage();
});

weatherTab.addEventListener("click", () => {
  showView("weather");
});

currencyTab.addEventListener("click", () => {
  showView("currency");
});

// -------------------------------------------
// Weather Forecast
// -------------------------------------------

weatherForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const city = $("weatherCity").value.trim();
  const startDate = $("weatherStartDate").value;
  const days = Number($("weatherDays").value);

  const status = $("weatherStatus");
  const results = $("weatherResults");

  results.replaceChildren();
  status.textContent = "";

  if (!city || !startDate || days < 1 || days > 16) {
    status.textContent = "Please enter valid weather details.";
    return;
  }

  status.textContent = "Loading weather forecast...";

  try {
    const data = await api("/api/tools/weather", {
      method: "POST",
      body: JSON.stringify({
        city,
        start_date: startDate,
        days,
      }),
    });

    if (data.error) {
      throw new Error(data.error);
    }

    status.textContent = `Forecast for ${data.location}`;

    if (!data.forecast || data.forecast.length === 0) {
      addText(results, "p", "No forecast data is available.");
      return;
    }

    const table = document.createElement("table");
    const header = document.createElement("tr");

    [
      "Date",
      "Conditions",
      "Min °C",
      "Max °C",
      "Rain chance",
    ].forEach((heading) => {
      addText(header, "th", heading);
    });

    table.appendChild(header);

    for (const day of data.forecast) {
      const row = document.createElement("tr");

      addText(row, "td", day.date);
      addText(row, "td", day.conditions);
      addText(row, "td", `${day.temp_min_c}°`);
      addText(row, "td", `${day.temp_max_c}°`);
      addText(row, "td", `${day.rain_chance_percent}%`);

      table.appendChild(row);
    }

    results.appendChild(table);

    addText(
      results,
      "p",
      "Forecast availability depends on the selected date and the weather provider."
    );
  } catch (error) {
    status.textContent = `Could not load forecast: ${error.message}`;
  }
}); 

// -------------------------------------------
// Currency Converter
// -------------------------------------------

currencyForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const amount = Number($("currencyAmount").value);
  const fromCurrency = $("fromCurrency").value;
  const toCurrency = $("toCurrency").value;

  const status = $("currencyStatus");
  const results = $("currencyResults");

  results.replaceChildren();
  status.textContent = "";

  if (!Number.isFinite(amount) || amount <= 0) {
    status.textContent = "Please enter an amount greater than zero.";
    return;
  }

  status.textContent = "Converting currency...";

  try {
    const data = await api("/api/tools/currency", {
      method: "POST",
      body: JSON.stringify({
        amount,
        from_currency: fromCurrency,
        to_currency: toCurrency,
      }),
    });

    if (data.error) {
      throw new Error(data.error);
    }

    if (data.converted == null) {
      throw new Error("The exchange rate is unavailable.");
    }

    status.textContent = "Conversion complete";

    addText(
      results,
      "h2",
      `${formatAmount(data.amount)} ${data.from} = ` +
      `${formatAmount(data.converted)} ${data.to}`
    );

    if (data.rate_date) {
      addText(
        results,
        "p",
        `Exchange-rate date: ${data.rate_date}`
      );
    }

    addText(
      results,
      "p",
      "Your bank or card provider may use a different exchange rate."
    );
  } catch (error) {
    status.textContent = `Conversion failed: ${error.message}`;
  }
});


// -------------------------------------------
// Chat messages
// -------------------------------------------

function renderMessages(messages) {
  messagesEl.replaceChildren();

  if (!messages || messages.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-chat";

    addText(empty, "div", "🌴", "empty-icon");
    addText(empty, "h2", "Let's plan something memorable!");
    addText(
      empty,
      "p",
      "Tell me your destination, travel dates, or interests."
    );

    messagesEl.appendChild(empty);
    return;
  }

  for (const message of messages) {
    addText(
      messagesEl,
      "div",
      message.content,
      `message ${message.role}`
    );
  }

  messagesEl.scrollTop = messagesEl.scrollHeight;
}


// -------------------------------------------
// Itinerary rendering
// -------------------------------------------

function renderItinerary(itinerary) {
  currentItinerary = itinerary;
  itineraryEl.replaceChildren();

  itineraryBadge.hidden = !itinerary;
  downloadButton.disabled = !itinerary;

  if (!itinerary) {
    if (activeView === "itinerary") {
      showView("chat");
    }
    return;
  }

  addText(itineraryEl, "h2", itinerary.title);
  addText(
    itineraryEl,
    "p",
    itinerary.summary,
    "itinerary-summary"
  );

  // Days and activities
  for (const day of itinerary.days || []) {
    const dayEl = document.createElement("div");
    dayEl.className = "day";

    addText(
      dayEl,
      "h3",
      `Day ${day.day}: ${day.title}`
    );

    for (const activity of day.activities || []) {
      const activityEl = document.createElement("div");
      activityEl.className = "activity";

      addText(
        activityEl,
        "strong",
        `${activity.time} — ${activity.title}`
      );

      addText(
        activityEl,
        "p",
        activity.description
      );

      if (activity.estimated_cost != null) {
        addText(
          activityEl,
          "small",
          `Estimated cost: ${formatAmount(activity.estimated_cost)} ${itinerary.currency || ""}`
        );
      }

      dayEl.appendChild(activityEl);
    }

    itineraryEl.appendChild(dayEl);
  }

  // Practical tips
  if (itinerary.practical_tips?.length) {
    const tipsCard = document.createElement("div");
    tipsCard.className = "itinerary-tips";

    addText(tipsCard, "h3", "💡 Practical Tips");

    const list = document.createElement("ul");

    for (const tip of itinerary.practical_tips) {
      addText(list, "li", tip);
    }

    tipsCard.appendChild(list);
    itineraryEl.appendChild(tipsCard);
  }

  // Budget
  if (itinerary.estimated_budget != null) {
    const budgetCard = document.createElement("div");
    budgetCard.className = "budget-card";

    addText(budgetCard, "h3", "💰 Estimated Budget");

    addText(
      budgetCard,
      "div",
      `${formatAmount(itinerary.estimated_budget)} ${itinerary.currency || ""}`,
      "budget-value"
    );

    addText(
      budgetCard,
      "p",
      itinerary.budget_basis || "Estimated travel budget"
    );

    itineraryEl.appendChild(budgetCard);
  }
}

function formatAmount(value) {
  const number = Number(value);
  return Number.isFinite(number)
    ? number.toFixed(2)
    : String(value ?? "");
}


// -------------------------------------------
// Markdown export
// -------------------------------------------

function buildItineraryMarkdown(itinerary) {
  const lines = [
    `# ${itinerary.title}`,
    "",
    itinerary.summary || "",
    "",
  ];

  for (const day of itinerary.days || []) {
    lines.push(
      `## Day ${day.day}: ${day.title}`,
      ""
    );

    for (const activity of day.activities || []) {
      lines.push(
        `### ${activity.time} — ${activity.title}`,
        "",
        activity.description || "",
        "",
        `Estimated activity cost: ${formatAmount(activity.estimated_cost)} ${itinerary.currency || ""}`,
        ""
      );
    }
  }

  lines.push("## Practical Tips", "");

  for (const tip of itinerary.practical_tips || []) {
    lines.push(`- ${tip}`);
  }

  lines.push(
    "",
    "## Estimated Budget",
    "",
    `${formatAmount(itinerary.estimated_budget)} ${itinerary.currency || ""}`,
    "",
    itinerary.budget_basis || "Estimated travel budget"
  );

  return lines.join("\n");
}

downloadButton.addEventListener("click", () => {
  if (!currentItinerary) return;

  const markdown = buildItineraryMarkdown(currentItinerary);

  const blob = new Blob(
    [markdown],
    { type: "text/markdown;charset=utf-8" }
  );

  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = "traveladvisor_itinerary.md";

  document.body.appendChild(link);
  link.click();
  link.remove();

  URL.revokeObjectURL(url);
});


// -------------------------------------------
// API Usage dashboard
// -------------------------------------------

async function loadUsage() {
  const note = $("usageNote");

  note.textContent = "Loading usage statistics...";

  try {
    const usage = await api("/api/usage");

    const requests = Number(usage.request_count || 0);
    const tokens = Number(usage.total_tokens || 0);
    const priced = Number(usage.priced_requests || 0);

    $("totalRequests").textContent =
      requests.toLocaleString();

    $("totalTokens").textContent =
      tokens.toLocaleString();

    // Same logic as the old Streamlit application.
    if (priced === requests) {
      const cost = Number(usage.total_cost_usd || 0);

      $("totalCost").textContent =
        `$${cost.toFixed(6)}`;

      note.textContent =
        "All recorded requests have configured pricing. " +
        "The cost shown is an estimate, not an invoice.";
    } else {
      $("totalCost").textContent = "Unavailable";

      note.textContent =
        "Total cost unavailable: some models do not " +
        "have configured pricing. " +
        `${priced} of ${requests} requests have pricing data.`;
    }
  } catch (error) {
    $("totalRequests").textContent = "—";
    $("totalTokens").textContent = "—";
    $("totalCost").textContent = "—";

    note.textContent =
      `Could not load usage statistics: ${error.message}`;
  }
}


// -------------------------------------------
// Saved conversations
// -------------------------------------------

async function loadConversations() {
  const conversations = await api("/api/conversations");

  conversationsEl.replaceChildren();

  if (!conversations.length) {
    addText(
      conversationsEl,
      "p",
      "Start a new trip to begin.",
      "sidebar-empty"
    );
    return;
  }

  for (const conversation of conversations) {
    const button = addText(
      conversationsEl,
      "button",
      conversation.title,
      "trip-button"
    );

    button.type = "button";

    if (conversation.id === conversationId) {
      button.classList.add("active");
    }

    button.addEventListener("click", () => {
      if (!busy) {
        openConversation(conversation.id);
      }
    });
  }
}

async function openConversation(id) {
  try {
    const data = await api(
      `/api/conversations/${encodeURIComponent(id)}`
    );

    conversationId = id;

    renderMessages(data.messages);
    renderItinerary(data.itinerary);

    showView("chat");

    await loadConversations();
  } catch (error) {
    statusEl.textContent = error.message;
  }
}


// -------------------------------------------
// Create a new trip
// -------------------------------------------

function newConversation() {
  if (busy) return;

  // Do not create a database record yet.
  conversationId = null;

  input.value = "";
  statusEl.textContent = "";

  renderMessages([]);
  renderItinerary(null);
  showView("chat");

  // Remove the selected styling from saved conversations.
  document.querySelectorAll(".trip-button").forEach(button => {
    button.classList.remove("active");
  });

  input.focus();
}

async function createConversationInDatabase() {
  const data = await api("/api/conversations", {
    method: "POST",
  });

  conversationId = data.conversation_id;

  return conversationId;
}

newTripButton.addEventListener("click", newConversation);

// -------------------------------------------
// Send chat message
// -------------------------------------------

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = input.value.trim();

  if (!message || busy) return;

  statusEl.textContent = "";
  setBusy(true);

  try {
    if (!conversationId) {
      await createConversationInDatabase();
    }

    const itineraryWasReady = Boolean(currentItinerary);

    const data = await api(
      `/api/conversations/${encodeURIComponent(conversationId)}/messages`,
      {
        method: "POST",
        body: JSON.stringify({ message }),
      }
    );

    input.value = "";

    renderMessages(data.messages);
    renderItinerary(data.itinerary);

    if (data.itinerary && !itineraryWasReady) {
      showView("itinerary");
      showToast("🎉 Your itinerary is ready!");
    } else if (data.itinerary && itineraryWasReady) {
      showToast("Your trip plan has been updated.");
    } else {
      showView("chat");
    }

    await loadConversations();

  } catch (error) {
    statusEl.textContent = error.message;

    showToast(
      "Could not process your message. Check your conversation history before retrying."
    );
  } finally {
    setBusy(false);
  }
});
 

// Default weather date: today's local date
const today = new Date();
const localToday = [
  today.getFullYear(),
  String(today.getMonth() + 1).padStart(2, "0"),
  String(today.getDate()).padStart(2, "0"),
].join("-");

$("weatherStartDate").value = localToday;
$("weatherStartDate").min = localToday;

// -------------------------------------------
// Initialize application
// -------------------------------------------

async function initialize() {
  try {
    const conversations = await api("/api/conversations");

    if (conversations.length) {
      await openConversation(conversations[0].id);
    } else {
      newConversation();
      await loadConversations();
    }
  } catch (error) {
    statusEl.textContent = error.message;
  }
}

initialize();
