// Safe JSON fetch helper
async function safeFetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        // Check if response is OK
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            console.error('Non-JSON response:', text);
            throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 100)}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Update timestamp
function updateTimestamp() {
    document.getElementById('timestamp').textContent = new Date().toLocaleString();
}
setInterval(updateTimestamp, 1000);
updateTimestamp();

// Handle Enter key in command input
function handleCommandEnter(event) {
    if (event.key === 'Enter') {
        executeCommand();
    }
}

// Show/hide sudo password field based on command type
document.getElementById('commandType').addEventListener('change', function() {
    const commandType = this.value;
    const passwordSection = document.getElementById('sudoPasswordSection');
    
    if (commandType === 'sudo') {
        passwordSection.style.display = 'block';
    } else {
        passwordSection.style.display = 'none';
        document.getElementById('sudoPassword').value = ''; // Clear password
    }
});

// Persistent Terminal Session Management
let persistentTerminalSession = null;
let currentWorkingDirectory = '';

async function togglePersistentTerminal() {
    const checkbox = document.getElementById('persistentTerminal');
    const outputDiv = document.getElementById('commandOutput');
    
    if (checkbox.checked) {
        // Create new persistent terminal session
        try {
            outputDiv.innerHTML = '<span style="color: #ffff00;">Creating persistent terminal session...</span>';
            
            const result = await safeFetchJSON('/api/terminal/create', { method: 'POST' });
            
            if (result.success) {
                persistentTerminalSession = result.session_id;
                currentWorkingDirectory = result.cwd;
                outputDiv.innerHTML = `<span style="color: #00ff00;">✅ Persistent terminal session created!</span>\n<span style="color: #007acc;">Session ID: ${result.session_id}</span>\n<span style="color: #888;">Working directory: ${result.cwd}</span>\n<span style="color: #ffff00;">You can now use commands like 'cd', and the directory will persist between commands.</span>`;
                
                // Update machine info with current directory
                if (document.getElementById('machineInfo')) {
                    const machineText = document.getElementById('machineInfo').textContent;
                    const baseInfo = machineText.split(':')[0];
                    document.getElementById('machineInfo').innerHTML = `${baseInfo} : <span style="color: #ffff00;">${result.cwd}</span>`;
                }
            } else {
                checkbox.checked = false;
                outputDiv.innerHTML = `<span style="color: #ff6b35;">Failed to create terminal session: ${result.error}</span>`;
            }
        } catch (error) {
            checkbox.checked = false;
            outputDiv.innerHTML = `<span style="color: #ff6b35;">Error: ${error.message}</span>`;
        }
    } else {
        // Close persistent terminal session
        if (persistentTerminalSession) {
            try {
                await safeFetchJSON(`/api/terminal/close/${persistentTerminalSession}`, { method: 'POST' });
                outputDiv.innerHTML = '<span style="color: #888;">Persistent terminal session closed.</span>';
                persistentTerminalSession = null;
                currentWorkingDirectory = '';
                
                // Reset machine info
                getMachineInfo();
            } catch (error) {
                console.error('Error closing terminal:', error);
            }
        }
    }
}

