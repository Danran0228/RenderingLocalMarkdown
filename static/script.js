function toggleFolder(element) {
    const folderContent = element.nextElementSibling;
    const folderIcon = element.querySelector('.folder-icon');
    
    if (folderContent.style.display === 'none' || !folderContent.style.display) {
        folderContent.style.display = 'block';
        folderIcon.classList.remove('fa-chevron-right');
        folderIcon.classList.add('fa-chevron-down');
    } else {
        folderContent.style.display = 'none';
        folderIcon.classList.remove('fa-chevron-down');
        folderIcon.classList.add('fa-chevron-right');
    }
}

function loadContent(filePath) {
    // 将路径按 / 分割，分别编码每个部分，然后重新组合
    const encodedPath = filePath.split('/')
        .map(part => encodeURIComponent(part))
        .join('/');

    fetch(`/api/content/${encodedPath}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                document.getElementById('content').innerHTML = `<div class="error">${data.error}</div>`;
                return;
            }
            document.getElementById('content').innerHTML = data.content;
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('content').innerHTML = '<div class="error">加载失败</div>';
        });
}

function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    
    // 显示通知
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // 3秒后隐藏通知
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

function toggleSaveArticle(event) {
    if (event) {
        event.stopPropagation(); // 阻止事件冒泡
    }
    const saveArticle = document.querySelector('.save-article');
    saveArticle.classList.toggle('open');
}

function saveArticle(event) {
    event.stopPropagation(); // 阻止事件冒泡
    const articleUrlInput = document.getElementById('article-url');
    const articleUrl = articleUrlInput.value;
    if (!articleUrl) {
        showNotification('请输入文章URL', 'error');
        return;
    }
    fetch('/save-article', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: articleUrl })
    })
    .then(response => response.json())
    .then(data => {
        showNotification(data.message, data.status || 'success');
        if (data.status !== 'error') {
            articleUrlInput.value = ''; // 清空输入框
            toggleSaveArticle(); // 关闭控件
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('保存文章失败', 'error');
    });
}

function setupMobileNavigation() {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    document.body.appendChild(overlay);

    // 创建菜单按钮
    const menuToggle = document.createElement('button');
    menuToggle.className = 'menu-toggle';
    menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
    document.body.appendChild(menuToggle);

    const sidebar = document.querySelector('.sidebar');
    const contentArea = document.querySelector('.content-area');

    function toggleSidebar() {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
        contentArea.classList.toggle('shifted');
        
        // 更新菜单图标
        const icon = menuToggle.querySelector('i');
        if (sidebar.classList.contains('active')) {
            icon.className = 'fas fa-times';
        } else {
            icon.className = 'fas fa-bars';
        }
    }

    // 点击菜单按钮
    menuToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleSidebar();
    });

    // 点击遮罩层关闭侧边栏
    overlay.addEventListener('click', toggleSidebar);

    // 处理触摸滑动
    let touchStartX = 0;
    let touchEndX = 0;
    let isSwiping = false;

    document.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
        isSwiping = true;
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
        if (!isSwiping) return;
        
        const currentX = e.touches[0].clientX;
        const diff = currentX - touchStartX;
        
        // 从左边缘开始滑动才打开侧边栏
        if (touchStartX < 30 && diff > 0 && !sidebar.classList.contains('active')) {
            e.preventDefault();
            sidebar.style.transform = `translateX(${diff}px)`;
            overlay.style.display = 'block';
            overlay.style.opacity = diff / 300;
        }
        
        // 已打开状态下向左滑动关闭
        if (sidebar.classList.contains('active') && diff < 0) {
            e.preventDefault();
            sidebar.style.transform = `translateX(${100 + diff}%)`;
            overlay.style.opacity = 1 + diff / 300;
        }
    }, { passive: false });

    document.addEventListener('touchend', (e) => {
        if (!isSwiping) return;
        
        touchEndX = e.changedTouches[0].clientX;
        const diff = touchEndX - touchStartX;
        
        // 重置样式
        sidebar.style.transform = '';
        overlay.style.opacity = '';
        
        // 判断滑动距离是否足够触发动作
        if (Math.abs(diff) > 50) {
            if (diff > 0 && touchStartX < 30) {
                sidebar.classList.add('active');
                overlay.classList.add('active');
                contentArea.classList.add('shifted');
                menuToggle.querySelector('i').className = 'fas fa-times';
            } else if (diff < 0 && sidebar.classList.contains('active')) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                contentArea.classList.remove('shifted');
                menuToggle.querySelector('i').className = 'fas fa-bars';
            }
        }
        
        isSwiping = false;
    }, { passive: true });

    // 处理屏幕旋转
    window.addEventListener('orientationchange', () => {
        setTimeout(() => {
            if (window.innerWidth > 768) {
                sidebar.classList.remove('active');
                overlay.classList.remove('active');
                contentArea.classList.remove('shifted');
                menuToggle.style.display = 'none';
                overlay.style.display = 'none';
            } else {
                menuToggle.style.display = 'flex';
            }
        }, 200);
    });

    // 初始化显示状态
    if (window.innerWidth <= 768) {
        menuToggle.style.display = 'flex';
    } else {
        menuToggle.style.display = 'none';
    }
}

// 在页面加载时初始化
document.addEventListener('DOMContentLoaded', () => {
    setupMobileNavigation();

    // 添加点击输入框和按钮的阻止冒泡
    document.querySelector('.save-article').addEventListener('click', (event) => {
        event.stopPropagation();
    });

    // 添加点击空白处关闭控件
    document.addEventListener('click', () => {
        const saveArticleDiv = document.querySelector('.save-article');
        if (saveArticleDiv.classList.contains('open')) {
            toggleSaveArticle();
        }
    });

    // 添加快捷键支持
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            const saveArticleDiv = document.querySelector('.save-article');
            if (saveArticleDiv.classList.contains('open')) {
                toggleSaveArticle();
            }
        }
    });

    // 创建触发按钮
    const toggleButton = document.createElement('button');
    toggleButton.innerHTML = '<i class="fas fa-save"></i>';
    toggleButton.style.position = 'fixed';
    toggleButton.style.top = '20px';
    toggleButton.style.right = '20px';
    toggleButton.style.padding = '8px 12px';
    toggleButton.style.backgroundColor = '#4CAF50';
    toggleButton.style.color = 'white';
    toggleButton.style.border = 'none';
    toggleButton.style.borderRadius = '4px';
    toggleButton.style.cursor = 'pointer';
    toggleButton.style.zIndex = '99';
    toggleButton.title = '保存文章';

    toggleButton.addEventListener('click', (event) => {
        event.stopPropagation();
        toggleSaveArticle();
    });

    document.body.appendChild(toggleButton);
}); 