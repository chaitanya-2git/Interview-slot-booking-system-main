console.log("script.js loaded — Premium UI v2.0");

document.addEventListener("DOMContentLoaded", function () {

    /* ---------------- MOBILE SIDEBAR TOGGLE ---------------- */
    var sidebarToggle = document.getElementById('sidebarToggle');
    var sidebarEl = document.getElementById('sidebar');
    var sidebarOverlay = document.getElementById('sidebarOverlay');

    if (sidebarToggle && sidebarEl) {
        sidebarToggle.addEventListener('click', function() {
            sidebarEl.classList.toggle('mobile-open');
            if (sidebarOverlay) sidebarOverlay.classList.toggle('visible');
        });
    }
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function() {
            if (sidebarEl) sidebarEl.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('visible');
        });
    }

    // Scroll to top on page load, unless a specific section is targeted
    if (!window.location.hash) {
        window.scrollTo(0, 0);
    }

    // Scroll to top on all link clicks (for page navigation)
    document.querySelectorAll('a[href]').forEach(link => {
        link.addEventListener('click', function(e) {
            // Only apply to actual page navigation, not anchor links or JavaScript links
            if (this.getAttribute('href').startsWith('/') ||
                this.getAttribute('href').startsWith('http') ||
                this.getAttribute('href').startsWith('#') === false) {
                // Let the navigation happen, browser will scroll to top automatically
            }
        });
    });

    /* ---------------- SIDEBAR NAVIGATION ---------------- */

    const sidebarLinks = document.querySelectorAll(".sidebar-link[data-section]");
    const sidebar = document.querySelector(".sidebar");
    const mainContent = document.querySelector(".main-content");
    const backToDashboardBtn = document.getElementById("backToDashboardBtn");
    const backToDashboardBtnTodays = document.getElementById("backToDashboardBtnTodays");

    sidebarLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();

            const targetSection = this.dataset.section;

            // Remove active class from all links
            sidebarLinks.forEach(l => l.classList.remove("active"));

            // Add active class to clicked link
            this.classList.add("active");

            // Hide all content sections
            document.querySelectorAll(".content-section").forEach(section => {
                section.classList.remove("active");
            });

            // Show target section
            const targetSectionElement = document.getElementById(`section-${targetSection}`);
            if (targetSectionElement) {
                targetSectionElement.classList.add("active");
                // Scroll to top of section
                window.scrollTo(0, 0);
            }

            // Close mobile sidebar after nav click
            if (sidebarEl) sidebarEl.classList.remove('mobile-open');
            if (sidebarOverlay) sidebarOverlay.classList.remove('visible');
            
            // Update URL hash without jumping
            if (history.pushState) {
                history.pushState(null, null, '#' + targetSection);
            } else {
                window.location.hash = targetSection;
            }
        });
    });

    // Check URL hash on page load for HR Dashboard
    if (window.location.hash) {
        const hashSection = window.location.hash.substring(1);
        const hashLink = document.querySelector(`.sidebar-link[data-section="${hashSection}"]`);
        if (hashLink) {
            hashLink.click();
        }
    }

    /* ---------------- BACK TO DASHBOARD BUTTON (Bookings Section) ---------------- */

    if (backToDashboardBtn) {
        backToDashboardBtn.addEventListener("click", function() {
            // Navigate to HR Dashboard route
            window.location.href = "/hr-dashboard";
        });
    }

    /* ---------------- BACK TO DASHBOARD BUTTON (Today's Interviews Section) ---------------- */

    if (backToDashboardBtnTodays) {
        backToDashboardBtnTodays.addEventListener("click", function() {
            // Navigate to HR Dashboard route
            window.location.href = "/hr-dashboard";
        });
    }

    /* ---------------- CANDIDATE NAVIGATION ---------------- */

    const candidateNavLinks = document.querySelectorAll(".candidate-nav-link[data-section]");

    candidateNavLinks.forEach(link => {
        link.addEventListener("click", function(e) {
            e.preventDefault();

            const targetSection = this.dataset.section;

            // Remove active class from all candidate nav links
            candidateNavLinks.forEach(l => l.classList.remove("active"));

            // Add active class to clicked link
            this.classList.add("active");

            // Hide all content sections
            document.querySelectorAll(".content-section").forEach(section => {
                section.classList.remove("active");
            });

            // Show target section
            const targetSectionElement = document.getElementById(`section-${targetSection}`);
            if (targetSectionElement) {
                targetSectionElement.classList.add("active");
                // Scroll to top of section
                window.scrollTo(0, 0);
            }
            
            // Update URL hash without jumping
            if (history.pushState) {
                history.pushState(null, null, '#' + targetSection);
            } else {
                window.location.hash = targetSection;
            }
        });
    });

    // Check URL hash on page load for Candidate Dashboard
    if (window.location.hash) {
        const hashSection = window.location.hash.substring(1);
        const hashLink = document.querySelector(`.candidate-nav-link[data-section="${hashSection}"]`);
        if (hashLink) {
            hashLink.click();
        }
    }

    const bookingModal = document.getElementById("bookingModal");
    const bookingForm = document.getElementById("bookingForm");
    const slotDetails = document.getElementById("slotDetails");

    const rescheduleModal = document.getElementById("rescheduleModal");
    const rescheduleModalContent = document.getElementById("rescheduleModalContent");

    const dateSelector = document.getElementById("interviewDateSelector");


    /* ---------------- BOOK SLOT MODAL ---------------- */

    if (bookingModal) {

        bookingModal.addEventListener("show.bs.modal", function (event) {

            const button = event.relatedTarget;

            slotDetails.innerHTML =
                `${button.dataset.slotDate}<br>
                 ${button.dataset.slotStart} - ${button.dataset.slotEnd}`;

            bookingForm.action = `/book-slot`;
            
            // Add or update hidden inputs for interview_date and start_time
            let dateInput = bookingForm.querySelector('input[name="interview_date"]');
            if (!dateInput) {
                dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'interview_date';
                bookingForm.appendChild(dateInput);
            }
            dateInput.value = button.dataset.slotDate;
            
            let timeInput = bookingForm.querySelector('input[name="start_time"]');
            if (!timeInput) {
                timeInput = document.createElement('input');
                timeInput.type = 'hidden';
                timeInput.name = 'start_time';
                bookingForm.appendChild(timeInput);
            }
            timeInput.value = button.dataset.slotStart;

        });

        bookingModal.addEventListener("hidden.bs.modal", function () {
            bookingForm.reset();
        });

    }

    // Slot rows are re-rendered after a date selection. Expose the action for
    // generated buttons and explicitly open the existing Bootstrap modal.
    window.openBookingModal = function (button) {
        if (window.bootstrap && bookingModal) {
            window.bootstrap.Modal.getOrCreateInstance(bookingModal).show(button);
        }
    };

    document.addEventListener("click", function (event) {
        const button = event.target.closest(".book-slot-btn");
        if (button) {
            window.openBookingModal(button);
        }
    });


    /* ---------------- RESCHEDULE MODAL ---------------- */

    if (rescheduleModal) {

        rescheduleModal.addEventListener("show.bs.modal", function (event) {

            const bookingId = event.relatedTarget.dataset.bookingId;

            rescheduleModalContent.innerHTML =
                '<div class="text-center p-4"><div class="spinner-border text-primary"></div></div>';

            fetch(`/reschedule/${bookingId}`, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })

            .then(response => response.text())

            .then(html => {

                rescheduleModalContent.innerHTML = html;

                initializeRescheduleForm(bookingId);

            })

            .catch(err => {

                rescheduleModalContent.innerHTML =
                    `<div class="alert alert-danger">${err}</div>`;

            });

        });

    }


    function initializeRescheduleForm(bookingId) {

        const form = document.querySelector("#rescheduleModalContent form");

        const dateInput = document.getElementById("rescheduleDate");

        const slotSelect = document.getElementById("new_slot_id");


        /* ---------- Calendar Change ---------- */

        if (dateInput) {

            dateInput.addEventListener("change", function () {

                fetch("/get-slots-by-date", {

                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        interview_date: this.value
                    })

                })

                .then(res => res.json())

                .then(data => {

                    if (!data.success) return;

                    slotSelect.innerHTML = "";

                    const blocks = data.time_blocks;

                    blocks.forEach(block => {

                        const option = document.createElement("option");

                        option.value = block.start_time;
                        
                        if (block.available > 0) {
                            option.text = `${block.start_time} - ${block.end_time} (${block.available} available)`;
                        } else {
                            option.text = `${block.start_time} - ${block.end_time} (Fully Booked)`;
                            option.disabled = true;
                        }

                        slotSelect.appendChild(option);

                    });

                });

            });

        }


        /* ---------- Submit ---------- */

        if (form) {

            form.addEventListener("submit", function (e) {

                e.preventDefault();

                fetch(`/reschedule/${bookingId}`, {

                    method: "POST",

                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },

                    body: new FormData(form)

                })

                .then(res => res.json())

                .then(data => {

                    if (data.success) {

                        const modalInstance = bootstrap.Modal.getInstance(rescheduleModal);
                        if (modalInstance) {
                            modalInstance.hide();
                        }

                        location.reload();

                    } else {

                        var errContainer = document.createElement('div');
                        errContainer.className = 'alert alert-danger';
                        errContainer.style.marginTop = '12px';
                        errContainer.textContent = data.error || 'Failed to reschedule.';
                        var modalBody = document.querySelector('#rescheduleModalContent');
                        if (modalBody) modalBody.appendChild(errContainer);
                        setTimeout(function() { if (errContainer.parentElement) errContainer.remove(); }, 4000);

                    }

                });

            });

        }

    }


    /* ---------------- Candidate Calendar ---------------- */

    if (dateSelector) {
        const isCandidateDashboard = window.location.pathname === '/candidate-dashboard';
        const storageKey = isCandidateDashboard ? 'candidateSelectedDate' : 'hrSelectedDate';
        const statusMessage = document.getElementById('slotLoadStatus');
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        dateSelector.min = today.toISOString().split('T')[0];

        const savedDate = sessionStorage.getItem(storageKey);
        if (savedDate && savedDate >= dateSelector.min) {
            dateSelector.value = savedDate;
            setTimeout(function() { dateSelector.dispatchEvent(new Event('change')); }, 100);
        }

        document.querySelectorAll('.date-shortcut[data-date-offset]').forEach(function(button) {
            button.addEventListener('click', function() {
                const selected = new Date(today);
                selected.setDate(selected.getDate() + Number(this.dataset.dateOffset));
                dateSelector.value = selected.toISOString().split('T')[0];
                dateSelector.dispatchEvent(new Event('change'));
            });
        });

        dateSelector.addEventListener("change", function () {
            if (!this.value) return;
            if (this.value < dateSelector.min) this.value = dateSelector.min;
            sessionStorage.setItem(storageKey, this.value);
            if (statusMessage) statusMessage.textContent = 'Loading available interview slots.';

            const tbody = document.querySelector("#availableSlotsTable tbody");
            if (tbody) {
                tbody.innerHTML = "<tr><td colspan='5'><div class='table-loading'><span class='spinner-border spinner-border-sm' aria-hidden='true'></span> Loading available slots…</div></td></tr>";
            }

            const endpoint = isCandidateDashboard
                ? "/available-slots-by-date?interview_date=" + encodeURIComponent(this.value)
                : "/get-slots-by-date";
            const options = isCandidateDashboard
                ? { headers: { "X-Requested-With": "XMLHttpRequest" } }
                : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ interview_date: this.value }) };

            fetch(endpoint, options)
                .then(res => res.json())
                .then(data => {
                    if (!data.success) throw new Error(data.error || 'Unable to load slots.');
                    updateSlotsTable(data.time_blocks);
                    if (statusMessage) statusMessage.textContent = data.time_blocks.length + ' time options loaded.';
                })
                .catch(() => {
                    if (tbody) {
                        tbody.innerHTML = "<tr><td colspan='5'><div class='empty-state'><div class='empty-state-icon'><i class='bi bi-exclamation-circle'></i></div><div class='empty-state-title'>Unable to load slots</div><div class='empty-state-sub'>Please choose another date or try again.</div></div></td></tr>";
                    }
                    if (statusMessage) statusMessage.textContent = 'Unable to load slots.';
                });
        });
    }


    function updateSlotsTable(timeBlocks) {

        const tbody = document.querySelector("#availableSlotsTable tbody");

        if (!tbody) return;

        if (timeBlocks.length === 0) {

            tbody.innerHTML = "<tr><td colspan='5'><div class='empty-state'><div class='empty-state-icon'><i class='bi bi-calendar-x'></i></div><div class='empty-state-title'>No slots available</div><div class='empty-state-sub'>No slots available for this date.</div></div></td></tr>";

            return;

        }

        let html = "";

        timeBlocks.forEach(block => {
            let availabilityBadge = block.available > 0 
                ? `<span class="badge bg-success">${block.available} slot(s) available</span>`
                : `<span class="badge bg-danger">🔴 Fully Booked</span>`;
            
            let actionButton = block.available > 0
                ? `<button
                        class="btn btn-primary btn-sm book-slot-btn"
                        data-slot-date="${block.interview_date}"
                        data-slot-start="${block.start_time}"
                        data-slot-end="${block.end_time}"
                        onclick="openBookingModal(this)">
                        Book
                    </button>`
                : `<button class="btn btn-secondary btn-sm" disabled>Book</button>`;

            html += `
            <tr>
                <td data-label="Availability">${availabilityBadge}</td>
                <td data-label="Date">${block.interview_date}</td>
                <td data-label="Start time">${block.start_time}</td>
                <td data-label="End time">${block.end_time}</td>
                <td data-label="Action">${actionButton}</td>
            </tr>`;

        });

        tbody.innerHTML = html;

    }

});