async function executeInPersistentTerminal(command) {
    if (!persistentTerminalSession) {
        return {
            success: false,
            error: 'No persistent terminal session. Please enable persistent terminal mode.'
        };
    }
    
    try {
        const result = await safeFetchJSON(`/api/terminal/execute/${persistentTerminalSession}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });
        
        if (result.success && result.cwd) {
            currentWorkingDirectory = result.cwd;
            // Update display with current directory
            if (document.getElementById('machineInfo')) {
                const machineText = document.getElementById('machineInfo').textContent;
                const baseInfo = machineText.split(':')[0];
                document.getElementById('machineInfo').innerHTML = `${baseInfo} : <span style="color: #ffff00;">${result.cwd}</span>`;
            }
        }
        
        return result;
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

// Quick command execution
function quickCommand(cmd) {
    document.getElementById('command').value = cmd;
    // Reset to normal user for quick commands
    document.getElementById('commandType').value = 'normal';
    document.getElementById('sudoPasswordSection').style.display = 'none';
    executeCommand();
}

// Clear output areas
function clearOutput(elementId) {
    const element = document.getElementById(elementId);
    
    // Special handling for command output in persistent terminal mode
    if (elementId === 'commandOutput') {
        const persistentCheckbox = document.getElementById('persistentTerminal');
        if (persistentCheckbox && persistentCheckbox.checked && persistentTerminalSession) {
            element.innerHTML = '<span style="color: #00ff00;">✅ Persistent terminal session active</span>\n<span style="color: #888;">Session ID: ' + persistentTerminalSession + '</span>\n<span style="color: #888;">Working directory: ' + currentWorkingDirectory + '</span>\n<span style="color: #ffff00;">Command history cleared. Session still active.</span>';
        } else {
            element.textContent = 'Terminal ready. Type commands above...';
        }
    } else {
        element.textContent = 
            elementId === 'dataOutput' ? 'Ready for data operations...' :
            'Click a system info button to see details...';
    }
}

// Format JSON output
function formatJSON(obj) {
    return JSON.stringify(obj, null, 2)
        .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
        .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
        .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
        .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');
}

// Data storage functions
async function storeData() {
    const key = document.getElementById('dataKey').value;
    const value = document.getElementById('dataValue').value;
    
    if (!key) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Error: Please enter a key</span>';
        return;
    }
    
    try {
        // Send value as string - backend will handle JSON parsing
        const result = await safeFetchJSON('/api/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: key, value: value })
        });
        document.getElementById('dataOutput').innerHTML = formatJSON(result);
    } catch (error) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Error: ' + error.message + '</span>';
    }
}

async function getAllData() {
    try {
        const result = await safeFetchJSON('/api/data');
        document.getElementById('dataOutput').innerHTML = formatJSON(result);
    } catch (error) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Error: ' + error.message + '</span>';
    }
}

async function getData() {
    const key = document.getElementById('dataKey').value;
    if (!key) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Please enter a key</span>';
        return;
    }
    
    try {
        const result = await safeFetchJSON(`/api/data/${key}`);
        // Use value_string for display (formatted string)
        if (result.value_string) {
            document.getElementById('dataValue').value = result.value_string;
        } else {
            document.getElementById('dataValue').value = JSON.stringify(result.value, null, 2);
        }
        document.getElementById('dataOutput').innerHTML = formatJSON(result);
    } catch (error) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Error: ' + error.message + '</span>';
    }
}

async function deleteData() {
    const key = document.getElementById('dataKey').value;
    if (!key) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Please enter a key to delete</span>';
        return;
    }
    
    if (!confirm(`Are you sure you want to delete "${key}"?`)) {
        return;
    }
    
    try {
        const result = await safeFetchJSON(`/api/data/${key}`, { method: 'DELETE' });
        document.getElementById('dataOutput').innerHTML = formatJSON(result);
        if (result.success) {
            document.getElementById('dataValue').value = '';
        }
    } catch (error) {
        document.getElementById('dataOutput').innerHTML = '<span style="color: #ff6b35;">Error: ' + error.message + '</span>';
    }
}

// Interactive command handling
let currentCommandSession = null;
let currentProgramSession = null;

function handleInteractiveEnter(event) {
    if (event.key === 'Enter') {
        sendInteractiveResponse();
    }
}

function handleProgramInteractiveEnter(event) {
    if (event.key === 'Enter') {
        sendProgramInteractiveResponse();
    }
}

function sendQuickResponse(response) {
    document.getElementById('interactiveInput').value = response;
    sendInteractiveResponse();
}

async function sendInteractiveResponse() {
    const response = document.getElementById('interactiveInput').value;
    
    if (!currentCommandSession) {
        document.getElementById('commandOutput').innerHTML += '<br><span style="color: #ff6b35;">No active command session</span>';
        return;
    }
    
    try {
        document.getElementById('commandOutput').innerHTML += `<br><span style="color: #007acc;">> ${response}</span>`;
        document.getElementById('interactiveInput').value = '';
        
        const data = await safeFetchJSON('/api/execute/interactive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentCommandSession,
                response: response
            })
        });
        
        if (data.success) {
            if (data.output) {
                document.getElementById('commandOutput').innerHTML += `<br><span style="color: #00ff00;">${data.output}</span>`;
            }
            
            if (data.completed) {
                // Command finished
                document.getElementById('commandOutput').innerHTML += `<br><span style="color: #888;">Exit code: ${data.return_code}</span>`;
                document.getElementById('interactiveSection').style.display = 'none';
                currentCommandSession = null;
            } else if (data.waiting_for_input) {
                // Still waiting for more input
                document.getElementById('interactiveSection').style.display = 'block';
            }
        } else {
            document.getElementById('commandOutput').innerHTML += `<br><span style="color: #ff6b35;">Error: ${data.error}</span>`;
            document.getElementById('interactiveSection').style.display = 'none';
            currentCommandSession = null;
        }
        
    } catch (error) {
        document.getElementById('commandOutput').innerHTML += `<br><span style="color: #ff6b35;">Network Error: ${error.message}</span>`;
        document.getElementById('interactiveSection').style.display = 'none';
        currentCommandSession = null;
    }
}

async function sendProgramInteractiveResponse() {
    const inputElem = document.getElementById('programInteractiveInput');
    const outputDiv = document.getElementById('programExecutionOutput');
    const response = inputElem.value;

    if (!currentProgramSession) {
        outputDiv.innerHTML += '<br><span style="color: #ff6b35;">No active program session</span>';
        return;
    }

    try {
        outputDiv.innerHTML += `<br><span style="color: #007acc;">> ${response}</span>`;
        inputElem.value = '';

        const data = await safeFetchJSON('/api/execute/interactive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: currentProgramSession,
                response: response
            })
        });

        if (data.success) {
            if (data.output) {
                outputDiv.innerHTML += `<br><span style="color: #00ff00;">${data.output}</span>`;
            }

            if (data.completed) {
                outputDiv.innerHTML += `<br><span style="color: #888;">Exit code: ${data.return_code}</span>`;
                document.getElementById('programInteractiveSection').style.display = 'none';
                currentProgramSession = null;
            }
        } else {
            outputDiv.innerHTML += `<br><span style="color: #ff6b35;">Error: ${data.error}</span>`;
            document.getElementById('programInteractiveSection').style.display = 'none';
            currentProgramSession = null;
        }
    } catch (error) {
        outputDiv.innerHTML += `<br><span style="color: #ff6b35;">Network Error: ${error.message}</span>`;
        document.getElementById('programInteractiveSection').style.display = 'none';
        currentProgramSession = null;
    }
}


// Command execution
async function executeCommand() {
    const command = document.getElementById('command').value;
    const commandType = document.getElementById('commandType').value;
    const sudoPassword = document.getElementById('sudoPassword').value;
    const persistentCheckbox = document.getElementById('persistentTerminal');
    const outputDiv = document.getElementById('commandOutput');
    
    if (!command) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please enter a command</span>';
        return;
    }
    
    // Check if persistent terminal is enabled
    if (persistentCheckbox && persistentCheckbox.checked && persistentTerminalSession) {
        // Use persistent terminal session and accumulate history
        const currentOutput = outputDiv.innerHTML;
        const isInitialMessage = currentOutput.includes('Persistent terminal session created') || 
                                 currentOutput.includes('Terminal ready') ||
                                 currentOutput.includes('Command history cleared');
        
        // Add new command to history (unless it's the initial message)
        let historyOutput = isInitialMessage ? '' : currentOutput + '\n<span style="color: #444;">─────────────────────────────────────────────────────────────</span>\n';
        historyOutput += `<span style="color: #007acc;">${currentWorkingDirectory || '~'}$ ${command}</span>\n<span style="color: #ffff00;">Executing...</span>`;
        outputDiv.innerHTML = historyOutput;
        
        // Scroll to bottom
        outputDiv.scrollTop = outputDiv.scrollHeight;
        
        try {
            const result = await executeInPersistentTerminal(command);
            
            // Update the last command with results
            historyOutput = historyOutput.replace('<span style="color: #ffff00;">Executing...</span>', '');
            
            if (result.success) {
                if (result.output) {
                    historyOutput += `<span style="color: #00ff00;">${result.output}</span>\n`;
                }
                historyOutput += `<span style="color: #888;">[${result.cwd || currentWorkingDirectory}]</span>`;
            } else {
                historyOutput += `<span style="color: #ff6b35;">Error: ${result.error}</span>`;
            }
            
            outputDiv.innerHTML = historyOutput;
            
            // Scroll to bottom after update
            outputDiv.scrollTop = outputDiv.scrollHeight;
            
            // Clear command input
            document.getElementById('command').value = '';
            return;
        } catch (error) {
            historyOutput = historyOutput.replace('<span style="color: #ffff00;">Executing...</span>', '');
            historyOutput += `<span style="color: #ff6b35;">Error: ${error.message}</span>`;
            outputDiv.innerHTML = historyOutput;
            outputDiv.scrollTop = outputDiv.scrollHeight;
            return;
        }
    }
    
    // Check if sudo is selected but no password provided
    if (commandType === 'sudo' && !sudoPassword) {
        document.getElementById('commandOutput').innerHTML = '<span style="color: #ff6b35;">Please enter sudo password for privileged commands</span>';
        return;
    }
    
    let fullCommand = command;
    let requestData = { command: fullCommand };
    
    // Add password for sudo commands
    if (commandType === 'sudo') {
        requestData.sudo_password = sudoPassword;
    }
    
    // Add interactive support flag (check if checkbox is enabled)
    const interactiveModeCheckbox = document.getElementById('interactiveMode');
    requestData.interactive = interactiveModeCheckbox ? interactiveModeCheckbox.checked : false;
    
    document.getElementById('commandOutput').innerHTML = `<span style="color: #007acc;">$ ${commandType === 'sudo' ? 'sudo ' : ''}${command}</span>\n<span style="color: #ffff00;">Executing...</span>`;
    
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        // Check if response is OK
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Check if response is JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Expected JSON but got: ${text.substring(0, 100)}`);
        }
        
        const result = await response.json();
        
        let output = `<span style="color: #007acc;">$ ${commandType === 'sudo' ? 'sudo ' : ''}${command}</span>\n`;
        if (result.success) {
            if (result.stdout) output += `<span style="color: #00ff00;">${result.stdout}</span>`;
            if (result.stderr) output += `<span style="color: #ff6b35;">${result.stderr}</span>`;
            
            // Handle interactive commands
            if (result.waiting_for_input && result.session_id) {
                currentCommandSession = result.session_id;
                document.getElementById('interactiveSection').style.display = 'block';
                document.getElementById('interactiveInput').focus();
                output += `\n<span style="color: #ffff00;">⏳ Waiting for input...</span>`;
            } else {
                output += `\n<span style="color: #888;">Exit code: ${result.return_code}</span>`;
                document.getElementById('interactiveSection').style.display = 'none';
                currentCommandSession = null;
            }
        } else {
            output += `<span style="color: #ff6b35;">Error: ${result.error}</span>`;
            document.getElementById('interactiveSection').style.display = 'none';
            currentCommandSession = null;
        }
        
        document.getElementById('commandOutput').innerHTML = output;
        
        // Clear password field after execution
        if (commandType === 'sudo') {
            document.getElementById('sudoPassword').value = '';
        }
        
        // Also show in system output if it's a system info command
        if (command.includes('uname') || command.includes('ps') || command.includes('free') || 
            command.includes('uptime') || command.includes('ip addr') || command.includes('lscpu')) {
            document.getElementById('systemOutput').innerHTML = output;
        }
        
    } catch (error) {
        document.getElementById('commandOutput').innerHTML = 
            `<span style="color: #007acc;">$ ${commandType === 'sudo' ? 'sudo ' : ''}${command}</span>\n<span style="color: #ff6b35;">Network Error: ${error.message}</span>`;
        
        // Clear password field on error
        if (commandType === 'sudo') {
            document.getElementById('sudoPassword').value = '';
        }
    }
}

