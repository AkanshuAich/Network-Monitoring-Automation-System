# 🚀 Deploying to Render (Free Tier)

This guide walks you through deploying the **Network Monitoring & Automation System** to Render's free tier.

## Prerequisites
- A [GitHub](https://github.com/) or [GitLab](https://gitlab.com/) account.
- A [Render](https://render.com/) account.

## Step 1: Push Code to Git
1.  Initialize a git repository if you haven't already:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```
2.  Push your code to a new repository on GitHub or GitLab.

## Step 2: Create a Blueprint on Render
1.  Log in to your [Render Dashboard](https://dashboard.render.com/).
2.  Click **New +** and select **Blueprint**.
3.  Connect your GitHub/GitLab account and select the repository you just pushed.
4.  Render will automatically detect the `render.yaml` file in the root of your repository.
5.  Click **Apply** to start the deployment.

## Step 3: Verify Deployment
Render will build and deploy both services automatically:

1.  **Backend (`netmonitor-backend`)**: This will be a Web Service running Python.
    - It may take a few minutes to build.
    - Once live, you can find its URL (e.g., `https://netmonitor-backend.onrender.com`).
2.  **Frontend (`netmonitor-frontend`)**: This will be a Static Site.
    - It will build the React app and serve the static files.
    - Render automatically injects the backend URL into the frontend build process via the `VITE_API_URL` environment variable defined in `render.yaml`.

## ⚠️ Free Tier Limitations
- **Spin Down**: The free tier web service (backend) will spin down after 15 minutes of inactivity. The first request after spin-down may take up to 30 seconds to respond.
- **Resource Limits**: 512 MB RAM and 0.1 CPU.
