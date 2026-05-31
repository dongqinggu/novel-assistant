/**
 * Inspiration box - New interaction flow
 * 1. Input inspiration
 * 2. AI format + match local entities
 * 3. Show formatted memories + matched entities
 * 4. User confirms to save new memories and update matched ones
 */

// State
let currentFormattedMemories = [];
let currentMatchedEntities = [];
let currentSuggestions = [];

// Get elements
const inputEl = document.getElementById('inspiration-input');
const btnProcess = document.getElementById('btn-process');
const btnSearch = document.getElementById('btn-search');
const processResultEl = document.getElementById('process-result');
const formattedMemoriesEl = document.getElementById('formatted-memories');
const matchedEntitiesEl = document.getElementById('matched-entities');
const suggestionsSection = document.getElementById('suggestions-section');
const suggestionsList = document.getElementById('suggestions-list');
const relatedMemoriesEl = document.getElementById('related-memories');

/**
 * Main: Process inspiration (format + match)
 */
async function processInspiration() {
    const content = inputEl.value.trim();
    if (!content) {
        showMessage('请输入构思内容', 'error');
        return;
    }

    setLoading(true, '正在格式化并匹配...');

    try {
        const type = getSelectedType();
        
        // Call the process API
        const data = await api('/api/inspirations/process', {
            method: 'POST',
            body: { content, memory_type: type }
        });

        if (data.code === 0) {
            currentFormattedMemories = data.data.formatted_memories || [];
            currentMatchedEntities = data.data.matched_entities || [];
            
            // Display results
            displayProcessResult();
            
            // Also update related memories panel
            displayRelatedMemories(currentMatchedEntities);
            
            showMessage(`格式化 ${currentFormattedMemories.length} 条记忆，匹配 ${currentMatchedEntities.length} 个实体`);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (e) {
        showMessage('处理失败: ' + e.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Display formatted memories and matched entities
 */
function displayProcessResult() {
    // Display formatted memories
    if (currentFormattedMemories.length > 0) {
        let html = '';
        currentFormattedMemories.forEach((m, i) => {
            html += `
                <div class="format-item" data-index="${i}">
                    <div class="format-header">
                        <select class="format-type-select">
                            <option value="outline" ${m.type === 'outline' ? 'selected' : ''}>大纲</option>
                            <option value="character" ${m.type === 'character' ? 'selected' : ''}>人物</option>
                            <option value="scene" ${m.type === 'scene' ? 'selected' : ''}>场景</option>
                            <option value="plot" ${m.type === 'plot' ? 'selected' : ''}>剧情</option>
                            <option value="callback" ${m.type === 'callback' ? 'selected' : ''}>伏笔</option>
                            <option value="worldbuilding" ${m.type === 'worldbuilding' ? 'selected' : ''}>世界观</option>
                            <option value="note" ${m.type === 'note' ? 'selected' : ''}>笔记</option>
                        </select>
                        <input type="text" class="format-title-input" value="${escapeHtml(m.title || '')}" placeholder="标题">
                    </div>
                    <textarea class="format-content-textarea" rows="3" placeholder="内容">${escapeHtml(m.content || '')}</textarea>
                    <input type="text" class="format-tags-input" value="${escapeHtml((m.tags || []).join(', '))}" placeholder="标签1, 标签2">
                </div>
            `;
        });
        formattedMemoriesEl.innerHTML = html;
    } else {
        formattedMemoriesEl.innerHTML = '<p class="empty-hint">AI未能从构思中提取结构化内容</p>';
    }

    // Display matched entities
    if (currentMatchedEntities.length > 0) {
        let html = '';
        currentMatchedEntities.forEach(m => {
            html += `
                <div class="matched-item">
                    <label class="matched-checkbox">
                        <input type="checkbox" class="matched-select" value="${m.id}" checked data-type="${m.type}">
                        <span class="matched-info">
                            <span class="matched-type">${getTypeIcon(m.type)} ${getTypeName(m.type)}</span>
                            <a href="/entity/${m.id}" class="matched-name" target="_blank">${escapeHtml(m.name || m.title || '无标题')}</a>
                        </span>
                    </label>
                    <div class="matched-content">${escapeHtml(m.content.substring(0, 100))}${m.content.length > 100 ? '...' : ''}</div>
                    <div class="matched-actions">
                        <button class="btn btn-sm" onclick="viewEntity('${m.id}')">查看</button>
                        <button class="btn btn-sm" onclick="updateEntity('${m.id}', '${m.type}')">更新此实体</button>
                    </div>
                </div>
            `;
        });
        matchedEntitiesEl.innerHTML = html;
    } else {
        matchedEntitiesEl.innerHTML = '<p class="empty-hint">未匹配到本地实体</p>';
    }

    processResultEl.style.display = 'block';
}

/**
 * Confirm all: save new memories and link to matched ones
 */
async function confirmAll() {
    // Collect formatted memories
    const newMemories = [];
    document.querySelectorAll('.format-item').forEach(item => {
        newMemories.push({
            type: item.querySelector('.format-type-select').value,
            title: item.querySelector('.format-title-input').value,
            content: item.querySelector('.format-content-textarea').value,
            tags: item.querySelector('.format-tags-input').value.split(/[,，]/).map(t => t.trim()).filter(t => t),
        });
    });

    // Collect selected matched entities
    const matchedIds = [];
    document.querySelectorAll('.matched-select:checked').forEach(cb => {
        matchedIds.push(cb.value);
    });

    if (newMemories.length === 0 && matchedIds.length === 0) {
        showMessage('没有需要保存的内容', 'error');
        return;
    }

    setLoading(true, '正在保存...');

    try {
        // 1. Save new memories
        if (newMemories.length > 0) {
            const saveRes = await api('/api/inspirations/confirm', {
                method: 'POST',
                body: { memories: newMemories }
            });
            if (saveRes.code !== 0) {
                showMessage(saveRes.message, 'error');
                return;
            }
        }

        // 2. Link to matched entities (add relationship note)
        if (matchedIds.length > 0) {
            // Create a summary of new memories for the relationship note
            const summary = newMemories.map(m => `${getTypeName(m.type)}:${m.title || m.content.substring(0, 20)}`).join(', ');
            
            for (const id of matchedIds) {
                const entity = currentMatchedEntities.find(e => e.id === id);
                if (entity) {
                    // Update entity content with relationship note
                    const newContent = entity.content + `\n\n[关联更新: ${summary}]`;
                    await api(`/api/memories/${id}`, {
                        method: 'PUT',
                        body: { content: newContent }
                    });
                }
            }
        }

        showMessage(`成功保存 ${newMemories.length} 条新记忆，更新 ${matchedIds.length} 个实体`);
        
        // Clear and refresh
        setTimeout(() => {
            clearAll();
            window.location.reload();
        }, 1500);

    } catch (e) {
        showMessage('保存失败: ' + e.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Update a specific entity with formatted content
 */
async function updateEntity(entityId, entityType) {
    // Find the formatted memory that matches this entity type
    const matchingMemory = currentFormattedMemories.find(m => m.type === entityType);
    
    if (!matchingMemory) {
        showMessage(`没有找到类型为 ${getTypeName(entityType)} 的格式化内容`, 'error');
        return;
    }

    if (!confirm(`确定要更新这个${getTypeName(entityType)}吗？\n\n新内容：${matchingMemory.content.substring(0, 100)}...`)) {
        return;
    }

    try {
        const res = await api(`/api/memories/${entityId}`, {
            method: 'PUT',
            body: {
                content: matchingMemory.content,
                tags: matchingMemory.tags
            }
        });

        if (res.code === 0) {
            showMessage('实体更新成功');
        } else {
            showMessage(res.message, 'error');
        }
    } catch (e) {
        showMessage('更新失败: ' + e.message, 'error');
    }
}

/**
 * View entity in new page
 */
function viewEntity(entityId) {
    window.open(`/entity/${entityId}`, '_blank');
}

/**
 * Cancel process
 */
function cancelProcess() {
    processResultEl.style.display = 'none';
    currentFormattedMemories = [];
    currentMatchedEntities = [];
}

/**
 * Search memories only (without formatting)
 */
async function searchMemories() {
    const query = inputEl.value.trim();
    if (!query) {
        showMessage('请输入构思内容', 'error');
        return;
    }

    setLoading(true, '正在检索...');

    try {
        const type = getSelectedType();
        const data = await api('/api/inspirations/search', {
            method: 'POST',
            body: { query, type }
        });

        if (data.code === 0) {
            displayRelatedMemories(data.data.memories);
            showMessage(`找到 ${data.data.memories.length} 条相关记忆`);
        } else {
            showMessage(data.message, 'error');
        }
    } catch (e) {
        showMessage('检索失败: ' + e.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Display related memories in right panel
 */
function displayRelatedMemories(memories) {
    if (memories.length === 0) {
        relatedMemoriesEl.innerHTML = '<p class="empty-hint">未找到相关记忆</p>';
        return;
    }

    let html = '';
    memories.forEach(m => {
        html += `
            <div class="related-memory-item" onclick="window.open('/entity/${m.id}', '_blank')">
                <div class="related-memory-type">${getTypeIcon(m.type)} ${getTypeName(m.type)}</div>
                <div class="related-memory-title">${escapeHtml(m.name || m.title || '无标题')}</div>
                <div class="related-memory-content">${escapeHtml(m.content.substring(0, 80))}${m.content.length > 80 ? '...' : ''}</div>
            </div>
        `;
    });
    relatedMemoriesEl.innerHTML = html;
}

/**
 * Show AI advise
 */
async function showAdvise() {
    const query = inputEl.value.trim();
    if (!query) {
        showMessage('请先输入构思内容', 'error');
        return;
    }

    setLoading(true, '正在生成建议...');

    try {
        // Get related memories first
        const searchRes = await api('/api/inspirations/search', {
            method: 'POST',
            body: { query, type: getSelectedType() }
        });

        const relatedMemories = searchRes.code === 0 ? searchRes.data.memories : [];

        // Generate advise
        const adviseRes = await api('/api/inspirations/advise', {
            method: 'POST',
            body: {
                query,
                related_memories: relatedMemories.map(m => ({ id: m.id })),
                memory_type: getSelectedType()
            }
        });

        if (adviseRes.code === 0) {
            currentSuggestions = adviseRes.data.suggestions || [];
            displaySuggestions();
            showMessage('AI 建议生成成功');
        } else {
            showMessage(adviseRes.message, 'error');
        }
    } catch (e) {
        showMessage('生成建议失败: ' + e.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Display AI suggestions
 */
function displaySuggestions() {
    if (currentSuggestions.length === 0) {
        suggestionsSection.style.display = 'none';
        return;
    }

    let html = '';
    currentSuggestions.forEach((s, i) => {
        html += `
            <div class="suggestion-item">
                <span class="suggestion-number">${i + 1}.</span>
                <span class="suggestion-text">${escapeHtml(s)}</span>
                <button class="btn btn-sm" onclick="useSuggestion(${i})">使用</button>
            </div>
        `;
    });

    suggestionsList.innerHTML = html;
    suggestionsSection.style.display = 'block';
}

/**
 * Use a suggestion as inspiration
 */
function useSuggestion(index) {
    const suggestion = currentSuggestions[index];
    inputEl.value = suggestion;
    suggestionsSection.style.display = 'none';
    showMessage('建议已填入输入框，点击"智能处理"继续');
}

/**
 * Clear all
 */
function clearAll() {
    inputEl.value = '';
    processResultEl.style.display = 'none';
    suggestionsSection.style.display = 'none';
    relatedMemoriesEl.innerHTML = '<p class="empty-hint">输入构思后点击"智能处理"或"仅检索"</p>';
    currentFormattedMemories = [];
    currentMatchedEntities = [];
    currentSuggestions = [];
}

/**
 * Sync vector database
 */
async function syncVectorDB() {
    setLoading(true, '正在同步...');
    try {
        const data = await api('/api/vector/sync', { method: 'POST' });
        if (data.code === 0) {
            showMessage('向量库同步成功');
        } else {
            showMessage(data.message, 'error');
        }
    } catch (e) {
        showMessage('同步失败: ' + e.message, 'error');
    } finally {
        setLoading(false);
    }
}

/**
 * Get selected memory type
 */
function getSelectedType() {
    const selected = document.querySelector('input[name="memory-type"]:checked');
    return selected ? selected.value : 'auto';
}

/**
 * Set loading state
 */
function setLoading(loading, message = '') {
    btnProcess.disabled = loading;
    btnSearch.disabled = loading;
    if (loading) {
        btnProcess.textContent = message || '处理中...';
    } else {
        btnProcess.textContent = '✨ 智能处理';
    }
}

/**
 * Escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Get type icon
 */
function getTypeIcon(type) {
    const icons = {
        outline: '📋', character: '👤', scene: '📍',
        plot: '📖', callback: '🔗', worldbuilding: '🌍', note: '📝'
    };
    return icons[type] || '📄';
}

/**
 * Get type name
 */
function getTypeName(type) {
    const names = {
        outline: '大纲', character: '人物', scene: '场景',
        plot: '剧情', callback: '伏笔', worldbuilding: '世界观', note: '笔记'
    };
    return names[type] || type;
}