// Check server health on load
async function checkServerHealth() {
    try {
        const response = await fetch('/health');
        if (response.ok) {
            document.getElementById('serverStatus').innerHTML = '🟢 Server Connected';
        } else {
            document.getElementById('serverStatus').innerHTML = '🟡 Server Issues';
        }
    } catch (error) {
        document.getElementById('serverStatus').innerHTML = '🔴 Server Disconnected';
    }
}

// Get machine info for command terminal
async function getMachineInfo() {
    try {
        const result = await safeFetchJSON('/api/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: 'whoami && hostname && pwd' })
        });
        
        if (result.success && result.stdout) {
            const lines = result.stdout.trim().split('\n');
            const user = lines[0] || 'unknown';
            const host = lines[1] || 'unknown';
            const dir = lines[2] || 'unknown';
            document.getElementById('machineInfo').innerHTML = `<span style="color: #00ff00;">${user}@${host}</span> : ${dir}`;
        } else {
            document.getElementById('machineInfo').textContent = 'localhost';
        }
    } catch (error) {
        document.getElementById('machineInfo').textContent = 'localhost';
    }
}

// Program management functions
document.getElementById('programUploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    await uploadProgram();
});

document.getElementById('multipleUploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    await uploadMultiplePrograms();
});

// Show/hide sudo password field for program execution
document.getElementById('programExecutionType').addEventListener('change', function() {
    const passwordDiv = document.getElementById('programSudoPassword');
    const passwordInput = document.getElementById('programSudoPasswordInput');
    
    if (this.value === 'sudo') {
        passwordDiv.style.display = 'block';
        passwordInput.required = true;
    } else {
        passwordDiv.style.display = 'none';
        passwordInput.required = false;
        passwordInput.value = '';
    }
});

function toggleUploadType() {
    const uploadType = document.querySelector('input[name="uploadType"]:checked').value;
    const singleForm = document.getElementById('programUploadForm');
    const multipleForm = document.getElementById('multipleUploadForm');
    const outputDiv = document.getElementById('programUploadOutput');
    
    if (uploadType === 'single') {
        singleForm.style.display = 'block';
        multipleForm.style.display = 'none';
        outputDiv.innerHTML = 'Select a program file to upload...';
    } else {
        singleForm.style.display = 'none';
        multipleForm.style.display = 'block';
        outputDiv.innerHTML = 'Select multiple files or a folder to upload as a project...';
    }
}

function selectFolder() {
    const folderInput = document.getElementById('multipleFiles');
    folderInput.click();
}

function selectMultipleFiles() {
    const filesInput = document.getElementById('multipleFilesRegular');
    filesInput.click();
}

document.getElementById('multipleFiles').addEventListener('change', function(e) {
    handleFileSelection(e.target.files, 'folder');
});

document.getElementById('multipleFilesRegular').addEventListener('change', function(e) {
    handleFileSelection(e.target.files, 'files');
});

function handleFileSelection(files, type) {
    const fileListDiv = document.getElementById('fileList');
    const uploadBtn = document.getElementById('uploadMultipleBtn');
    const outputDiv = document.getElementById('programUploadOutput');
    
    if (files.length === 0) {
        fileListDiv.style.display = 'none';
        uploadBtn.disabled = true;
        return;
    }
    
    let fileListHTML = `<strong>Selected ${files.length} file(s):</strong><br>`;
    Array.from(files).forEach(file => {
        const size = (file.size / 1024).toFixed(1);
        fileListHTML += `📄 ${file.name} (${size} KB)<br>`;
    });
    
    fileListDiv.innerHTML = fileListHTML;
    fileListDiv.style.display = 'block';
    uploadBtn.disabled = false;
    
    outputDiv.innerHTML = `Ready to upload ${files.length} file(s) as a project...`;
}

async function uploadProgram() {
    const fileInput = document.getElementById('programFile');
    const descriptionInput = document.getElementById('programDescription');
    const outputDiv = document.getElementById('programUploadOutput');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please select a program file</span>';
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    formData.append('description', descriptionInput.value || '');
    
    outputDiv.innerHTML = '<span style="color: #ffff00;">Uploading program...</span>';
    
    try {
        const response = await fetch('/api/programs/upload', {
            method: 'POST',
            body: formData
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            outputDiv.innerHTML = 
                `<span style="color: #00ff00;">✅ ${result.program.filename} uploaded successfully!</span><br>
                Type: ${result.program.program_type}<br>
                Size: ${result.program.size} bytes`;
            
            // Clear form and refresh lists
            fileInput.value = '';
            descriptionInput.value = '';
            loadProgramList();
        } else {
            outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Upload failed: ' + (result.error || 'Unknown error') + '</span>';
        }
    } catch (error) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Error: ' + error.message + '</span>';
    }
}

async function uploadMultiplePrograms() {
    const outputDiv = document.getElementById('programUploadOutput');
    const projectNameInput = document.getElementById('projectName');
    const projectDescriptionInput = document.getElementById('projectDescription');
    
    // Get files from either folder or multiple file input
    const folderFiles = document.getElementById('multipleFiles').files;
    const regularFiles = document.getElementById('multipleFilesRegular').files;
    const files = folderFiles.length > 0 ? folderFiles : regularFiles;
    
    if (!files || files.length === 0) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please select files to upload</span>';
        return;
    }
    
    const formData = new FormData();
    
    // Add all files
    Array.from(files).forEach(file => {
        formData.append('files[]', file);
        
        // For folder uploads, preserve the relative path
        if (folderFiles.length > 0 && file.webkitRelativePath) {
            formData.append(`path_${file.name}`, file.webkitRelativePath);
        }
    });
    
    formData.append('project_name', projectNameInput.value || '');
    formData.append('description', projectDescriptionInput.value || '');
    
    outputDiv.innerHTML = '<span style="color: #ffff00;">Uploading project...</span>';
    
    try {
        const response = await fetch('/api/programs/upload-multiple', {
            method: 'POST',
            body: formData
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            if (result.program) {
                // Single file result
                outputDiv.innerHTML = 
                    `<span style="color: #00ff00;">✅ ${result.program.filename} uploaded successfully!</span><br>
                    Type: ${result.program.program_type}<br>
                    Size: ${result.program.size} bytes`;
            } else if (result.project) {
                // Project result
                outputDiv.innerHTML = 
                    `<span style="color: #00ff00;">✅ Project "${result.project.project_name}" uploaded successfully!</span><br>
                    Files: ${result.project.file_count}<br>
                    Total Size: ${result.project.total_size} bytes`;
            }
            
            // Clear form and refresh lists
            document.getElementById('multipleFiles').value = '';
            document.getElementById('multipleFilesRegular').value = '';
            document.getElementById('fileList').style.display = 'none';
            document.getElementById('uploadMultipleBtn').disabled = true;
            projectNameInput.value = '';
            projectDescriptionInput.value = '';
            loadProgramList();
        } else {
            outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Upload failed: ' + (result.error || 'Unknown error') + '</span>';
        }
    } catch (error) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Error: ' + error.message + '</span>';
    }
}

async function loadProgramList() {
    const listDiv = document.getElementById('programList');
    const selectDiv = document.getElementById('selectedProgram');
    
    try {
        const result = await safeFetchJSON('/api/programs/list');
        
        if (result.success) {
            updateProgramList(result.programs);
            updateProgramSelector(result.programs);
        } else {
            listDiv.innerHTML = '<div style="color: #ff6b35;">Error loading programs: ' + (result.error || 'Unknown error') + '</div>';
        }
    } catch (error) {
        listDiv.innerHTML = '<div style="color: #ff6b35;">Error: ' + error.message + '</div>';
    }
}

