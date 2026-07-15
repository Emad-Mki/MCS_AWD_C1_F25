document.addEventListener("DOMContentLoaded", function () {
    const subscribeButtons = document.querySelectorAll(".subscribe-btn");
    const messageBox = document.getElementById("subscription-message");

    function showMessage(message, type = "success") {
        if (!messageBox) return;
        messageBox.textContent = message;
        messageBox.className = `subscription-message ${type}`;
        messageBox.style.display = "block";
        setTimeout(() => {
            messageBox.style.display = "none";
        }, 3000);
    }

    subscribeButtons.forEach((button) => {
        button.addEventListener("click", async function () {
            const offeringId = this.dataset.offeringId;
            if (!offeringId) {
                showMessage("Invalid offering ID.", "error");
                return;
            }

            this.disabled = true;
            const originalText = this.textContent;
            this.textContent = "Subscribing...";

            const formData = new FormData();
            formData.append("offering_id", offeringId);

            try {
                const response = await fetch("/ajax/subscribe", {
                    method: "POST",
                    body: formData,
                });

                const data = await response.json();

                if (response.ok && data.status === "success") {
                    this.textContent = "Already Subscribed";
                    this.classList.remove("btn-primary");
                    this.classList.add("btn-disabled");
                    showMessage(data.message, "success");
                } else {
                    this.disabled = false;
                    this.textContent = originalText;
                    showMessage(data.message || "Subscription failed.", "error");
                }
            } catch (error) {
                this.disabled = false;
                this.textContent = originalText;
                showMessage("Something went wrong. Please try again.", "error");
            }
        });
    });
});
