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
    fetch(`/api/content/${filePath}`)
        .then(response => response.json())
        .then(data => {
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

// 在页面加载时绑定事件
document.addEventListener('DOMContentLoaded', () => {
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