function updateProgramList(programs) {
    const listDiv = document.getElementById('programList');
    
    if (programs.length === 0) {
        listDiv.innerHTML = '<div style="text-align: center; color: #888; padding: 20px;">📝 No programs uploaded yet<br><br>Upload a program using the form above to get started!</div>';
        return;
    }
    
    let totalSize = 0;
    let itemCount = 0;
    programs.forEach(p => {
        totalSize += p.total_size || p.size || 0;
        itemCount += p.type === 'project' ? (p.file_count || 1) : 1;
    });
    
    let html = `<div style="font-size: 12px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; padding: 8px; background: #2d2d2d; border-radius: 4px;">
            <span style="color: #007acc; font-weight: bold;">📊 ${programs.length} item${programs.length !== 1 ? 's' : ''} stored (${itemCount} files)</span>
            <span style="color: #888;">Total size: ${totalSize} bytes</span>
        </div>`;
    
    programs.forEach((program, index) => {
        const uploadDate = new Date(program.upload_time).toLocaleString();
        const lastExecuted = program.last_executed ? 
            new Date(program.last_executed).toLocaleString() : 'Never executed';
        
        const isProject = program.type === 'project';
        const displayName = isProject ? (program.project_name || program.project_id) : program.filename;
        const identifier = isProject ? program.project_id : program.program_id;
        
        // Color coding based on program type or project
        const typeColors = {
            'python': '#007acc',
            'shell': '#00ff00',
            'javascript': '#ffff00',
            'perl': '#ff6b35',
            'ruby': '#dc3545',
            'project': '#9370db',
            'unknown': '#888'
        };
        const typeColor = isProject ? typeColors['project'] : (typeColors[program.program_type] || typeColors['unknown']);
        const typeLabel = isProject ? 'PROJECT' : (program.program_type || 'unknown').toUpperCase();
        
        html += `
            <div style="background: #1a1a1a; padding: 10px; margin: 5px 0; border-radius: 4px; border-left: 3px solid ${typeColor};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <input type="checkbox" class="program-checkbox" value="${identifier}" 
                               onchange="toggleProgramSelection('${identifier}', this)"
                               style="cursor: pointer;">
                        <strong style="color: ${typeColor};">${isProject ? '📁' : '📄'} ${displayName}</strong>
                        <span style="background: ${typeColor}; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 10px; font-weight: bold;">
                            ${typeLabel}
                        </span>
                        ${isProject ? `<span style="color: #888; font-size: 10px;">(${program.file_count} files)</span>` : ''}
                    </div>
                    <div style="display: flex; gap: 5px;">
                        ${isProject ? `<button onclick="showProjectFiles('${identifier}')" 
                                        style="background: #007acc; color: white; border: none; padding: 4px 8px; 
                                               border-radius: 3px; cursor: pointer; font-size: 11px;">
                                        📂 Files
                                      </button>` : ''}
                        <button onclick="deleteProgram('${identifier}')" 
                                style="background: #dc3545; color: white; border: none; padding: 4px 10px; 
                                       border-radius: 3px; cursor: pointer; font-size: 11px; font-weight: bold;
                                       transition: background 0.3s;"
                                onmouseover="this.style.background='#c82333'"
                                onmouseout="this.style.background='#dc3545'">
                            🗑️ Delete
                        </button>
                    </div>
                </div>
                <div style="color: #888; font-size: 11px; line-height: 1.4;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <div>📊 <strong>Stats:</strong> ${program.execution_count || 0} execution${(program.execution_count || 0) !== 1 ? 's' : ''}</div>
                        <div>📏 <strong>Size:</strong> ${isProject ? program.total_size : program.size || 0} bytes</div>
                        <div>📅 <strong>Uploaded:</strong> ${uploadDate}</div>
                        <div>⚡ <strong>Last run:</strong> ${lastExecuted}</div>
                    </div>
                    ${program.description ? `<div style="margin-top: 6px; color: #bbb;"><strong>Description:</strong> ${program.description}</div>` : ''}
                </div>
            </div>`;
    });
    html += '</div>';
    
    listDiv.innerHTML = html;
    
    // Clear selection state when list is updated
    selectedPrograms.clear();
    updateSelectedUI();
}

function updateProgramSelector(programs) {
    const selectDiv = document.getElementById('selectedProgram');
    
    // Clear existing options except the first
    selectDiv.innerHTML = '<option value="">Select a program to execute...</option>';
    
    // Add program options
    programs.forEach(program => {
        const option = document.createElement('option');
        const isProject = program.type === 'project';
        const displayName = isProject ? (program.project_name || program.project_id) : program.filename;
        const identifier = isProject ? program.project_id : program.program_id;
        const typeLabel = isProject ? 'PROJECT' : program.program_type;
        
        option.value = identifier;
        option.textContent = `${isProject ? '📁' : '📄'} ${displayName} (${typeLabel})`;
        option.dataset.type = program.type || 'single';
        selectDiv.appendChild(option);
    });
}

function handleProgramSelection() {
    const programSelect = document.getElementById('selectedProgram');
    const selectedOption = programSelect.options[programSelect.selectedIndex];
    const projectTerminalSection = document.getElementById('projectTerminalSection');
    const traditionalArgsSection = document.getElementById('traditionalArgsSection');
    
    if (selectedOption && selectedOption.dataset.type === 'project') {
        // Show project terminal section, hide traditional args
        projectTerminalSection.style.display = 'block';
        traditionalArgsSection.style.display = 'none';
    } else {
        // Show traditional args, hide project terminal
        projectTerminalSection.style.display = 'none';
        traditionalArgsSection.style.display = 'block';
    }
}

function handleProjectTerminalEnter(event) {
    if (event.key === 'Enter') {
        executeProjectTerminal();
    }
}

