// Global State
let userToken = localStorage.getItem('token');
let currentUsername = localStorage.getItem('username');

// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
    if (!userToken && !window.location.pathname.includes('login')) {
        window.location.href = '/login';
    }
    document.getElementById('displayUsername').innerText = currentUsername || 'Guest';
});

// View Toggle Logic
function showView(view) {
    const searchView = document.getElementById('viewSearch');
    const collectionView = document.getElementById('viewCollection');
    const btnSearch = document.getElementById('btnSearch');
    const btnCollection = document.getElementById('btnCollection');

    if (view === 'search') {
        searchView.style.display = 'block';
        collectionView.style.display = 'none';
        btnSearch.classList.add('active');
        btnCollection.classList.remove('active');
    } else {
        searchView.style.display = 'none';
        collectionView.style.display = 'block';
        btnSearch.classList.remove('active');
        btnCollection.classList.add('active');
        fetchCollection(); // Refresh collection when switching
    }
}

// ... keep existing state and toggle logic ...


async function sendPrompt() {
    const inputField = document.getElementById('userInput');
    const prompt = inputField.value;
    const category = document.getElementById('chatCategory').value;
    
    if (!prompt) return alert("Please enter a prompt");

    const chatWindow = document.getElementById('chatWindow');
    chatWindow.innerHTML += `<div class="user-msg"><b>You:</b> ${prompt}</div>`;
    
    // Auto-scroll to bottom after user message
    chatWindow.scrollTop = chatWindow.scrollHeight;
    
    // Clear input
    inputField.value = '';

    try {
        const response = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify({ prompt, category })
        });
        
        const result = await response.json();
        if (result.status === 'success') {
            // 1. Render the table
            renderAiTable(result.data, category);

            // 2. Add a bot message to the chat history
            chatWindow.innerHTML += `<div class="bot-msg">I've found some <b>${category}</b> resources for you. Check the table below!</div>`;

            // 3. Auto-scroll the page down to the table
            setTimeout(() => {
                const tableContainer = document.getElementById('aiResponseTable');
                tableContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);

        } else {
            alert(result.message);
        }
    } catch (err) {
        console.error("Chat Error:", err);
    }
}
// async function sendPrompt() {
//     const inputField = document.getElementById('userInput');
//     const prompt = inputField.value;
//     const category = document.getElementById('chatCategory').value;
    
//     if (!prompt) return alert("Please enter a prompt");

//     const chatWindow = document.getElementById('chatWindow');
//     chatWindow.innerHTML += `<div class="user-msg"><b>You:</b> ${prompt}</div>`;
    
//     // Auto-scroll to bottom
//     chatWindow.scrollTop = chatWindow.scrollHeight;
    
//     // Clear input
//     inputField.value = '';

//     try {
//         const response = await fetch('/api/v1/chat', {
//             method: 'POST',
//             headers: { 
//                 'Content-Type': 'application/json',
//                 'Authorization': `Bearer ${userToken}`
//             },
//             body: JSON.stringify({ prompt, category })
//         });
        
//         const result = await response.json();
//         if (result.status === 'success') {
//             renderAiTable(result.data, category);
//         } else {
//             alert(result.message);
//         }
//     } catch (err) {
//         console.error("Chat Error:", err);
//     }
// }

// AI Chat Logic
// async function sendPrompt() {
//     const prompt = document.getElementById('userInput').value;
//     const category = document.getElementById('chatCategory').value;
//     const tableContainer = document.getElementById('aiResponseTable');
    
//     if (!prompt) return alert("Please enter a prompt");

//     // Add user message to UI
//     const chatWindow = document.getElementById('chatWindow');
//     chatWindow.innerHTML += `<div class="user-msg"><b>You:</b> ${prompt}</div>`;
    
//     try {
//         const response = await fetch('/api/v1/chat', {
//             method: 'POST',
//             headers: { 
//                 'Content-Type': 'application/json',
//                 'Authorization': `Bearer ${userToken}`
//             },
//             body: JSON.stringify({ prompt, category })
//         });
        
//         const result = await response.json();
//         if (result.status === 'success') {
//             renderAiTable(result.data, category);
//         } else {
//             alert(result.message);
//         }
//     } catch (err) {
//         console.error("Chat Error:", err);
//     }
// }



function renderAiTable(data, category) {
    const container = document.getElementById('aiResponseTable');
    container.style.display = 'block';
    
    let html = `
        <h3>AI Suggestions (${category})</h3>
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Rating</th>
                    <th>Link</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>`;
    
    data.forEach(item => {
        html += `
            <tr>
                <td>${item.name}</td>
                <td>${item.description}</td>
                <td>${item.rating}</td>
                <td><a href="${item.link}" target="_blank">View</a></td>
                <td><button onclick="addToCollection('${item.name}', '${item.link}', '${category}')">Add</button></td>
            </tr>`;
    });
    
    html += `</tbody></table>`;
    container.innerHTML = html;
}

// Collection Logic
async function addToCollection(name, link, category) {
    const response = await fetch('/api/v1/collection', {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({ resource_name: name, links: link, category: category })
    });
    
    const result = await response.json();
    alert(result.message);
}

