// 後端 API 的網址。如果你的 FastAPI 後端在本地執行，通常是這個網址
const API_URL = 'http://127.0.0.1:8000/api/v1/movie-insight';

// 抓取 HTML 上的積木元素
const searchBtn = document.getElementById('search-btn');
const movieInput = document.getElementById('movie-input');
const loadingDiv = document.getElementById('loading');
const errorBox = document.getElementById('error-box');
const errorMessage = document.getElementById('error-message');
const resultBox = document.getElementById('result-box');

// 結果區內部的元素
const movieTitle = document.getElementById('movie-title');
const movieRating = document.getElementById('movie-rating');
const overallSentiment = document.getElementById('overall-sentiment');
const summaryText = document.getElementById('summary-text');
const audioContainer = document.getElementById('audio-container');
const audioPlayer = document.getElementById('audio-player');
const aspectsList = document.getElementById('aspects-list');

// 點擊「開始分析」按鈕時觸發的動作
searchBtn.addEventListener('click', async () => {
    const textValue = movieInput.value.trim();

    // 檢查防呆：如果沒打字就按送出
    if (!textValue) {
        showError("請輸入你想查詢的電影內容！");
        return;
    }

    // 1. 進入等待狀態：顯示轉圈圈，藏起之前的結果或錯誤訊息
    loadingDiv.classList.remove('hidden');
    resultBox.classList.add('hidden');
    errorBox.classList.add('hidden');

    try {
        // 2. 呼叫服務生送單：把 message 用 JSON 格式打包發送給後端
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: textValue })
        });

        // 如果連線失敗 (例如網址錯了或後端沒開)
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "後端伺服器回應錯誤。");
        }

        // 3. 廚房做完菜了，解析後端傳回來的資料
        const data = await response.json();

        // 4. 擺盤邏輯：檢查狀態
        if (data.status === 'ok') {
            // 如果成功，呼叫下方寫好的擺盤功能
            renderSuccessResult(data);
        } else {
            // 如果是不成功的狀況 (例如 movie_not_found、no_movie_in_message)
            // 直接顯示後端貼心準備的繁體中文說明字串 (message_zh)
            showError(data.message_zh || `無法處理，狀態代碼：${data.status}`);
        }

    } catch (error) {
        console.error(error);
        showError("無法連線到後端，請確認後端程式是否有啟動、或是否遇到了跨網域(CORS)問題。");
    } finally {
        // 無論結果是成功或失敗，最後都要把轉圈圈藏起來
        loadingDiv.classList.add('hidden');
    }
});

// 顯示提示訊息的公用功能
function showError(msg) {
    errorMessage.textContent = msg;
    errorBox.classList.remove('hidden');
}

// 成功拿到資料時的擺盤方法 (完全對齊後端資料格式版)
function renderSuccessResult(data) {
    // 1. 填入電影名稱
    movieTitle.textContent = data.matched_movie;//////
    
    // 2. 評分欄位 (因為後端 bundle.py 沒有傳送這個資料，我們先寫死，以免報錯)
    movieRating.textContent = data.rating;////////

    // 3. 處理整體情感 (✨ 關鍵：多加一層 data.analysis 去找資料)
    const labelMap = { 'positive': '正面', 'neutral': '中立', 'negative': '負面', 'unknown': '未知' };
    
    // 檢查 analysis 是否存在，再拿裡面的 overall_sentiment
    const sentiment = (data.analysis && data.analysis.overall_sentiment) 
                       ? data.analysis.overall_sentiment 
                       : { label: 'unknown', confidence: 0 };  
                       
    const labelClass = `label-${sentiment.label}`;
    const confidencePercent = Math.round(sentiment.confidence * 100);
    
    overallSentiment.textContent = `${labelMap[sentiment.label] } (信心度: ${confidencePercent}%)`;
    overallSentiment.className = `sentiment-badge ${labelClass}`;

    // 4. 填入大字總結
    summaryText.textContent = data.summary_text || "error";

    // 5. 處理語音播放器
    if (data.audio_base64) {
        audioPlayer.src = `data:audio/${data.audio_format || 'mp3'};base64,${data.audio_base64}`;
        audioContainer.classList.remove('hidden');
    } else {
        audioContainer.classList.add('hidden');
    }

    // 6. 處理各面向清單 (✨ 關鍵：多加一層 data.analysis 去找資料)
    aspectsList.innerHTML = '';
    
    // 檢查 analysis 和 aspect_sentiments 是否存在
    if (data.analysis && data.analysis.aspect_sentiments && data.analysis.aspect_sentiments.length > 0) {
        data.analysis.aspect_sentiments.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'aspect-item';

            const itemSent = item.sentiment || { label: 'neutral', confidence: 0 };
            const aspectText = labelMap[itemSent.label] ;
            const aspectClass = `label-${itemSent.label}`;
            const aspectConf = Math.round(itemSent.confidence * 100);

            // 留意這裡的名稱也是抓 aspect_display 或 aspect
            itemDiv.innerHTML = `
                <span class="aspect-name">${item.aspect_display || item.aspect || "未知面向"}</span>
                <div class="aspect-meta">
                    <span class="review-count">(${item.review_count } 則評論)</span>
                    <span class="sentiment-badge ${aspectClass}">${aspectText} ${aspectConf}%</span>
                </div>
            `;
            aspectsList.appendChild(itemDiv);
        });
    }

    // 7. 最後，把整個結果卡片秀出來！
    resultBox.classList.remove('hidden');
}