// worker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");

let pyodide = null;

async function loadPyodideEngine() {
    try {
        pyodide = await loadPyodide();
        // Redirect stdout/stderr to main thread
        pyodide.setStdout({
            batched: (text) => {
                postMessage({ type: 'stdout', content: text });
            }
        });
        pyodide.setStderr({
            batched: (text) => {
                postMessage({ type: 'stderr', content: text });
            }
        });
        postMessage({ type: 'ready' });
    } catch (err) {
        postMessage({ type: 'error', content: err.toString() });
    }
}

loadPyodideEngine();

self.onmessage = async (event) => {
    const { code } = event.data;
    if (!pyodide) {
        postMessage({ type: 'error', content: "Pyodide not ready yet." });
        return;
    }

    try {
        await pyodide.runPythonAsync(code);
        postMessage({ type: 'success' });
    } catch (err) {
        postMessage({ type: 'error', content: err.toString() });
    }
};
