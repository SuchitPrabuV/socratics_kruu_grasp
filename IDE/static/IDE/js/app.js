// Global variables
var editor;
var pyodide;
var lastError = "";
var currentScore = 0;
var decorations = [];
var avatarAnim;
var outputBuffer = "";

// Initialize Monaco
require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.38.0/min/vs' } });
require(['vs/editor/editor.main'], function () {
    editor = monaco.editor.create(document.getElementById('editor-container'), {
        value: window.problemConfig.starterCode || [
            'def main():',
            '    print("Hello Human!")',
            '    for i in range(3):',
            '        print("Counting:", i)',
            '',
            'if __name__ == "__main__":',
            '    main()'
        ].join('\n'),
        language: 'python',
        theme: 'vs-dark',
        automaticLayout: true,
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "'JetBrains Mono', Consolas, monospace",
        scrollBeyondLastLine: false,
        renderLineHighlight: "all",
    });
});

// Initialize Lottie Avatar
function initAvatar() {
    avatarAnim = lottie.loadAnimation({
        container: document.getElementById('socratis-avatar'),
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: 'https://assets5.lottiefiles.com/packages/lf20_jR229r.json' // Robot Idle
    });
}
initAvatar();

function setAvatarState(state) {
    if (!avatarAnim) return;
    if (state === 'thinking') {
        avatarAnim.setSpeed(2);
    } else if (state === 'celebration') {
        avatarAnim.setSpeed(0.5);
    } else {
        avatarAnim.setSpeed(1);
    }
}

// Initialize Pyodide
async function loadEngine() {
    const status = document.getElementById('pyodide-status');
    try {
        if (typeof loadPyodide === 'undefined') {
            status.innerText = "Error: Offline?";
            status.style.color = "var(--error-color)";
            return;
        }

        // Use CDN or local if configured
        pyodide = await loadPyodide({
            indexURL: "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/"
        });

        status.innerText = "Ready";
        status.style.color = "var(--success-color)";
        document.getElementById('run-btn').disabled = false;

        updateScoreDisplay();
    } catch (err) {
        console.error("Failed to load Pyodide:", err);
        status.innerText = "Load Failed";
        status.style.color = "var(--error-color)";
    }
}
loadEngine();

// -- UTILS --
function clearTerminal() {
    document.getElementById('terminal').innerHTML = "";
    outputBuffer = "";
}

function addToTerminal(text, isError = false) {
    const terminal = document.getElementById('terminal');
    const span = document.createElement('span');
    span.className = isError ? 'output-error' : 'output-log';
    span.innerText = text;
    terminal.appendChild(span);

    if (!isError) {
        outputBuffer += text;
    }
}

function clearDecorations() {
    if (editor && decorations) {
        decorations = editor.deltaDecorations(decorations, []);
    }
}

// -- DEMO MODE --
function loadDemo() {
    if (!editor) return;
    const buggyCode = [
        'def count_down(n):',
        '    while n > 0:',
        '        print(n)',
        '        # Ooops, forgot to decrement!',
        '        # n = n - 1',
        '',
        'count_down(5)'
    ].join('\n');

    editor.setValue(buggyCode);
    clearTerminal();
    addToTerminal("Demo Loaded: Infinite Loop Logic.\nClick RUN.");
}

// -- RUN LOGIC --
async function runCode() {
    if (!pyodide || !editor) return;

    clearTerminal();
    clearDecorations();
    const userCode = editor.getValue();

    setAvatarState('thinking');
    document.getElementById('ask-btn').style.display = 'none';
    lastError = "";

    pyodide.setStdout({
        batched: (text) => {
            addToTerminal(text + "\n");
        }
    });

    try {
        await pyodide.runPythonAsync(userCode);

        // Validation Logic
        const expected = window.problemConfig.expectedOutput;
        if (expected && outputBuffer.trim() !== expected.trim()) {
            addToTerminal(`\n[Verifier] Output Mismatch.\nExpected:\n${expected}\nGot:\n${outputBuffer}`, true);
            setAvatarState('idle');
        } else {
            // Success!
            setAvatarState('celebration');
            addToTerminal("\n[Verifier] Success! Correct Output.", false);
            recordSuccess(userCode);
        }

    } catch (err) {
        lastError = err.toString();
        addToTerminal(lastError + "\n", true);
        setAvatarState('idle');

        const askBtn = document.getElementById('ask-btn');
        askBtn.style.display = 'flex';
        const chatM = document.getElementById('mentor-chat');
        chatM.scrollTop = chatM.scrollHeight;
    }
}

