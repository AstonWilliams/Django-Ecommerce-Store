// Cart functionality
function addToCart(productId) {
  fetch(`/add-to-cart/${productId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showMessage("Product added to cart!", "success")
        updateCartCount()
      } else {
        showMessage("Please sign in to add items to cart", "error")
      }
    })
    .catch((error) => {
      console.error("Error:", error)
      showMessage("Error adding product to cart", "error")
    })
}

// Get CSRF token
function getCookie(name) {
  let cookieValue = null
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue
}

// Show message
function showMessage(message, type) {
  const messageDiv = document.createElement("div")
  messageDiv.className = `message message-${type}`
  messageDiv.textContent = message

  const main = document.querySelector(".main")
  main.insertBefore(messageDiv, main.firstChild)

  setTimeout(() => {
    messageDiv.remove()
  }, 3000)
}

// Update cart count
function updateCartCount() {
  // This would typically fetch the current cart count from the server
  const cartCount = document.querySelector(".cart-count")
  if (cartCount) {
    const count = Number.parseInt(cartCount.textContent) || 0
    cartCount.textContent = count + 1
  }
}

// Product detail page functions
function changeImage(src) {
  const mainImage = document.getElementById("mainImage")
  if (mainImage) {
    mainImage.src = src
  }

  // Update active thumbnail
  document.querySelectorAll(".thumbnail").forEach((thumb) => {
    thumb.classList.remove("active")
  })
  event.target.classList.add("active")
}

function increaseQuantity() {
  const quantityInput = document.getElementById("quantity")
  if (quantityInput) {
    quantityInput.value = Number.parseInt(quantityInput.value) + 1
  }
}

function decreaseQuantity() {
  const quantityInput = document.getElementById("quantity")
  if (quantityInput && Number.parseInt(quantityInput.value) > 1) {
    quantityInput.value = Number.parseInt(quantityInput.value) - 1
  }
}

// Cart page functions
function increaseCartQuantity(button) {
  const input = button.parentElement.querySelector('input[name="quantity"]')
  input.value = Number.parseInt(input.value) + 1
  input.form.submit()
}

function decreaseCartQuantity(button) {
  const input = button.parentElement.querySelector('input[name="quantity"]')
  if (Number.parseInt(input.value) > 1) {
    input.value = Number.parseInt(input.value) - 1
    input.form.submit()
  }
}

// Search functionality
document.addEventListener("DOMContentLoaded", () => {
  const searchInput = document.querySelector(".search-input")
  const searchBtn = document.querySelector(".search-btn")

  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      const query = searchInput.value.trim()
      if (query) {
        // Implement search functionality
        console.log("Searching for:", query)
      }
    })
  }

  if (searchInput) {
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        const query = searchInput.value.trim()
        if (query) {
          // Implement search functionality
          console.log("Searching for:", query)
        }
      }
    })
  }
})

// Form validation
function validateForm(form) {
  const inputs = form.querySelectorAll("input[required]")
  let isValid = true

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      input.style.borderColor = "#dc3545"
      isValid = false
    } else {
      input.style.borderColor = "#e1e5e9"
    }
  })

  return isValid
}

// Password confirmation validation
document.addEventListener("DOMContentLoaded", () => {
  const confirmPasswordInput = document.getElementById("confirm_password")
  const passwordInput = document.getElementById("password")

  if (confirmPasswordInput && passwordInput) {
    confirmPasswordInput.addEventListener("input", function () {
      if (this.value !== passwordInput.value) {
        this.style.borderColor = "#dc3545"
      } else {
        this.style.borderColor = "#28a745"
      }
    })
  }
})