async function fetchCollection() {
    const response = await fetch('/api/v1/collection', {
        headers: { 'Authorization': `Bearer ${userToken}` }
    });
    const result = await response.json();
    
    const body = document.getElementById('collectionBody');
    body.innerHTML = '';
    
    result.data.forEach((item, index) => {
        body.innerHTML += `
            <tr>
                <td>${index + 1}</td>
                <td>${item.category}</td>
                <td>${item.resource_name}</td>
                <td><a href="${item.links}" target="_blank">Link</a></td>
                <td><button onclick="confirmDelete('${item._id}', '${item.resource_name}')">Delete</button></td>
            </tr>`;
    });
}

function confirmDelete(id, name) {
    if (confirm(`Are you sure you want to delete ${name}?`)) {
        deleteResource(id);
    }
}

async function deleteResource(id) {
    const response = await fetch(`/api/v1/collection/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${userToken}` }
    });
    const result = await response.json();
    if (result.status === 'success') {
        fetchCollection();
    }
}

// Toggle between Login and Register forms
function toggleAuth() {
    const loginBox = document.getElementById('loginBox');
    const registerBox = document.getElementById('registerBox');
    if (loginBox.style.display === 'none') {
        loginBox.style.display = 'block';
        registerBox.style.display = 'none';
    } else {
        loginBox.style.display = 'none';
        registerBox.style.display = 'block';
    }
}

async function handleRegister() {
    const username = document.getElementById('regUser').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPass').value;

    const response = await fetch('/api/v1/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
    });

    const result = await response.json();
    if (result.status === 'success') {
        alert("Registration successful! Please login.");
        toggleAuth();
    } else {
        alert("Error: " + JSON.stringify(result.message));
    }
}

async function handleLogin() {
    const username = document.getElementById('loginUser').value;
    const password = document.getElementById('loginPass').value;

    const response = await fetch('/api/v1/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });

    const result = await response.json();
    if (result.status === 'success') {
        localStorage.setItem('token', result.token);
        localStorage.setItem('username', result.username);
        window.location.href = '/';
    } else {
        alert(result.message);
    }
}

// Simple Logout function
function logout() {
    localStorage.clear();
    window.location.href = '/login';
}


// Profile Initialization
if (window.location.pathname === '/profile') {
    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('profileUsername').innerText = localStorage.getItem('username');
    });
}

async function updatePassword() {
    const newPass = document.getElementById('newPassword').value;
    if (newPass.length < 6) return alert("Password must be at least 6 characters");

    const response = await fetch('/api/v1/update-password', {
        method: 'PUT',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ password: newPass })
    });

    const result = await response.json();
    alert(result.message);
}

function confirmSelfDelete() {
    if (confirm("Are you absolutely sure? This will delete your account and all saved collections.")) {
        executeSelfDelete();
    }
}

async function executeSelfDelete() {
    const response = await fetch('/api/v1/me', {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });

    const result = await response.json();
    if (result.status === 'success') {
        alert("Account deleted.");
        logout();
    }
}

function handleSignout() {
    // 1. Remove the token and user data from browser storage
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    
    // 2. Clear any other session-related items
    localStorage.clear(); 
    
    // 3. Optional: Alert the user or log it
    console.log("User signed out successfully.");

    // 4. Redirect to the login page
    window.location.href = '/login';
}

// Admin Logic
if (window.location.pathname === '/admin') {
    document.addEventListener('DOMContentLoaded', fetchAllUsers);
}

async function fetchAllUsers() {
    try {
        const response = await fetch('/api/v1/admin/users');
        const result = await response.json();
        
        if (result.status === 'success') {
            const body = document.getElementById('adminUserBody');
            document.getElementById('userCount').innerText = result.data.length;
            body.innerHTML = '';

            result.data.forEach(user => {
                const statusClass = user.is_active ? 'status-active' : 'status-inactive';
                const statusText = user.is_active ? 'Active' : 'Terminated';
                
                body.innerHTML += `
                    <tr>
                        <td>${user.username}</td>
                        <td>${user.email}</td>
                        <td class="${statusClass}">${statusText}</td>
                        <td>
                            <button class="terminate-btn" 
                                ${!user.is_active ? 'disabled' : ''} 
                                onclick="terminateUser('${user._id}', '${user.username}')">
                                Terminate
                            </button>
                        </td>
                    </tr>`;
            });
        }
    } catch (err) {
        console.error("Admin Fetch Error:", err);
    }
}

async function terminateUser(userId, username) {
    const reason = prompt(`Enter reason for terminating ${username}:`);
    
    if (reason === null) return; // Cancelled
    if (reason.trim().length < 5) return alert("Please provide a valid reason (min 5 chars).");

    const response = await fetch('/api/v1/admin/terminate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, reason: reason })
    });

    const result = await response.json();
    if (result.status === 'success') {
        alert(`User ${username} has been deactivated.`);
        fetchAllUsers(); // Refresh the list
    } else {
        alert(result.message);
    }
}


