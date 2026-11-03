const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const messagesEl = $("#messages");
const input = $("#messageInput");
const sendButton = $("#sendBtn");
const typing = $("#typing");
const typingLabel = $("#typing small");
const cartModal = $("#cartModal");
const sidebar = $("#sidebar");
let activeConversationId = null;
let busy = false;
let lastFocusedElement = null;
let toastTimer = null;

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function renderMarkdownLite(value) {
  let safe = escapeHtml(value);
  safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
  safe = safe.replace(/^- (.*)$/gm, "• $1");
  return safe.replace(/\n/g, "<br>");
}

function showToast(message, kind = "info") {
  let toast = $("#appToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "appToast";
    toast.className = "app-toast";
    toast.setAttribute("role", "status");
    toast.setAttribute("aria-live", "polite");
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.dataset.kind = kind;
  toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("visible"), 3200);
}

function scrollBottom() {
  const pane = $("#chatScroll");
  if (pane) pane.scrollTo({ top: pane.scrollHeight, behavior: "auto" });
}

function appendMessage(role, content, products = []) {
  $("#welcome")?.classList.add("hidden");
  const article = document.createElement("article");
  article.className = `message-row ${role === "user" ? "user" : "assistant"}`;
  const label = role === "user" ? "You" : "ShopMate";
  const avatar = role === "user" ? "You" : "S";
  const cards = Array.isArray(products) && products.length
    ? `<div class="result-products">${products.slice(0, 8).map((product) => `
        <article class="result-card">
          <div class="result-image">
            <img src="${escapeHtml(product.image_url || "")}" alt="${escapeHtml(product.name)}" loading="lazy">
          </div>
          <div class="result-body">
            <span>${escapeHtml(product.category)}</span>
            <b>${escapeHtml(product.name)}</b>
            <strong>₹${Number(product.price || 0).toLocaleString("en-IN")}</strong>
            <small>★ ${escapeHtml(product.rating)} · ${escapeHtml(product.stock)} in stock</small>
            <button class="result-add" type="button" data-product-id="${Number(product.id)}">Add to cart</button>
          </div>
        </article>`).join("")}</div>`
    : "";

  article.innerHTML = `
    <div class="message-avatar ${role === "user" ? "user" : "assistant"}" aria-hidden="true">${avatar}</div>
    <div class="message-content">
      <div class="message-meta">${label}<span>${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span></div>
      <div class="bubble">${renderMarkdownLite(content)}</div>
      ${cards}
    </div>`;

  $$("img", article).forEach((image) => {
    image.addEventListener("error", () => {
      image.closest(".result-image")?.classList.add("image-failed");
      image.remove();
    }, { once: true });
  });
  messagesEl.appendChild(article);
  scrollBottom();
}

async function api(url, options = {}) {
  const { timeoutMs = url.includes("/messages") ? 60000 : 12000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      credentials: "same-origin",
      ...fetchOptions,
      headers: { "Content-Type": "application/json", ...(fetchOptions.headers || {}) },
      signal: controller.signal
    });
    if (response.status === 401) {
      window.location.assign("/login");
      throw new Error("Your session expired. Please sign in again.");
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status}).`);
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("That request took too long. Please try again.");
    }
    if (error instanceof TypeError) {
      throw new Error("Network connection problem. Check your connection and retry.");
    }
    throw error;
  } finally {
    window.clearTimeout(timer);
  }
}

function setBusy(value) {
  busy = value;
  sendButton.disabled = value;
  sendButton.setAttribute("aria-busy", String(value));
  input.setAttribute("aria-busy", String(value));
  typing.classList.toggle("hidden", !value);
}

async function ensureConversation() {
  if (activeConversationId) return activeConversationId;
  const conversation = await api("/api/conversations", { method: "POST", body: "{}" });
  activeConversationId = conversation.id;
  await refreshConversations();
  return activeConversationId;
}

async function sendMessage(value) {
  const message = String(value || "").trim();
  if (busy || !message) return;

  appendMessage("user", message);
  input.value = "";
  input.style.height = "auto";
  setBusy(true);
  typingLabel.textContent = "ShopMate is thinking…";

  try {
    const conversationId = await ensureConversation();
    const data = await api(`/api/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: message }),
      timeoutMs: 60000
    });
    appendMessage("assistant", data.reply || "I couldn't generate a response. Please try again.", data.products || []);
    await Promise.allSettled([refreshConversations(), refreshCartCount()]);
  } catch (error) {
    appendMessage("assistant", error.message || "I couldn't complete that request. Please try again.");
    showToast(error.message || "Message failed. Please try again.", "error");
  } finally {
    setBusy(false);
    input.focus();
  }
}

