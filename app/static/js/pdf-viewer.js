// Функция для инициализации PDF-вьюера
function initPdfViewer(idSuffix) {
  const canvas = document.getElementById('pdfCanvas' + idSuffix);
  const prevButton = document.getElementById('prevPage' + idSuffix);
  const nextButton = document.getElementById('nextPage' + idSuffix);
  const pageNumSpan = document.getElementById('pageNum' + idSuffix);
  const pageCountSpan = document.getElementById('pageCount' + idSuffix);
  const zoomInButton = document.getElementById('zoomIn' + idSuffix);
  const zoomOutButton = document.getElementById('zoomOut' + idSuffix);
  const pdfSource = document.getElementById('pdfSource' + idSuffix);
  
  if (!canvas || !pdfSource) {
    console.error('Missing required elements for PDF viewer', idSuffix);
    return;
  }
  
  let pdfDoc = null;
  let pageNum = 1;
  let pageRendering = false;
  let pageNumPending = null;
  let scale = 1.0;
  const ctx = canvas.getContext('2d');
  
  // Получаем URL PDF-файла
  const pdfUrl = pdfSource ? pdfSource.src : null;
  if (!pdfUrl) {
    console.error('No PDF URL found', idSuffix);
    return;
  }
  
  /**
   * Отображаем страницу PDF
   */
  function renderPage(num) {
    pageRendering = true;
    
    // Получаем страницу
    pdfDoc.getPage(num).then(function(page) {
      // Устанавливаем масштаб для отображения
      const viewport = page.getViewport({ scale: scale });
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      
      // Рендерим PDF на канвасе
      const renderContext = {
        canvasContext: ctx,
        viewport: viewport
      };
      
      const renderTask = page.render(renderContext);
      
      // После завершения рендеринга
      renderTask.promise.then(function() {
        pageRendering = false;
        if (pageNumPending !== null) {
          // Если есть ожидающая страница, отображаем ее
          renderPage(pageNumPending);
          pageNumPending = null;
        }
      });
    });
    
    // Обновляем номер текущей страницы
    pageNumSpan.textContent = num;
  }
  
  /**
   * Если идет рендеринг, ставим страницу в очередь, иначе отображаем сразу
   */
  function queueRenderPage(num) {
    if (pageRendering) {
      pageNumPending = num;
    } else {
      renderPage(num);
    }
  }
  
  /**
   * Предыдущая страница
   */
  function onPrevPage() {
    if (pageNum <= 1) {
      return;
    }
    pageNum--;
    queueRenderPage(pageNum);
  }
  
  /**
   * Следующая страница
   */
  function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
      return;
    }
    pageNum++;
    queueRenderPage(pageNum);
  }
  
  /**
   * Увеличить масштаб
   */
  function onZoomIn() {
    scale += 0.2;
    queueRenderPage(pageNum);
  }
  
  /**
   * Уменьшить масштаб
   */
  function onZoomOut() {
    if (scale <= 0.4) return;
    scale -= 0.2;
    queueRenderPage(pageNum);
  }
  
  // Добавляем обработчики событий
  if (prevButton) prevButton.addEventListener('click', onPrevPage);
  if (nextButton) nextButton.addEventListener('click', onNextPage);
  if (zoomInButton) zoomInButton.addEventListener('click', onZoomIn);
  if (zoomOutButton) zoomOutButton.addEventListener('click', onZoomOut);
  
  // Загружаем PDF
  pdfjsLib.getDocument(pdfUrl).promise.then(function(pdf) {
    pdfDoc = pdf;
    pageCountSpan.textContent = pdf.numPages;
    
    // Отображаем первую страницу
    renderPage(pageNum);
  }).catch(function(error) {
    console.error('Error loading PDF:', error);
    const pdfContainer = document.getElementById('pdfContainer' + idSuffix);
    if (pdfContainer) {
      const errorMessage = document.createElement('div');
      errorMessage.className = 'alert alert-danger';
      errorMessage.innerHTML = '<i class="bi bi-exclamation-triangle-fill me-2"></i> Ошибка загрузки PDF: ' + error.message;
      pdfContainer.innerHTML = '';
      pdfContainer.appendChild(errorMessage);
    }
  });
}

// Функция для сворачивания/разворачивания контента
function toggleCollapse(targetSelector, button) {
  const target = document.querySelector(targetSelector);
  if (!target) return;
  
  // Переключаем класс show
  if (target.classList.contains('show')) {
    target.classList.remove('show');
    // Меняем иконку на кнопке
    const icon = button.querySelector('i');
    if (icon) {
      icon.classList.remove('bi-arrows-collapse');
      icon.classList.add('bi-arrows-expand');
    }
  } else {
    target.classList.add('show');
    // Меняем иконку на кнопке
    const icon = button.querySelector('i');
    if (icon) {
      icon.classList.remove('bi-arrows-expand');
      icon.classList.add('bi-arrows-collapse');
    }
  }
}