async function executeProjectTerminal() {
    const programSelect = document.getElementById('selectedProgram');
    const terminalCommand = document.getElementById('projectTerminalCommand');
    const executionType = document.getElementById('programExecutionType');
    const passwordInput = document.getElementById('programSudoPasswordInput');
    const interactiveCheckbox = document.getElementById('programInteractive');
    const outputDiv = document.getElementById('programExecutionOutput');
    const interactiveSection = document.getElementById('programInteractiveSection');
    
    // Reset interactive state
    interactiveSection.style.display = 'none';
    currentProgramSession = null;
    
    const projectId = programSelect.value;
    const command = terminalCommand.value.trim();
    
    if (!projectId) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please select a project</span>';
        return;
    }
    
    if (!command) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please enter a command</span>';
        return;
    }
    
    const useSudo = executionType.value === 'sudo';
    const sudoPassword = useSudo ? passwordInput.value : '';
    
    if (useSudo && !sudoPassword) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Password required for sudo execution</span>';
        return;
    }
    
    outputDiv.innerHTML = '<span style="color: #ffff00;">Executing command in project directory...</span>';
    
    try {
        const requestData = {
            command: command,
            use_sudo: useSudo,
            sudo_password: sudoPassword,
            interactive: interactiveCheckbox.checked
        };
        
        const result = await safeFetchJSON(`/api/programs/execute-terminal/${projectId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (result.success) {
            const exitStyle = result.return_code === 0 ? 'color: #00ff00;' : 'color: #ff6b35;';
            let outputHTML = 
                `<div style="background: #1a1a1a; padding: 10px; border-radius: 4px; margin: 5px 0;">
                    <div style="margin-bottom: 5px;">
                        <strong>Command:</strong> ${result.command}<br>
                        <strong>Working Dir:</strong> ${result.cwd || 'N/A'}<br>`;

            if (result.completed) {
                 outputHTML += `<strong style="${exitStyle}">Exit Code:</strong> ${result.return_code}`;
            }
            
            outputHTML += `</div>
                    <div style="background: #000; padding: 8px; border-radius: 3px; font-family: monospace; 
                                white-space: pre-wrap; max-height: 300px; overflow-y: auto;">
${result.stdout || result.output || '(No output)'}
                    </div>
                </div>`;
            
            outputDiv.innerHTML = outputHTML;

            if (result.waiting_for_input && result.session_id) {
                currentProgramSession = result.session_id;
                interactiveSection.style.display = 'block';
                document.getElementById('programInteractiveInput').focus();
                outputDiv.innerHTML += `<span style="color: #ffff00;">⏳ Waiting for input...</span>`;
            } else {
                interactiveSection.style.display = 'none';
                currentProgramSession = null;
            }
            
            // Clear password and command after execution
            if (useSudo) {
                passwordInput.value = '';
            }
            terminalCommand.value = '';
            
        } else {
            outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Execution failed: ' + (result.error || 'Unknown error') + '</span>';
        }
    } catch (error) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Error: ' + error.message + '</span>';
    }
}

async function executeSelectedProgram(specificFile = null) {
    const programSelect = document.getElementById('selectedProgram');
    const argsInput = document.getElementById('programArgs');
    const executionType = document.getElementById('programExecutionType');
    const passwordInput = document.getElementById('programSudoPasswordInput');
    const interactiveCheckbox = document.getElementById('programInteractive');
    const outputDiv = document.getElementById('programExecutionOutput');
    const interactiveSection = document.getElementById('programInteractiveSection');

    // Reset interactive state
    interactiveSection.style.display = 'none';
    currentProgramSession = null;
    
    const filename = programSelect.value;
    if (!filename) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please select a program to execute</span>';
        return;
    }
    
    // Check if this is a project - if so, show file selector first
    if (!specificFile) {
        try {
            const infoData = await safeFetchJSON(`/api/programs/info/${filename}`);
            
            if (infoData.success && infoData.program.type === 'project') {
                // Show file selection modal for projects
                const files = infoData.program.files || [];
                const supported = ['python', 'shell', 'javascript', 'perl', 'ruby'];
                const candidates = files.filter(f => 
                    supported.includes(f.program_type) || f.is_executable
                );
                
                if (candidates.length === 0) {
                    outputDiv.innerHTML = '<span style="color: #ff6b35;">No executable files found in project</span>';
                    return;
                }
                
                openFileSelectionModal(filename, candidates, (chosenFile) => {
                    executeSelectedProgram(chosenFile);
                });
                return;
            }
        } catch (e) {
            console.error('Error checking program type:', e);
        }
    }
    
    const useSudo = executionType.value === 'sudo';
    const sudoPassword = useSudo ? passwordInput.value : '';
    
    if (useSudo && !sudoPassword) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Password required for sudo execution</span>';
        return;
    }
    
    outputDiv.innerHTML = '<span style="color: #ffff00;">Executing program...</span>';
    
    try {
        const requestData = {
            args: argsInput.value ? argsInput.value.split(' ').filter(arg => arg.trim()) : [],
            use_sudo: useSudo,
            sudo_password: sudoPassword,
            interactive: interactiveCheckbox.checked
        };
        
        // If specificFile is provided, include it in the request
        if (specificFile) {
            requestData.specific_file = specificFile;
        }
        
        const result = await safeFetchJSON(`/api/programs/execute/${filename}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        if (result.success) {
            const exitStyle = result.return_code === 0 ? 'color: #00ff00;' : 'color: #ff6b35;';
            let outputHTML = 
                `<div style="background: #1a1a1a; padding: 10px; border-radius: 4px; margin: 5px 0;">
                    <div style="margin-bottom: 5px;">
                        <strong>Command:</strong> ${result.command}<br>
                        <strong>Type:</strong> ${result.program_type || 'N/A'}<br>`;

            if (result.completed) {
                 outputHTML += `<strong style="${exitStyle}">Exit Code:</strong> ${result.return_code}`;
            }
            
            outputHTML += `</div>
                    <div style="background: #000; padding: 8px; border-radius: 3px; font-family: monospace; 
                                white-space: pre-wrap; max-height: 300px; overflow-y: auto;">
${result.stdout || result.output || '(No output)'}
                    </div>
                </div>`;
            
            outputDiv.innerHTML = outputHTML;

            if (result.waiting_for_input && result.session_id) {
                currentProgramSession = result.session_id;
                interactiveSection.style.display = 'block';
                document.getElementById('programInteractiveInput').focus();
                outputDiv.innerHTML += `<span style="color: #ffff00;">⏳ Waiting for input...</span>`;
            } else {
                interactiveSection.style.display = 'none';
                currentProgramSession = null;
            }
            
            // Clear password after execution
            if (useSudo) {
                passwordInput.value = '';
            }
            
            // Refresh program list to update execution stats
            loadProgramList();
        } else {
            if (result.need_main_file && result.project_id) {
                // Ask user to choose a main file, then set it and retry
                openMainSelectionModal(result.project_id, result.candidates || [], async (chosenPath) => {
                    try {
                        const setJson = await safeFetchJSON(`/api/programs/project/${result.project_id}/set-main`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ relative_path: chosenPath })
                        });
                        if (!setJson.success) {
                            outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Failed to set main file: ' + (setJson.error || 'Unknown error') + '</span>';
                            return;
                        }
                        // Retry execution
                        executeSelectedProgram();
                    } catch (e) {
                        outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Error setting main file: ' + e.message + '</span>';
                    }
                });
            } else {
                outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Execution failed: ' + (result.error || 'Unknown error') + '</span>';
            }
        }
    } catch (error) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">❌ Error: ' + error.message + '</span>';
    }
}