async function refreshConversations() {
  const rows = await api("/api/conversations");
  const list = $("#conversationList");
  list.replaceChildren();
  rows.forEach((conversation) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "conversation-link" + (conversation.id === activeConversationId ? " active" : "");
    button.dataset.id = conversation.id;
    button.innerHTML = `<span class="chat-dot" aria-hidden="true"></span><span class="conversation-title">${escapeHtml(conversation.title)}</span>`;
    button.addEventListener("click", () => loadConversation(conversation.id));
    list.appendChild(button);
  });
}

async function loadConversation(id) {
  if (busy) return;
  try {
    const data = await api(`/api/conversations/${id}`);
    activeConversationId = id;
    messagesEl.replaceChildren();
    $("#welcome").classList.toggle("hidden", data.messages.length > 0);
    (data.messages || []).slice(-80).forEach((message) => appendMessage(message.role, message.content));
    await refreshConversations();
    closeSidebar();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function newConversation() {
  if (busy) return;
  activeConversationId = null;
  messagesEl.replaceChildren();
  $("#welcome").classList.remove("hidden");
  await refreshConversations().catch((error) => showToast(error.message, "error"));
  closeSidebar();
  input.focus();
}

function openSidebar() {
  sidebar.classList.add("mobile-open");
  $("#mobileMenu").setAttribute("aria-expanded", "true");
  $("#sidebarScrim")?.classList.add("visible");
}
function closeSidebar() {
  sidebar.classList.remove("mobile-open");
  $("#mobileMenu").setAttribute("aria-expanded", "false");
  $("#sidebarScrim")?.classList.remove("visible");
}

async function addToCart(productId, button) {
  if (button?.disabled) return;
  if (button) button.disabled = true;
  try {
    await api("/api/cart", {
      method: "POST",
      body: JSON.stringify({ product_id: Number(productId), quantity: 1 })
    });
    await refreshCartCount();
    showToast("Added to your cart.", "success");
    if (button) button.textContent = "Added ✓";
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    if (button) button.disabled = false;
  }
}

async function refreshCartCount() {
  const cart = await api("/api/cart");
  $("#cartCount").textContent = Number(cart.count || 0);
}

function closeCart() {
  cartModal.classList.add("hidden");
  cartModal.setAttribute("aria-hidden", "true");
  lastFocusedElement?.focus?.();
}

async function showCart() {
  try {
    const cart = await api("/api/cart");
    const host = $("#cartItems");
    if (!cart.items.length) {
      host.innerHTML = `<div class="empty-cart">Your cart is empty.<br><small>Ask ShopMate to find something you’ll love.</small></div>`;
    } else {
      host.innerHTML = cart.items.map((row) => `
        <div class="cart-row">
          <div><b>${escapeHtml(row.product.name)}</b><small>₹${Number(row.product.price).toLocaleString("en-IN")} × ${Number(row.quantity)}</small></div>
          <button class="remove-cart" type="button" data-item-id="${Number(row.id)}">Remove</button>
        </div>`).join("");
    }
    const subtotal = cart.items.reduce((sum, row) => sum + Number(row.product.price) * Number(row.quantity), 0);
    $("#cartTotal").textContent = "₹" + subtotal.toLocaleString("en-IN");
    lastFocusedElement = document.activeElement;
    cartModal.classList.remove("hidden");
    cartModal.setAttribute("aria-hidden", "false");
    $("#closeCart").focus();
  } catch (error) {
    showToast(error.message, "error");
  }
}

async function refreshFeatured() {
  const button = $("#refreshProducts");
  button.disabled = true;
  button.classList.add("is-loading");
  try {
    const products = await api("/api/products");
    const host = $("#featuredProducts");
    if (!products.length) {
      host.innerHTML = '<div class="empty-cart">No products are available right now.</div>';
      return;
    }
    host.innerHTML = products.slice(0, 5).map((product) => `
      <article class="mini-product">
        <div class="mini-image"><img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.name)}" loading="lazy"></div>
        <div class="mini-info">
          <span>${escapeHtml(product.category)}</span>
          <b>${escapeHtml(product.name)}</b>
          <strong>₹${Number(product.price).toLocaleString("en-IN")}</strong>
          <small>★ ${escapeHtml(product.rating)} · ${escapeHtml(product.stock)} in stock</small>
        </div>
        <button class="mini-add" type="button" data-product-id="${Number(product.id)}" aria-label="Add ${escapeHtml(product.name)} to cart">＋</button>
      </article>`).join("");
    host.querySelectorAll("img").forEach((image) => image.addEventListener("error", () => {
      image.closest(".mini-image")?.classList.add("image-failed");
      image.remove();
    }, { once: true }));
  } catch (error) {
    showToast(error.message, "error");
  } finally {
    button.disabled = false;
    button.classList.remove("is-loading");
  }
}

sendButton.addEventListener("click", () => sendMessage(input.value));
input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    sendMessage(input.value);
  }
});
input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 180) + "px";
});

