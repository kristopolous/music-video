const API_BASE = '/projects';
let currentProjectId = null;
let eventSource = null;

const STEP_CONFIG = {
    'generate_lyrics': { title: 'Lyrics Generation', icon: '📝' },
    'generate_song': { title: 'Music Composition', icon: '🎵' },
    'extract_timestamps': { title: 'Timestamp Extraction', icon: '⏱️' },
    'generate_scene_list': { title: 'Scene Breakdown', icon: '🎬' },
    'generate_video_scenes': { title: 'Video Production', icon: '📽️' },
    'finalize_video': { title: 'Final Mastering', icon: '✨' }
};

// --- Initialization ---
document.getElementById('btn-start').addEventListener('click', startProject);

// --- Core Actions ---
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
        
        // Hide inputs (optionally) or just mark active
        document.getElementById('row-inputs').classList.remove('active');
        document.getElementById('row-inputs').classList.add('completed');
        
        initializeTimeline();
        connectSSE(currentProjectId);
    } catch (err) {
        console.error('Failed to start project:', err);
    }
}

function initializeTimeline() {
    const container = document.getElementById('dynamic-rows');
    container.innerHTML = ''; // Clear previous if any
    
    Object.keys(STEP_CONFIG).forEach((stepName, index) => {
        const template = document.getElementById('step-row-template');
        const clone = template.content.cloneNode(true);
        const section = clone.querySelector('section');
        
        section.id = `row-${stepName}`;
        section.querySelector('.step-title').textContent = STEP_CONFIG[stepName].title;
        section.querySelector('.step-status').textContent = STEP_CONFIG[stepName].icon;
        
        // Setup buttons
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

// --- UI Updates ---
function updateUI(project) {
    Object.entries(project.steps).forEach(([name, step]) => {
        const row = document.getElementById(`row-${name}`);
        if (!row) return;

        // Update classes
        row.classList.remove('active', 'completed', 'failed');
        if (step.status === 'running') row.classList.add('active');
        if (step.status === 'completed') row.classList.add('completed');
        if (step.status === 'failed') row.classList.add('failed');

        // Update progress
        const fill = row.querySelector('.progress-fill');
        fill.style.width = `${step.progress * 100}%`;

        // Update content if data is present
        if (step.data) {
            renderStepData(name, step.data, row.querySelector('.content-display'));
        }
    });

    // Auto-scroll to active row
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
        audio.src = `/${data}`; // Serves from /output
        container.appendChild(audio);
    }
    else if (name === 'generate_scene_list') {
        const list = document.createElement('div');
        list.className = 'scene-list';
        data.forEach(scene => {
            const item = document.createElement('div');
            item.className = 'scene-item';
            item.innerHTML = `
                <span class="scene-time">${scene.start.toFixed(2)}s - ${scene.end.toFixed(2)}s</span>
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

// --- Interactive Handlers ---
async function handleEdit(stepName) {
    const row = document.getElementById(`row-${stepName}`);
    const display = row.querySelector('.content-display');
    const project = await (await fetch(`${API_BASE}/${currentProjectId}`)).json();
    const currentData = project.steps[stepName].data;

    // Simple prompt for now, can be improved to inline textarea
    const newData = prompt(`Edit ${STEP_CONFIG[stepName].title}:`, typeof currentData === 'string' ? currentData : JSON.stringify(currentData));
    
    if (newData !== null) {
        let parsedData = newData;
        try { parsedData = JSON.parse(newData); } catch(e) {}

        await fetch(`${API_BASE}/${currentProjectId}/steps/${stepName}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: parsedData })
        });
        
        // Refresh local UI content
        renderStepData(stepName, parsedData, display);
    }
}

async function handleRegenerate(stepName) {
    if (!confirm(`Regenerate from ${STEP_CONFIG[stepName].title}? Downstream steps will be overwritten.`)) return;

    await fetch(`${API_BASE}/${currentProjectId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_step: stepName })
    });
    
    // UI will update automatically via SSE
}
