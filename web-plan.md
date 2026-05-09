# Web Interface Implementation Plan - Music Video Automation (Vanilla JS)

This plan outlines the steps to build a stylish but simple interactive web interface using Vanilla HTML, CSS, and JavaScript.

## 1. Frontend Infrastructure
- [ ] Create `static/index.html`: Base structure with a vertical container for rows.
- [ ] Create `static/style.css`: Stylish **Vanilla CSS** with a focus on typography, spacing, and modern dark-mode aesthetic.
- [ ] Create `static/app.js`: Simple state management and DOM manipulation logic.
- [ ] Implement SSE listener using native `EventSource` to update rows.

## 2. API & Backend Enhancements
- [ ] Mount a static files directory in FastAPI to serve the frontend.
- [ ] `GET /projects/{project_id}`: Retrieve the full project state.
- [ ] `PATCH /projects/{project_id}/steps/{step_name}`: Update step data (e.g., modified lyrics).
- [ ] `POST /projects/{project_id}/regenerate`: Re-trigger pipeline from a specific stage.
- [ ] `app.mount("/output", StaticFiles(directory="output"), name="output")`: Serve generated media.

## 3. UI Components (Vertical Timeline)
- [ ] **Inputs Row**: Topic & Style textareas + "Start" button.
- [ ] **Step Rows**: A reusable HTML template for each step.
    - Status indicator (spinner, checkmark, or error).
    - Content area (Textarea for lyrics, `<audio>` for song, `<img>` grid for assets, `<video>` for clips).
    - Action buttons: "Edit", "Regenerate From Here".

## 4. Interaction Logic (`app.js`)
- [ ] `updateRow(stepName, data)`: Surgical DOM updates to keep the UI snappy.
- [ ] `handleRegenerate(stepName)`: Send the signal to the backend and reset downstream UI states.
- [ ] Automatic scrolling to the active row.

## 5. Visual Polish
- [ ] CSS Grid/Flexbox for the vertical timeline.
- [ ] Subtle animations for status changes.
- [ ] Responsive design (works on desktop and tablet).

## 6. Verification
- [ ] Start a project and watch rows "fill in" via SSE.
- [ ] Edit lyrics, hit "Regenerate", and verify the song/video updates.
- [ ] Test the full flow from a clean browser refresh.