$("#newChatBtn").addEventListener("click", newConversation);
$("#cartButton").addEventListener("click", showCart);
$("#closeCart").addEventListener("click", closeCart);
cartModal.addEventListener("click", (event) => {
  if (event.target === cartModal) closeCart();
});
$("#refreshProducts").addEventListener("click", refreshFeatured);
$("#mobileMenu").addEventListener("click", () => {
  sidebar.classList.contains("mobile-open") ? closeSidebar() : openSidebar();
});

if (!$("#sidebarScrim")) {
  const scrim = document.createElement("button");
  scrim.id = "sidebarScrim";
  scrim.className = "sidebar-scrim";
  scrim.type = "button";
  scrim.setAttribute("aria-label", "Close navigation");
  scrim.addEventListener("click", closeSidebar);
  document.body.appendChild(scrim);
}

document.addEventListener("click", async (event) => {
  const suggestion = event.target.closest("[data-prompt]");
  if (suggestion) {
    await sendMessage(suggestion.dataset.prompt);
    return;
  }

  const addButton = event.target.closest("[data-product-id]");
  if (addButton) {
    await addToCart(addButton.dataset.productId, addButton);
    return;
  }

  const removeButton = event.target.closest("[data-item-id]");
  if (removeButton) {
    removeButton.disabled = true;
    try {
      await api(`/api/cart/${Number(removeButton.dataset.itemId)}`, { method: "DELETE" });
      await showCart();
      await refreshCartCount();
      showToast("Item removed from your cart.", "success");
    } catch (error) {
      removeButton.disabled = false;
      showToast(error.message, "error");
    }
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (!cartModal.classList.contains("hidden")) closeCart();
    closeSidebar();
  }
});

$$(".conversation-link").forEach((button) => {
  button.addEventListener("click", () => loadConversation(Number(button.dataset.id)));
});

refreshCartCount().catch((error) => {
  if (!String(error.message).includes("sign in")) showToast(error.message, "error");
});