function openMainSelectionModal(projectId, candidates, onConfirm) {
    // Build modal
    const modal = document.createElement('div');
    modal.id = 'mainSelectModal';
    modal.style.cssText = 'position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); z-index: 1000; display:flex; justify-content:center; align-items:center;';
    const inner = document.createElement('div');
    inner.style.cssText = 'background:#1a1a1a; border:2px solid #007acc; border-radius:8px; max-width: 700px; width:90%; max-height:80%; overflow:auto; padding:16px;';
    inner.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="color:#00c7ff; margin:0;">Select Main File for Project</h3>
            <button onclick="closeModal()" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">✕</button>
        </div>
        <div style="color:#bbb; font-size:12px; margin-bottom:8px;">Choose the file that should be executed when running this project.</div>
        <div id="mainFileList"></div>
        <div style="margin-top:12px; display:flex; justify-content:flex-end; gap:8px;">
            <button id="confirmMainBtn" disabled>✅ Set Main & Run</button>
        </div>
    `;
    modal.appendChild(inner);
    document.body.appendChild(modal);

    const listDiv = inner.querySelector('#mainFileList');
    const confirmBtn = inner.querySelector('#confirmMainBtn');
    let selected = null;
    
    if (!candidates || candidates.length === 0) {
        listDiv.innerHTML = '<div style="color:#ff6b35;">No executable candidates found. You can still set any project file as main from the Files view.</div>';
    } else {
        const supportedBadges = (t)=> t ? `<span style="background:#444; color:#fff; padding:1px 6px; border-radius:10px; font-size:10px; margin-left:6px;">${t.toUpperCase()}</span>` : '';
        listDiv.innerHTML = candidates.map((c,i)=>`
            <label style="display:flex; align-items:center; gap:8px; padding:6px 8px; border:1px solid #333; border-radius:6px; margin:6px 0;">
                <input type="radio" name="mainChoice" value="${c.relative_path}" ${i===0?'checked':''} />
                <span class="mono" style="flex:1;">${c.relative_path}</span>
                ${supportedBadges(c.program_type)}
                <span style="color:#888; font-size:11px;">${c.size || 0} bytes</span>
            </label>
        `).join('');
        selected = candidates[0].relative_path;
        confirmBtn.disabled = false;
    }

    inner.querySelectorAll('input[name="mainChoice"]').forEach(inp=>{
        inp.addEventListener('change', ()=>{ selected = inp.value; confirmBtn.disabled = !selected; });
    });

    confirmBtn.addEventListener('click', ()=>{
        if (selected) {
            document.body.removeChild(modal);
            onConfirm && onConfirm(selected);
        }
    });
}

function openFileSelectionModal(projectId, candidates, onConfirm) {
    // Build modal for selecting which file to execute (not setting main file)
    const modal = document.createElement('div');
    modal.id = 'fileSelectModal';
    modal.style.cssText = 'position: fixed; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.8); z-index: 1000; display:flex; justify-content:center; align-items:center;';
    const inner = document.createElement('div');
    inner.style.cssText = 'background:#1a1a1a; border:2px solid #007acc; border-radius:8px; max-width: 700px; width:90%; max-height:80%; overflow:auto; padding:16px;';
    inner.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <h3 style="color:#00c7ff; margin:0;">⚡ Select File to Execute</h3>
            <button onclick="closeModal()" style="background:#dc3545; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">✕</button>
        </div>
        <div style="color:#bbb; font-size:12px; margin-bottom:8px;">Choose which file from the project to run this time:</div>
        <div id="fileExecuteList"></div>
        <div style="margin-top:12px; display:flex; justify-content:flex-end; gap:8px;">
            <button onclick="closeModal()" style="background:#6c757d; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">Cancel</button>
            <button id="confirmFileBtn" style="background:#28a745; color:white; border:none; padding:8px 16px; border-radius:4px; cursor:pointer;">▶️ Execute</button>
        </div>
    `;
    modal.appendChild(inner);
    document.body.appendChild(modal);

    const listDiv = inner.querySelector('#fileExecuteList');
    const confirmBtn = inner.querySelector('#confirmFileBtn');
    let selected = candidates[0]?.relative_path || null;
    
    const supportedBadges = (t)=> t ? `<span style="background:#444; color:#fff; padding:1px 6px; border-radius:10px; font-size:10px; margin-left:6px;">${t.toUpperCase()}</span>` : '';
    listDiv.innerHTML = candidates.map((c,i)=>`
        <label style="display:flex; align-items:center; gap:8px; padding:8px 10px; border:1px solid #333; border-radius:6px; margin:6px 0; cursor:pointer; transition: all 0.2s;"
               onmouseover="this.style.background='#2a2a2a'; this.style.borderColor='#007acc';"
               onmouseout="this.style.background='transparent'; this.style.borderColor='#333';">
            <input type="radio" name="fileChoice" value="${c.relative_path}" ${i===0?'checked':''} />
            <span style="flex:1; font-family: 'Courier New', monospace; color:#00ff88;">${c.relative_path}</span>
            ${supportedBadges(c.program_type)}
            <span style="color:#888; font-size:11px;">${c.size || 0} bytes</span>
        </label>
    `).join('');

    inner.querySelectorAll('input[name="fileChoice"]').forEach(inp=>{
        inp.addEventListener('change', ()=>{ selected = inp.value; });
    });

    confirmBtn.addEventListener('click', ()=>{
        if (selected) {
            document.body.removeChild(modal);
            onConfirm && onConfirm(selected);
        }
    });
    
    // Close on Escape key
    const escHandler = (e) => {
        if (e.key === 'Escape') {
            if (document.getElementById('fileSelectModal')) {
                document.body.removeChild(modal);
                document.removeEventListener('keydown', escHandler);
            }
        }
    };
    document.addEventListener('keydown', escHandler);
}

