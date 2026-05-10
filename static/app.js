const API_BASE = '/projects';
let currentProjectId = null;
let eventSource = null;

const STEP_CONFIG = {
    'generate_lyrics': { title: 'LYRICS GENERATION', number: '02', icon: '◆' },
    'generate_song': { title: 'MUSIC COMPOSITION', number: '03', icon: '♦' },
    'extract_timestamps': { title: 'TIMESTAMP EXTRACTION', number: '04', icon: '◇' },
    'generate_scene_list': { title: 'SCENE BREAKDOWN', number: '05', icon: '◈' },
    'generate_video_scenes': { title: 'VIDEO PRODUCTION', number: '06', icon: '◊' },
    'finalize_video': { title: 'FINAL MASTERING', number: '07', icon: '★' }
};

document.getElementById('btn-start').addEventListener('click', startProject);

async function startProject() {
    const topic = document.getElementById('topic').value;
    const style = document.getElementById('style').value;
    const quality = document.getElementById('quality').value;

    if (!topic || !style) {
        alert('Please provide both topic and style.');
        return;
    }

    try {
        const response = await fetch(API_BASE, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, style, quality })
        });
        const data = await response.json();
        currentProjectId = data.project_id;
        
        document.getElementById('row-inputs').classList.remove('active');
        document.getElementById('row-inputs').classList.add('completed');
        const inputsProgress = document.querySelector('#row-inputs .progress-fill');
        if (inputsProgress) inputsProgress.style.width = '100%';
        
        initializeTimeline();
        connectSSE(currentProjectId);
    } catch (err) {
        console.error('Failed to start project:', err);
    }
}

function initializeTimeline() {
    const container = document.getElementById('dynamic-rows');
    container.innerHTML = '';
    
    Object.keys(STEP_CONFIG).forEach((stepName) => {
        const template = document.getElementById('step-row-template');
        const clone = template.content.cloneNode(true);
        const section = clone.querySelector('section');
        const config = STEP_CONFIG[stepName];
        
        section.id = `row-${stepName}`;
        section.querySelector('.step-title').textContent = config.title;
        section.querySelector('.step-status').textContent = config.number;
        
        section.querySelector('.edit-btn').onclick = () => handleEdit(stepName);
        section.querySelector('.regen-btn').onclick = () => handleRegenerate(stepName);
        
        container.appendChild(clone);
    });
}

function connectSSE(projectId) {
    if (eventSource) eventSource.close();
    
    eventSource = new EventSource(`${API_BASE}/${projectId}/events`);
    
    eventSource.onmessage = (event) => {
        const project = JSON.parse(event.data);
        updateUI(project);
    };
    
    eventSource.onerror = (err) => {
        console.error('SSE Error:', err);
        eventSource.close();
    };
}

function updateUI(project) {
    Object.entries(project.steps).forEach(([name, step]) => {
        const row = document.getElementById(`row-${name}`);
        if (!row) return;

        row.classList.remove('active', 'completed', 'failed');
        if (step.status === 'running') row.classList.add('active');
        if (step.status === 'completed') row.classList.add('completed');
        if (step.status === 'failed') row.classList.add('failed');

        const statusEl = row.querySelector('.step-status');
        const config = STEP_CONFIG[name];
        
        if (step.status === 'running') {
            statusEl.innerHTML = '<span class="step-spinner"></span>';
        } else if (step.status === 'completed') {
            statusEl.textContent = config.icon;
        } else if (step.status === 'failed') {
            statusEl.textContent = '✕';
        } else {
            statusEl.textContent = config.number;
        }

        const fill = row.querySelector('.progress-fill');
        fill.style.width = `${step.progress * 100}%`;

        if (step.data) {
            renderStepData(name, step.data, row.querySelector('.content-display'));
        }
    });

    const activeRow = document.querySelector('.row.active');
    if (activeRow) {
        activeRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function renderStepData(name, data, container) {
    if (container.dataset.lastData === JSON.stringify(data)) return;
    container.dataset.lastData = JSON.stringify(data);

    container.innerHTML = '';
    
    if (name === 'generate_lyrics') {
        const div = document.createElement('div');
        div.className = 'lyrics-display';
        div.textContent = data;
        container.appendChild(div);
    } 
    else if (name === 'generate_song') {
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = `/${data}`;
        container.appendChild(audio);
    }
    else if (name === 'generate_scene_list') {
        const list = document.createElement('div');
        list.className = 'scene-list';
        data.forEach((scene, index) => {
            const item = document.createElement('div');
            item.className = 'scene-item';
            const idx = String(index + 1).padStart(2, '0');
            item.innerHTML = `
                <span class="scene-time">[${idx}] ${scene.start.toFixed(2)}s — ${scene.end.toFixed(2)}s</span>
                <p>${scene.description}</p>
            `;
            list.appendChild(item);
        });
        container.appendChild(list);
    }
    else if (name === 'finalize_video') {
        const video = document.createElement('video');
        video.controls = true;
        video.src = `/${data}`;
        container.appendChild(video);
    }
    else {
        container.textContent = typeof data === 'string' ? data : JSON.stringify(data);
    }
}

let editingStep = null;

async function handleEdit(stepName) {
    const row = document.getElementById(`row-${stepName}`);
    const display = row.querySelector('.content-display');

    if (editingStep === stepName) {
        const textarea = display.querySelector('textarea');
        if (textarea) {
            const newData = textarea.value;
            await fetch(`${API_BASE}/${currentProjectId}/steps/${stepName}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ data: newData })
            });
            renderStepData(stepName, newData, display);
        }
        editingStep = null;
        return;
    }

    const project = await (await fetch(`${API_BASE}/${currentProjectId}`)).json();
    const currentData = project.steps[stepName].data;
    const dataStr = typeof currentData === 'string' ? currentData : JSON.stringify(currentData, null, 2);

    display.innerHTML = `<textarea class="edit-textarea">${dataStr.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</textarea>`;
    display.querySelector('textarea').focus();
    editingStep = stepName;

    display.querySelector('textarea').addEventListener('blur', () => {
        if (editingStep === stepName) {
            handleEdit(stepName);
        }
    });
}

async function handleRegenerate(stepName) {
    if (!confirm(`REGENERATE FROM ${STEP_CONFIG[stepName].title}? DOWNSTREAM STEPS WILL BE OVERWRITTEN.`)) return;

    await fetch(`${API_BASE}/${currentProjectId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_step: stepName })
    });
}
