"""Standalone HTML playground for manual RAG testing."""

PLAYGROUND_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>RecipeProject RAG Playground</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      :root {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #0f172a;
        background-color: #f5f5f5;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: linear-gradient(135deg, #eef2ff, #fafafa);
        min-height: 100vh;
      }
      .page {
        max-width: 1200px;
        padding: 2.5rem 1.5rem 3rem;
        margin: 0 auto;
        display: grid;
        gap: 1.5rem;
      }
      header h1 {
        margin: 0;
        font-size: 2rem;
      }
      header p {
        margin: 0.4rem 0 0;
        color: #475569;
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 1.5rem;
      }
      .panel {
        background: #fff;
        border-radius: 16px;
        padding: 1.75rem;
        box-shadow: 0 25px 55px rgba(15, 23, 42, 0.08);
      }
      .panel h2 {
        margin: 0 0 1rem;
        font-size: 1.2rem;
      }
      textarea {
        width: 100%;
        min-height: 160px;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #d4d4d8;
        font-size: 1rem;
        resize: vertical;
        line-height: 1.5;
      }
      textarea:focus,
      input:focus,
      select:focus {
        outline: none;
        border-color: #6366f1;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
      }
      .controls {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.9rem;
        margin-top: 1.2rem;
      }
      label {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        font-size: 0.95rem;
        color: #475569;
      }
      input,
      select {
        padding: 0.55rem 0.65rem;
        border-radius: 10px;
        border: 1px solid #d4d4d8;
        font-size: 0.95rem;
      }
      .toggle {
        flex-direction: row;
        align-items: center;
        gap: 0.5rem;
      }
      .actions {
        display: flex;
        gap: 0.8rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
      }
      button {
        background: #4f46e5;
        border: none;
        color: #fff;
        padding: 0.85rem 1.6rem;
        border-radius: 999px;
        font-size: 1rem;
        cursor: pointer;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }
      button:disabled {
        opacity: 0.55;
        cursor: not-allowed;
        box-shadow: none;
        transform: none;
      }
      button:not(:disabled):hover {
        transform: translateY(-1px);
        box-shadow: 0 15px 30px rgba(79, 70, 229, 0.2);
      }
      .status {
        min-height: 1.3rem;
        color: #475569;
        font-size: 0.95rem;
        margin-top: 0.4rem;
      }
      .answer-box {
        min-height: 160px;
        padding: 1rem;
        border-radius: 12px;
        border: 1px dashed #cbd5f5;
        background: #f8fafc;
        white-space: pre-wrap;
        line-height: 1.55;
      }
      .docs {
        margin-top: 1.2rem;
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
      }
      .doc {
        padding: 0.9rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        background: #fff;
      }
      .doc-header {
        display: flex;
        justify-content: space-between;
        gap: 0.6rem;
        font-size: 0.92rem;
        color: #334155;
        font-weight: 600;
      }
      .doc-content {
        margin-top: 0.4rem;
        color: #475569;
        white-space: pre-wrap;
      }
      code {
        font-family: 'JetBrains Mono', 'SFMono-Regular', Consolas, monospace;
        background: rgba(99, 102, 241, 0.08);
        padding: 0.15rem 0.45rem;
        border-radius: 6px;
        font-size: 0.9rem;
      }
      @media (max-width: 640px) {
        .panel {
          padding: 1.2rem;
        }
        textarea {
          min-height: 130px;
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <header>
        <h1>RecipeProject RAG Playground</h1>
        <p>直接点击 <code>发送请求</code> 即可命中后端 <code>/chat</code>，支持流式和重排参数测试。</p>
      </header>
      <div class="grid">
        <section class="panel">
          <h2>请求配置</h2>
          <textarea id="query" placeholder="例如：有什么适合儿童的无坚果甜点？"></textarea>
          <div class="controls">
            <label>
              Top-K
              <input id="topk" type="number" min="1" max="50" placeholder="默认" />
            </label>
            <label>
              重排策略
              <select id="use-rerank">
                <option value="default">跟随配置</option>
                <option value="true">强制开启</option>
                <option value="false">强制关闭</option>
              </select>
            </label>
            <label>
              重排模式
              <select id="rerank-mode">
                <option value="">默认</option>
                <option value="cross">Cross</option>
                <option value="bi">Bi</option>
              </select>
            </label>
            <label>
              重排 Top-K
              <input id="rerank-topk" type="number" min="1" max="50" placeholder="默认" />
            </label>
            <label class="toggle">
              <input id="stream" type="checkbox" />
              流式输出
            </label>
          </div>
          <div class="actions">
            <button id="send">发送请求</button>
            <button id="clear" type="button">清空输出</button>
          </div>
          <div class="status" id="status"></div>
        </section>
        <section class="panel">
          <h2>返回内容</h2>
          <div class="answer-box" id="answer">尚未发送请求。</div>
          <div class="docs" id="documents"></div>
        </section>
      </div>
    </div>
    <script>
      const $ = (id) => document.getElementById(id);
      const sendBtn = $('send');
      const clearBtn = $('clear');
      const statusEl = $('status');
      const answerEl = $('answer');
      const docsEl = $('documents');

      console.log('[RAG UI] playground script loaded');

      const renderDocs = (docs = []) => {
        docsEl.innerHTML = '';
        if (!docs.length) {
          docsEl.style.display = 'none';
          return;
        }
        docsEl.style.display = 'flex';
        docsEl.innerHTML = docs
          .map((doc, idx) => {
            const label = doc.title || doc.id || `Document ${idx + 1}`;
            const score = typeof doc.score === 'number' ? doc.score.toFixed(3) : 'N/A';
            const content = (doc.content || '')
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;');
            return `
              <article class="doc">
                <div class="doc-header">
                  <span>${label}</span>
                  <span>score: ${score}</span>
                </div>
                <div class="doc-content">${content}</div>
              </article>
            `;
          })
          .join('');
      };

      const buildPayload = () => {
        const payload = {
          query: $('query').value.trim(),
          stream: $('stream').checked,
        };
        const topK = $('topk').value;
        if (topK) payload.top_k = Number(topK);
        const rerankChoice = $('use-rerank').value;
        if (rerankChoice !== 'default') {
          payload.use_rerank = rerankChoice === 'true';
        }
        const mode = $('rerank-mode').value;
        if (mode) payload.rerank_mode = mode;
        const rerankTop = $('rerank-topk').value;
        if (rerankTop) payload.rerank_top_k = Number(rerankTop);
        return payload;
      };

      const resetOutput = () => {
        answerEl.textContent = '尚未发送请求。';
        docsEl.innerHTML = '';
        docsEl.style.display = 'none';
        statusEl.textContent = '';
      };

      const parseEventBlock = (block) => {
        const lines = block.split('\\n');
        let event = 'message';
        const dataLines = [];
        for (const line of lines) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
        }
        return { event, data: dataLines.join('\\n') };
      };

      const safeParse = (text) => {
        try {
          return JSON.parse(text);
        } catch (err) {
          return null;
        }
      };

      async function handleStream(resp) {
        const reader = resp.body?.getReader();
        if (!reader) throw new Error('浏览器不支持流式响应');
        const decoder = new TextDecoder('utf-8');
        let buffer = '';
        let answer = '';
        answerEl.textContent = '';
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true }).replace(/\\r\\n/g, '\\n');
          let boundary;
          while ((boundary = buffer.indexOf('\\n\\n')) !== -1) {
            const chunk = buffer.slice(0, boundary).trim();
            buffer = buffer.slice(boundary + 2);
            if (!chunk) continue;
            const evt = parseEventBlock(chunk);
            if (!evt.data) continue;
            if (evt.event === 'meta') {
              const meta = safeParse(evt.data) || {};
              renderDocs(meta.documents || []);
              statusEl.textContent = `模型：${meta.model || '未知'}`;
            } else if (evt.event === 'delta') {
              answer += evt.data;
              answerEl.textContent = answer;
            } else if (evt.event === 'end') {
              const final = safeParse(evt.data) || {};
              if (final.answer) answerEl.textContent = final.answer;
              statusEl.textContent = '流式输出完成';
            } else if (evt.event === 'error') {
              const errPayload = safeParse(evt.data) || {};
              throw new Error(errPayload.message || '流式请求失败');
            }
          }
        }
        if (buffer.trim()) {
          const evt = parseEventBlock(buffer.trim());
          if (evt.event === 'error') {
            const errPayload = safeParse(evt.data) || {};
            throw new Error(errPayload.message || '流式请求失败');
          }
        }
      }

      async function callChat() {
        const payload = buildPayload();
        console.log('[RAG UI] callChat invoked', payload);
        if (!payload.query) {
          alert('请输入问题再发送');
          return;
        }
        const stream = payload.stream;
        sendBtn.disabled = true;
        statusEl.textContent = '请求发送中...';
        answerEl.textContent = stream ? '' : '等待返回...';
        docsEl.innerHTML = '';
        docsEl.style.display = 'none';
        try {
          const resp = await fetch('/chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Accept: stream ? 'text/event-stream' : 'application/json',
            },
            body: JSON.stringify(payload),
          });
          console.log('[RAG UI] /chat response status', resp.status);
          if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            throw new Error(err.detail || resp.statusText || '请求失败');
          }
          if (stream) {
            await handleStream(resp);
          } else {
            const data = await resp.json();
            answerEl.textContent = data.answer || '未返回答案';
            renderDocs(data.documents || []);
            statusEl.textContent = `模型：${data.model || '未知'}`;
          }
        } catch (err) {
          console.error('[RAG UI] callChat failed', err);
          statusEl.textContent = err.message;
        } finally {
          sendBtn.disabled = false;
        }
      }

      sendBtn.addEventListener('click', callChat);
      clearBtn.addEventListener('click', resetOutput);
      $('query').addEventListener('keydown', (evt) => {
        if ((evt.metaKey || evt.ctrlKey) && evt.key === 'Enter') {
          callChat();
        }
      });
    </script>
  </body>
</html>
"""
