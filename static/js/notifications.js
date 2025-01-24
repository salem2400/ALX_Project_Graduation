function showNotification(message, type = 'default') {
    // Remove any existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // Add notification to page
    document.body.appendChild(notification);

    // Remove notification after delay
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Example usage:
// showNotification('Data saved successfully', 'success');
// showNotification('An error occurred', 'error');
// showNotification('Important alert', 'warning'); 