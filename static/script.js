function sendMessage() {
    var userInput = document.getElementById("user-input").value;
    if (userInput.trim() === "") return; // Prevent sending empty messages

    var chatBox = document.getElementById("chat-box");
    var userMessageDiv = document.createElement("div");
    userMessageDiv.classList.add("message", "user-message");
    userMessageDiv.textContent = userInput;
    chatBox.appendChild(userMessageDiv);

    document.getElementById("user-input").value = ""; // Clear input

    // AJAX request to send message to Flask backend
    $.ajax({
        type: "POST",
        url: "/get_response",
        data: { message: userInput },
        success: function(data) {
            var botResponse = data.response;
            var botMessageDiv = document.createElement("div");
            botMessageDiv.classList.add("message", "bot-message");
            botMessageDiv.innerHTML = botResponse; // Use innerHTML to render any HTML returned by Gemini
            chatBox.appendChild(botMessageDiv);

            chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
        },
        error: function(xhr, status, error) {
            console.error("Error:", error);
            var botMessageDiv = document.createElement("div");
            botMessageDiv.classList.add("message", "bot-message");
            botMessageDiv.textContent = "I'm sorry, there was an error.";
            chatBox.appendChild(botMessageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    });
}

// Allow sending messages with the Enter key
document.getElementById("user-input").addEventListener("keyup", function(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
});