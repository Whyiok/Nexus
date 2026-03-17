document.addEventListener('DOMContentLoaded', function () {
    // Like forms (unified handler)
    document.querySelectorAll('.like-form').forEach(form => {
        form.addEventListener('submit', async (event) => {
            event.preventDefault();
            const postId = form.dataset.id;
            const csrfToken = form.querySelector('input[name="csrf_token"]').value;
            try {
                const response = await fetch(`/like/${postId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ discuss_id: postId })
                });
                const data = await response.json();
                const likeIcon = document.getElementById(`like-icon-${postId}`); 
                if (likeIcon) {
                    likeIcon.src = data.liked ? '/static/like_filled.svg' : '/static/like.svg';
                }

                const rating = document.getElementById(`rating-${postId}`);
                if (rating) {
                    rating.textContent = data.rating;
                }

                console.log(data);
            } catch (error) {
                console.error('Error:', error);
            }
        });
    });


    // Popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));

    // Sidebar
    const sidebar = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('toggleSidebarBtn');

    if (sidebar && toggleBtn) {
        const savedState = localStorage.getItem('sidebarCollapsed');

        if (savedState === 'false') {
            sidebar.classList.remove('collapsed');
            sidebar.style.width = '260px';
            sidebar.style.padding = '20px';
            toggleBtn.style.left = '260px';
            toggleBtn.textContent = '☰';
        } else {
            sidebar.classList.add('collapsed');
            sidebar.style.width = '0';
            sidebar.style.padding = '0';
            toggleBtn.style.left = '0';
            toggleBtn.textContent = '☰';
        }

        toggleBtn.addEventListener('click', function () {
            if (sidebar.classList.contains('collapsed')) {
                sidebar.classList.remove('collapsed');
                sidebar.style.width = '260px';
                sidebar.style.padding = '20px';
                toggleBtn.style.left = '260px';
                toggleBtn.textContent = '☰';
                localStorage.setItem('sidebarCollapsed', 'false');
            } else {
                sidebar.classList.add('collapsed');
                sidebar.style.width = '0';
                sidebar.style.padding = '0';
                toggleBtn.style.left = '0';
                toggleBtn.textContent = '☰';
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        });
    }

    // Dropdown - отмечаем уведомления как прочитанные
    const notificationDropdown = document.getElementById('notificationDropdown');

    if (notificationDropdown) {
        notificationDropdown.addEventListener('shown.bs.dropdown', async function () {
            try {
                // Получаем CSRF токен из мета-тега или cookie
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

                const response = await fetch('/mark_notice', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(csrfToken && { 'X-CSRFToken': csrfToken })
                    }
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success) {
                    console.log('Уведомления отмечены как прочитанные');

                    // Убираем бейдж с количеством уведомлений
                    const badge = notificationDropdown.querySelector('.badge');
                    if (badge) {
                        badge.remove();
                    }
                } else {
                    console.error('Ошибка:', data.message);
                }
            } catch (error) {
                console.error('Ошибка при отправке запроса:', error);
            }
        });
    } else {
        console.log('notificationDropdown не найден');
    }
});
