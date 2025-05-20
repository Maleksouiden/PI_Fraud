// Main JavaScript file for JobMatch

// Fonction pour ouvrir les liens externes en toute sécurité
function openExternalLink(url) {
  // Ouvrir l'URL dans un nouvel onglet avec des paramètres de sécurité
  window.open(url, "_blank", "noopener,noreferrer");
  return true;
}

document.addEventListener("DOMContentLoaded", function () {
  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Initialize popovers
  var popoverTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="popover"]')
  );
  var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });

  // Auto-dismiss alerts
  setTimeout(function () {
    var alerts = document.querySelectorAll(".alert:not(.alert-permanent)");
    alerts.forEach(function (alert) {
      var bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 5000);

  // Initialize modals
  var modals = document.querySelectorAll(".modal");
  modals.forEach(function (modalEl) {
    var modal = new bootstrap.Modal(modalEl);

    // Add event listener to show modal when button is clicked
    var modalTrigger = document.querySelector(
      `[data-bs-target="#${modalEl.id}"]`
    );
    if (modalTrigger) {
      modalTrigger.addEventListener("click", function () {
        modal.show();
      });
    }
  });

  // Skills input enhancement
  var skillsInput = document.getElementById("skills");
  if (skillsInput) {
    // Simple tag input functionality
    skillsInput.addEventListener("keydown", function (e) {
      if (e.key === ",") {
        e.preventDefault();
        var value = this.value.trim();
        if (value) {
          this.value = value + ", ";
        }
      }
    });
  }

  // Match score animation
  var matchCircles = document.querySelectorAll("circle[stroke-dashoffset]");
  if (matchCircles.length > 0) {
    matchCircles.forEach(function (circle) {
      // Add animation class
      circle.classList.add("circle-animation");
    });
  }

  // Job card hover effects
  var jobCards = document.querySelectorAll(".card");
  jobCards.forEach(function (card) {
    card.classList.add("job-card");
  });

  // Form validation
  var forms = document.querySelectorAll(".needs-validation");
  Array.prototype.slice.call(forms).forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });

  // Salary range input with display
  var salaryRange = document.getElementById("salary_range");
  var salaryDisplay = document.getElementById("salary_display");
  if (salaryRange && salaryDisplay) {
    salaryRange.addEventListener("input", function () {
      salaryDisplay.textContent = this.value + " €";
    });
  }

  // Back to top button
  var backToTopBtn = document.getElementById("back-to-top");
  if (backToTopBtn) {
    window.addEventListener("scroll", function () {
      if (window.pageYOffset > 300) {
        backToTopBtn.style.display = "block";
      } else {
        backToTopBtn.style.display = "none";
      }
    });

    backToTopBtn.addEventListener("click", function (e) {
      e.preventDefault();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }
});