// -- ASK SOCRATIS --
async function askSocratis() {
    const mentorChat = document.getElementById('mentor-chat');
    const askBtn = document.getElementById('ask-btn');
    const userCode = editor.getValue();
    const errorMsg = lastError || "No runtime error, but logic seems wrong.";

    setAvatarState('thinking');

    // 1. User Bubble
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-bubble chat-user';
    userDiv.innerText = "Student: " + errorMsg.split('\n')[0];
    mentorChat.insertBefore(userDiv, document.getElementById('ask-container'));

    // 2. Loading Bubble
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-bubble chat-bot text-dim';
    loadingDiv.innerText = "Socratis is analyzing logic structure...";
    loadingDiv.id = "loading-bubble";
    mentorChat.insertBefore(loadingDiv, document.getElementById('ask-container'));

    askBtn.style.display = 'none';
    mentorChat.scrollTop = mentorChat.scrollHeight;

    try {
        const response = await fetch('/api/hint/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: userCode,
                error: errorMsg,
                problem_id: window.problemConfig.problemId
            })
        });

        const data = await response.json();
        document.getElementById('loading-bubble').remove();
        setAvatarState('idle');

        // 3. Bot Response Bubble
        const botDiv = document.createElement('div');
        botDiv.className = 'chat-bubble chat-bot';
        botDiv.innerHTML = `<strong style="color: #4ec9b0">Socratis:</strong> ${data.hint}`;
        mentorChat.insertBefore(botDiv, document.getElementById('ask-container'));

        // 4. Highlight Line (Mock Logic)
        if (data.analysis && data.analysis.line) {
            highlightLine(data.analysis.line);
        } else {
            let lineNo = 1;
            const match = errorMsg.match(/line (\d+)/);
            if (match) {
                lineNo = parseInt(match[1]);
                highlightLine(lineNo);
            }
        }

        mentorChat.scrollTop = mentorChat.scrollHeight;

    } catch (err) {
        console.error("API Error:", err);
        if (document.getElementById('loading-bubble'))
            document.getElementById('loading-bubble').innerText = "System Failure.";
    }
}

function highlightLine(lineNum) {
    decorations = editor.deltaDecorations(decorations, [
        {
            range: new monaco.Range(lineNum, 1, lineNum, 1),
            options: {
                isWholeLine: true,
                className: 'myContentClass',
                glyphMarginClassName: 'myGlyphMarginClass'
            }
        }
    ]);
}

async function recordSuccess(successfulCode) {
    try {
        const response = await fetch('/api/success/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: successfulCode,
                problem_id: window.problemConfig.problemId
            })
        });
        const data = await response.json();
        if (data.status === 'success') {
            updateScoreDisplay(data.new_score, data.breakdown, data.gained);
        }
    } catch (err) { console.error(err); }
}

function updateScoreDisplay(newScore, breakdown, gained) {
    // Update Number
    if (newScore !== undefined) currentScore = newScore;
    document.getElementById('score-val').innerText = `${currentScore} XP`;

    // Update Bar
    const level = Math.floor(currentScore / 500) + 1;
    document.getElementById('lvl-val').innerText = level;

    const progressInLevel = currentScore % 500;
    const percentage = (progressInLevel / 500) * 100;
    document.getElementById('progress-bar-fill').style.width = percentage + "%";

    // Update Breakdown Tooltip
    if (breakdown) {
        let html = "<strong>Mastery Breakdown:</strong><br>";
        breakdown.forEach(item => {
            html += `• ${item.concept}: Lvl ${Math.floor(item.score / 100)} (${item.score} XP)<br>`;
        });
        document.getElementById('xp-breakdown').innerHTML = html;
    }

    if (gained) {
        console.log("Gained XP:", gained);
    }
}

// Initial Fetch
fetch('/api/progress/').then(r => r.json()).then(data => {
    updateScoreDisplay(data.total_score, data.mastery);
});