// Функция для открытия PDF в новом окне без возможности скачивания
function openPdfInNewWindow(pdfUrl) {
  // Открываем новое окно с PDF-файлом
  const newWindow = window.open(pdfUrl, '_blank', 'width=800,height=600,toolbar=0,location=0,menubar=0');
  
  // Если новое окно не открылось (возможно, из-за блокировщика всплывающих окон)
  if (!newWindow || newWindow.closed || typeof newWindow.closed === 'undefined') {
    alert('Пожалуйста, разрешите всплывающие окна для этого сайта или перейдите по ссылке: ' + pdfUrl);
    // Если не удалось открыть новое окно, открываем в той же вкладке
    window.location.href = pdfUrl;
  }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
  // Инициализируем PDF.js
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdn.jsdelivr.net/npm/pdfjs-dist@3.4.120/build/pdf.worker.min.js';
  
  // Добавляем обработчик событий для кнопок с классом pdf-open-btn
  document.querySelectorAll('.pdf-open-btn').forEach(function(button) {
    button.addEventListener('click', function() {
      const pdfUrl = this.getAttribute('data-pdf-url');
      if (pdfUrl) {
        openPdfInNewWindow(pdfUrl);
      }
    });
  });
  
  // Получаем все элементы collapse
  const collapseElements = document.querySelectorAll('.collapse');
  
  // Инициализируем каждый элемент с помощью Bootstrap
  collapseElements.forEach(collapseElement => {
    new bootstrap.Collapse(collapseElement, {
      toggle: false // Не переключать при инициализации
    });
  });
  
  // Инициализируем все PDF-вьюеры на странице
  // Находим все PDF-контейнеры на странице
  const pdfContainers = document.querySelectorAll('[id^="pdfContainer"]');
  
  pdfContainers.forEach(container => {
    const materialId = container.id.replace('pdfContainer', '');
    // Используем общую функцию для инициализации PDF-вьюера
    initPdfViewer(materialId);
  });
  
  // Инициализируем PDF-вьюеры в разделе Тесты (Savollar)
  const pdfViewersTest = document.querySelectorAll('[id^="pdfViewerTest"]');
  
  pdfViewersTest.forEach(container => {
    const materialId = 'Test' + container.id.replace('pdfViewerTest', '');
    // Используем общую функцию для инициализации PDF-вьюера
    initPdfViewer(materialId);
  });
  
  // Обработка кнопок сворачивания/разворачивания
  document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(function(button) {
    // Проверяем, что кнопка существует и имеет атрибут data-bs-target
    if (!button || !button.getAttribute('data-bs-target')) return;
    
    // Получаем целевой элемент
    const targetId = button.getAttribute('data-bs-target');
    const target = document.querySelector(targetId);
    
    if (!target) return;
    
    // Слушаем события show.bs.collapse и hide.bs.collapse
    target.addEventListener('show.bs.collapse', function() {
      button.setAttribute('aria-expanded', 'true');
      const icon = button.querySelector('i');
      if (icon) {
        icon.classList.remove('bi-arrows-expand');
        icon.classList.add('bi-arrows-collapse');
      }
    });
    
    target.addEventListener('hide.bs.collapse', function() {
      button.setAttribute('aria-expanded', 'false');
      const icon = button.querySelector('i');
      if (icon) {
        icon.classList.remove('bi-arrows-collapse');
        icon.classList.add('bi-arrows-expand');
      }
    });
    
    // Добавляем обработчик события клика для подстраховки
    button.addEventListener('click', function(e) {
      // Не предотвращаем стандартное поведение, чтобы Bootstrap мог обработать клик
    });
  });

  // Сворачивание/разворачивание длинных лекций
  const maxChars = 500; // Макс. символов до сворачивания
  const expandableContents = document.querySelectorAll('.content-expandable');

  expandableContents.forEach(content => {
    const fullText = content.innerHTML;
    if (content.textContent.length > maxChars) {
      const shortText = content.textContent.substring(0, maxChars) + '...';
      content.innerHTML = shortText; // Показываем урезанный текст

      const toggleLink = document.createElement('a');
      toggleLink.href = '#';
      toggleLink.textContent = ' Показать полностью';
      toggleLink.className = 'text-primary small ms-1';
      toggleLink.style.cursor = 'pointer';

      toggleLink.addEventListener('click', function(e) {
        e.preventDefault();
        if (content.innerHTML === shortText) {
          content.innerHTML = fullText; // Показываем полный текст
          toggleLink.textContent = ' Свернуть';
        } else {
          content.innerHTML = shortText; // Сворачиваем
          toggleLink.textContent = ' Показать полностью';
        }
        content.appendChild(toggleLink); // Передобавляем ссылку
      });
      content.appendChild(toggleLink); // Добавляем ссылку в конец
    }
  });
});
