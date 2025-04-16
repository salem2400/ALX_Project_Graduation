function showNotification(message, type = 'default') {
    // إزالة أي إشعارات موجودة
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // إنشاء عنصر الإشعار
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    // إضافة الإشعار إلى الصفحة
    document.body.appendChild(notification);

    // إزالة الإشعار بعد انتهاء التحريك
    setTimeout(() => {
        notification.remove();
    }, 1500);
}

// مثال على الاستخدام:
// showNotification('تم حفظ البيانات بنجاح', 'success');
// showNotification('حدث خطأ ما', 'error');
// showNotification('تنبيه مهم', 'warning'); 