async function deleteProgram(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?\n\nThis action cannot be undone.`)) {
        return;
    }
    
    try {
        const result = await safeFetchJSON(`/api/programs/delete/${filename}`, {
            method: 'DELETE'
        });
        
        if (result.success) {
            // Show success message briefly
            const listDiv = document.getElementById('programList');
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'color: #00ff00; text-align: center; padding: 10px; background: #1a1a1a; border-radius: 4px; margin: 5px 0;';
            successMsg.innerHTML = `✅ ${filename} deleted successfully`;
            listDiv.insertBefore(successMsg, listDiv.firstChild);
            
            // Remove success message after 3 seconds
            setTimeout(() => {
                if (successMsg.parentNode) {
                    successMsg.parentNode.removeChild(successMsg);
                }
            }, 3000);
            
            loadProgramList(); // Refresh the list
        } else {
            alert('Delete failed: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

async function showProjectFiles(projectId) {
    try {
        const result = await safeFetchJSON(`/api/programs/project/${projectId}/files`);
        
        if (result.success) {
            const project = result.project;
            const files = result.files;
            
            let modalHTML = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                            background: rgba(0,0,0,0.8); z-index: 1000; display: flex; 
                            justify-content: center; align-items: center;" onclick="closeModal()">
                    <div style="background: #1a1a1a; border-radius: 8px; padding: 20px; 
                                max-width: 80%; max-height: 80%; overflow-y: auto; border: 2px solid #007acc;"
                         onclick="event.stopPropagation()">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h3 style="color: #007acc; margin: 0;">📁 ${project.project_name || project.project_id}</h3>
                            <button onclick="closeModal()" style="background: #dc3545; color: white; border: none; 
                                                                   padding: 5px 10px; border-radius: 3px; cursor: pointer;">✕</button>
                        </div>
                        <div style="color: #888; margin-bottom: 15px; font-size: 12px;">
                            ${files.length} files • ${project.total_size} bytes • Uploaded: ${new Date(project.upload_time).toLocaleString()}
                            ${project.description ? `<br>Description: ${project.description}` : ''}
                        </div>
                        <div style="max-height: 400px; overflow-y: auto;">`;
            
            files.forEach(file => {
                const typeColors = {
                    'python': '#007acc',
                    'shell': '#00ff00',
                    'javascript': '#ffff00',
                    'perl': '#ff6b35',
                    'ruby': '#dc3545',
                    'unknown': '#888'
                };
                const typeColor = typeColors[file.program_type] || typeColors['unknown'];
                const isExecutable = file.is_executable;
                
                modalHTML += `
                    <div style="background: #2d2d2d; padding: 10px; margin: 5px 0; border-radius: 4px; 
                                border-left: 3px solid ${typeColor};">
                        <div style="display: flex; justify-content: between; align-items: center;">
                            <div style="flex: 1;">
                                <strong style="color: ${typeColor};">
                                    ${isExecutable ? '⚡' : '📄'} ${file.relative_path}
                                </strong>
                                <span style="background: ${typeColor}; color: #000; padding: 1px 4px; 
                                             border-radius: 2px; font-size: 9px; font-weight: bold; margin-left: 8px;">
                                    ${file.program_type.toUpperCase()}
                                </span>
                            </div>
                            <div style="color: #888; font-size: 11px; text-align: right;">
                                ${file.size} bytes<br>
                                ${isExecutable ? 'Executable' : 'Data file'}
                            </div>
                        </div>
                    </div>`;
            });
            
            modalHTML += `
                        </div>
                    </div>
                </div>`;
            
            // Create and show modal
            const modal = document.createElement('div');
            modal.innerHTML = modalHTML;
            modal.id = 'projectModal';
            document.body.appendChild(modal);
        } else {
            alert('Failed to load project files: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function closeModal() {
    const ids = ['projectModal','mainSelectModal', 'fileSelectModal'];
    ids.forEach(id => {
        const m = document.getElementById(id);
        if (m) {
            document.body.removeChild(m);
        }
    });
}

async function deleteAllPrograms() {
    // Get current program list to check if there are any programs
    const result = await safeFetchJSON('/api/programs/list');
    
    if (!result.success) {
        alert('Error checking program list: ' + (result.error || 'Unknown error'));
        return;
    }
    
    const programs = result.programs;
    if (programs.length === 0) {
        alert('No programs to delete.');
        return;
    }
    
    const confirmMessage = `⚠️ WARNING: This will delete ALL ${programs.length} programs!\n\nPrograms to be deleted:\n${programs.map(p => `• ${p.filename} (${p.program_type})`).join('\n')}\n\nThis action cannot be undone. Are you absolutely sure?`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    // Double confirmation for safety
    if (!confirm('Last chance! This will permanently delete ALL programs. Continue?')) {
        return;
    }
    
    const listDiv = document.getElementById('programList');
    listDiv.innerHTML = '<div style="color: #ffff00; text-align: center; padding: 20px;">🗑️ Deleting all programs...</div>';
    
    let deletedCount = 0;
    let errors = [];
    
    // Delete each program
    for (const program of programs) {
        try {
            const deleteResult = await safeFetchJSON(`/api/programs/delete/${program.filename}`, {
                method: 'DELETE'
            });
            
            if (deleteResult.success) {
                deletedCount++;
            } else {
                errors.push(`${program.filename}: ${deleteResult.error || 'Unknown error'}`);
            }
        } catch (error) {
            errors.push(`${program.filename}: ${error.message}`);
        }
    }
    
    // Show results
    let resultMessage = `✅ Deleted ${deletedCount} of ${programs.length} programs`;
    if (errors.length > 0) {
        resultMessage += `\n\n❌ Errors:\n${errors.join('\n')}`;
    }
    
    alert(resultMessage);
    loadProgramList(); // Refresh the list
}

// Track selected programs
let selectedPrograms = new Set();

function toggleProgramSelection(filename, checkbox) {
    if (checkbox.checked) {
        selectedPrograms.add(filename);
    } else {
        selectedPrograms.delete(filename);
    }
    updateSelectedUI();
}

function toggleSelectAll() {
    const checkboxes = document.querySelectorAll('.program-checkbox');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const allSelected = selectedPrograms.size === checkboxes.length;
    
    if (allSelected) {
        // Unselect all
        checkboxes.forEach(cb => {
            cb.checked = false;
            selectedPrograms.delete(cb.value);
        });
        selectAllBtn.innerHTML = '☑️ Select All';
        selectAllBtn.style.background = '#007acc';
    } else {
        // Select all
        checkboxes.forEach(cb => {
            cb.checked = true;
            selectedPrograms.add(cb.value);
        });
        selectAllBtn.innerHTML = '◻️ Unselect All';
        selectAllBtn.style.background = '#ff6b35';
    }
    updateSelectedUI();
}

function updateSelectedUI() {
    const deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
    const selectAllBtn = document.getElementById('selectAllBtn');
    const count = selectedPrograms.size;
    
    if (count > 0) {
        deleteSelectedBtn.style.display = 'inline-block';
        deleteSelectedBtn.innerHTML = `🗑️ Delete Selected (${count})`;
    } else {
        deleteSelectedBtn.style.display = 'none';
    }
    
    // Update select all button
    const checkboxes = document.querySelectorAll('.program-checkbox');
    if (count === checkboxes.length && count > 0) {
        selectAllBtn.innerHTML = '◻️ Unselect All';
        selectAllBtn.style.background = '#ff6b35';
    } else {
        selectAllBtn.innerHTML = '☑️ Select All';
        selectAllBtn.style.background = '#007acc';
    }
}

async function deleteSelectedPrograms() {
    if (selectedPrograms.size === 0) {
        alert('No programs selected.');
        return;
    }
    
    const programsToDelete = Array.from(selectedPrograms);
    const confirmMessage = `Delete ${programsToDelete.length} selected program(s)?\n\n${programsToDelete.map(p => `• ${p}`).join('\n')}\n\nThis action cannot be undone.`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    const listDiv = document.getElementById('programList');
    listDiv.innerHTML = '<div style="color: #ffff00; text-align: center; padding: 20px;">🗑️ Deleting selected programs...</div>';
    
    let deletedCount = 0;
    let errors = [];
    
    for (const filename of programsToDelete) {
        try {
            const result = await safeFetchJSON(`/api/programs/delete/${filename}`, {
                method: 'DELETE'
            });
            
            if (result.success) {
                deletedCount++;
                selectedPrograms.delete(filename);
            } else {
                errors.push(`${filename}: ${result.error || 'Unknown error'}`);
            }
        } catch (error) {
            errors.push(`${filename}: ${error.message}`);
        }
    }
    
    let resultMessage = `✅ Deleted ${deletedCount} of ${programsToDelete.length} selected programs`;
    if (errors.length > 0) {
        resultMessage += `\n\n❌ Errors:\n${errors.join('\n')}`;
    }
    
    alert(resultMessage);
    selectedPrograms.clear();
    loadProgramList();
}

// Tunnel functions
async function startNgrok() {
    updateTunnelOutput('Starting ngrok tunnel...', 'warning');
    updateTunnelStatus('Starting...');
    
    try {
        const result = await safeFetchJSON('/api/ngrok/start', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Ngrok tunnel started! Checking for public URL...', 'success');
            setTimeout(checkAllTunnelStatus, 5000);
        } else {
            updateTunnelOutput('Failed to start ngrok: ' + (result.error || result.status), 'error');
            updateTunnelStatus('Error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
        updateTunnelStatus('Error');
    }
}

async function stopNgrok() {
    updateTunnelOutput('Stopping ngrok tunnel...', 'warning');
    
    try {
        const result = await safeFetchJSON('/api/ngrok/stop', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Ngrok tunnel stopped.', 'success');
            setTimeout(checkAllTunnelStatus, 1000);
        } else {
            updateTunnelOutput('Failed to stop ngrok: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
    }
}

async function startLocaltunnel() {
    updateTunnelOutput('Starting localtunnel...', 'warning');
    updateTunnelStatus('Starting...');
    
    try {
        const result = await safeFetchJSON('/api/localtunnel/start', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Localtunnel started! Checking for public URL...', 'success');
            setTimeout(checkAllTunnelStatus, 8000); // Localtunnel takes longer
        } else {
            updateTunnelOutput('Failed to start localtunnel: ' + (result.error || result.status), 'error');
            updateTunnelStatus('Error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
        updateTunnelStatus('Error');
    }
}

async function stopLocaltunnel() {
    updateTunnelOutput('Stopping localtunnel...', 'warning');
    
    try {
        const result = await safeFetchJSON('/api/localtunnel/stop', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Localtunnel stopped.', 'success');
            setTimeout(checkAllTunnelStatus, 1000);
        } else {
            updateTunnelOutput('Failed to stop localtunnel: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
    }
}

async function startCloudflared() {
    updateTunnelOutput('Starting cloudflared tunnel...', 'warning');
    updateTunnelStatus('Starting...');
    
    try {
        const result = await safeFetchJSON('/api/cloudflared/start', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Cloudflared tunnel started! Checking for public URL...', 'success');
            setTimeout(checkAllTunnelStatus, 8000); // Cloudflared takes longer
        } else {
            updateTunnelOutput('Failed to start cloudflared: ' + (result.error || result.status), 'error');
            updateTunnelStatus('Error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
        updateTunnelStatus('Error');
    }
}

async function stopCloudflared() {
    updateTunnelOutput('Stopping cloudflared tunnel...', 'warning');
    
    try {
        const result = await safeFetchJSON('/api/cloudflared/stop', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('Cloudflared tunnel stopped.', 'success');
            setTimeout(checkAllTunnelStatus, 1000);
        } else {
            updateTunnelOutput('Failed to stop cloudflared: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
    }
}

async function checkAllTunnelStatus() {
    updateTunnelOutput('Checking all tunnel statuses...', 'warning');
    
    try {
        const result = await safeFetchJSON('/api/tunnels/status');
        
        if (result.success) {
            let output = '<strong>Tunnel Status:</strong>\n';
            let activeTunnels = 0;
            
            for (const [name, data] of Object.entries(result.tunnels)) {
                output += `\n<strong>${name.charAt(0).toUpperCase() + name.slice(1)}:</strong>\n`;
                output += `  Status: ${data.status}\n`;
                if (data.public_url) {
                    output += `  URL: <a href="${data.public_url}" target="_blank">${data.public_url}</a>\n`;
                    activeTunnels++;
                }
            }
            
            updateTunnelOutput(output, 'success');
            updateTunnelStatus(`${activeTunnels} active tunnel(s)`);
        } else {
            updateTunnelOutput('Failed to get tunnel status: ' + (result.error || 'Unknown error'), 'error');
            updateTunnelStatus('Error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
        updateTunnelStatus('Error');
    }
}

async function stopAllTunnels() {
    if (!confirm('Are you sure you want to stop ALL active tunnels?')) {
        return;
    }
    
    updateTunnelOutput('Stopping all tunnels...', 'warning');
    
    try {
        const result = await safeFetchJSON('/api/tunnels/stop-all', { method: 'POST' });
        
        if (result.success) {
            updateTunnelOutput('All tunnels stopped.', 'success');
            setTimeout(checkAllTunnelStatus, 1000);
        } else {
            updateTunnelOutput('Failed to stop all tunnels: ' + (result.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        updateTunnelOutput('Error: ' + error.message, 'error');
    }
}

function updateTunnelOutput(message, type) {
    const outputDiv = document.getElementById('tunnelOutput');
    const color = type === 'success' ? '#00ff00' : type === 'error' ? '#ff6b35' : '#ffff00';
    outputDiv.innerHTML = `<span style="color: ${color};">${message}</span>`;
}

function updateTunnelStatus(status) {
    document.getElementById('tunnelStatus').textContent = `Status: ${status}`;
}

// File storage functions
async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const outputDiv = document.getElementById('fileOutput');
    
    if (!fileInput.files || fileInput.files.length === 0) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Please select one or more files</span>';
        return;
    }
    
    const formData = new FormData();
    for (const file of fileInput.files) {
        formData.append('files', file);  // Backend expects 'files' not 'files[]'
    }
    
    outputDiv.innerHTML = '<span style="color: #ffff00;">Uploading files...</span>';
    
    try {
        const response = await fetch('/api/files/upload', {
            method: 'POST',
            body: formData
        });
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            let fileDetails = result.files.map(f => `✅ ${f.filename} (${f.size} bytes)`).join('<br>');
            outputDiv.innerHTML = `<span style="color: #00ff00;">${result.message}</span><br>${fileDetails}`;
            fileInput.value = ''; // Clear the file input
            refreshFiles();
        } else {
            outputDiv.innerHTML = '<span style="color: #ff6b35;">Upload failed: ' + (result.error || 'Unknown error') + '</span>';
        }
    } catch (error) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Error: ' + error.message + '</span>';
    }
}

async function refreshFiles() {
    const listDiv = document.getElementById('fileList');
    const storageInfoDiv = document.getElementById('storageInfo');
    
    try {
        const result = await safeFetchJSON('/api/files/list');
        
        if (result.success) {
            const files = result.files;
            const info = result.storage_info;
            
            storageInfoDiv.innerHTML = `Total Files: ${info.file_count} | Total Size: ${info.used_mb.toFixed(2)} MB | Available: ${info.available_bytes > 0 ? (info.available_bytes / (1024*1024)).toFixed(2) : 0} MB`;
            
            if (files.length === 0) {
                listDiv.innerHTML = '<div style="text-align: center; color: #888;">No files uploaded yet</div>';
                return;
            }
            
            let html = '';
            files.forEach(file => {
                html += `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #444;">
                        <div>
                            <a href="/api/files/download/${file.filename}" target="_blank" style="color: #9cdcfe; text-decoration: none;">
                                📄 ${file.filename}
                            </a>
                            <span style="color: #888; font-size: 11px; margin-left: 10px;">
                                (${(file.size / 1024).toFixed(1)} KB)
                            </span>
                        </div>
                        <button onclick="deleteFile('${file.filename}')" class="danger" style="padding: 4px 8px; font-size: 11px;">
                            🗑️ Delete
                        </button>
                    </div>`;
            });
            listDiv.innerHTML = html;
        } else {
            listDiv.innerHTML = '<div style="color: #ff6b35;">Error loading files: ' + result.error + '</div>';
        }
    } catch (error) {
        listDiv.innerHTML = '<div style="color: #ff6b35;">Error: ' + error.message + '</div>';
    }
}

async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    try {
        const result = await safeFetchJSON(`/api/files/delete/${filename}`, { method: 'DELETE' });
        
        if (result.success) {
            document.getElementById('fileOutput').innerHTML = `<span style="color: #00ff00;">${result.message}</span>`;
            refreshFiles();
        } else {
            document.getElementById('fileOutput').innerHTML = `<span style="color: #ff6b35;">Delete failed: ${result.error || 'Unknown error'}</span>`;
        }
    } catch (error) {
        document.getElementById('fileOutput').innerHTML = `<span style="color: #ff6b35;">Error: ${error.message}</span>`;
    }
}

// Initial load
window.onload = () => {
    checkServerHealth();
    getMachineInfo();
    loadProgramList();
    refreshFiles();
    checkAllTunnelStatus();
    initProgramsTerminal();
};

// Programs Terminal - Persistent session in programs directory
let programsTerminalSessionId = null;

async function initProgramsTerminal() {
    try {
        const result = await safeFetchJSON('/api/programs-terminal/init', {
            method: 'POST'
        });
        
        if (result.success) {
            programsTerminalSessionId = result.session_id;
            document.getElementById('programsTerminalPath').textContent = result.working_dir || '/programs';
            console.log('Programs terminal initialized:', result.session_id);
        } else {
            document.getElementById('programsTerminalOutput').innerHTML = '<span style="color: #ff6b35;">Failed to initialize programs terminal: ' + (result.error || 'Unknown error') + '</span>';
        }
    } catch (error) {
        document.getElementById('programsTerminalOutput').innerHTML = '<span style="color: #ff6b35;">Error initializing programs terminal: ' + error.message + '</span>';
    }
}

function handleProgramsTerminalEnter(event) {
    if (event.key === 'Enter') {
        executeProgramsTerminal();
    }
}

async function executeProgramsTerminal() {
    const commandInput = document.getElementById('programsTerminalCommand');
    const outputDiv = document.getElementById('programsTerminalOutput');
    const pathDisplay = document.getElementById('programsTerminalPath');
    
    const command = commandInput.value.trim();
    if (!command) return;
    
    if (!programsTerminalSessionId) {
        outputDiv.innerHTML = '<span style="color: #ff6b35;">Terminal session not initialized. Refreshing page...</span>';
        setTimeout(() => window.location.reload(), 2000);
        return;
    }
    
    // Add command to output with prompt
    const timestamp = new Date().toLocaleTimeString();
    const commandDisplay = `<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #444;">
        <div style="color: #888; font-size: 10px;">${timestamp}</div>
        <div style="color: #00ff00;">$ ${escapeHtml(command)}</div>
    </div>`;
    
    outputDiv.innerHTML += commandDisplay;
    outputDiv.scrollTop = outputDiv.scrollHeight;
    
    // Clear input
    commandInput.value = '';
    
    try {
        const result = await safeFetchJSON('/api/programs-terminal/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: programsTerminalSessionId,
                command: command
            })
        });
        
        if (result.success) {
            // Display output
            const output = result.output || '';
            const outputHtml = `<pre style="margin: 5px 0; white-space: pre-wrap; word-wrap: break-word;">${escapeHtml(output)}</pre>`;
            outputDiv.innerHTML += outputHtml;
            
            // Update working directory if changed
            if (result.working_dir) {
                pathDisplay.textContent = result.working_dir;
            }
        } else {
            outputDiv.innerHTML += `<div style="color: #ff6b35;">Error: ${result.error || 'Command failed'}</div>`;
        }
    } catch (error) {
        outputDiv.innerHTML += `<div style="color: #ff6b35;">Error: ${error.message}</div>`;
    }
    
    outputDiv.scrollTop = outputDiv.scrollHeight;
}

async function quickProgramsCommand(command) {
    document.getElementById('programsTerminalCommand').value = command;
    await executeProgramsTerminal();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
