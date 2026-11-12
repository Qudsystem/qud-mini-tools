// Mock data
const repositories = [
    { name: "Repository 1", description: "This is repository 1" },
    { name: "Repository 2", description: "This is repository 2" },
    { name: "Repository 3", description: "This is repository 3" }
];

const issues = [
    { title: "Issue 1", description: "This is issue 1" },
    { title: "Issue 2", description: "This is issue 2" },
    { title: "Issue 3", description: "This is issue 3" }
];

const pullRequests = [
    { title: "Pull Request 1", description: "This is pull request 1" },
    { title: "Pull Request 2", description: "This is pull request 2" },
    { title: "Pull Request 3", description: "This is pull request 3" }
];

// Render repository list
document.getElementById("repo-list").innerHTML = repositories.map((repo) => {
    return `
        <li class="repo-list-item">
            <h3>${repo.name}</h3>
            <p>${repo.description}</p>
        </li>
    `;
}).join("");

// Render issue list
document.getElementById("issue-list").innerHTML = issues.map((issue) => {
    return `
        <li class="issue-list-item">
            <h3>${issue.title}</h3>
            <p>${issue.description}</p>
        </li>
    `;
}).join("");

// Render pull request list
document.getElementById("pr-list").innerHTML = pullRequests.map((pr) => {
    return `
        <li class="pr-list-item">
            <h3>${pr.title}</h3>
            <p>${pr.description}</p>
        </li>
    `;
}).join("");