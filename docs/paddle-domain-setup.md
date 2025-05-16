# Setting Up a Custom Domain with HTTPS for Paddle Integration

This guide walks you through setting up a custom domain with HTTPS using DigitalOcean, which will fix the Paddle checkout URL issue.

## Step 1: Register a Domain

If you don't already have a domain:

1. Use a domain registrar like Namecheap, GoDaddy, or Google Domains to register a domain
2. Alternatively, you can register a domain directly through DigitalOcean

## Step 2: Set Up Your Application on DigitalOcean

You have two main options:

### Option A: App Platform (Recommended for a quick setup)

1. Log in to your DigitalOcean account
2. Click on "Apps" in the left sidebar
3. Click "Create App"
4. Connect your GitHub repository or upload your code
5. Select your branch and configure the build settings
6. In the Resources tab, select appropriate plan for your application
7. Add any environment variables needed for your app
8. Review and launch your app

### Option B: Traditional Droplet

1. Log in to your DigitalOcean account
2. Click on "Droplets" in the left sidebar
3. Click "Create Droplet"
4. Choose an image (Ubuntu is a good default)
5. Select a plan (the smallest $5 plan should be sufficient for testing)
6. Select a datacenter region close to your users
7. Add your SSH key or select password authentication
8. Click "Create Droplet"

## Step 3: Configure DNS Settings

1. Go to the "Networking" section in DigitalOcean
2. Click "Domains"
3. Add your domain
4. Create the following DNS records:
   - An A record pointing to your Droplet's IP address or CNAME for App Platform
   - A www A/CNAME record (optional)
5. If your domain is registered elsewhere, update your domain's nameservers to point to DigitalOcean's nameservers or create the appropriate A/CNAME records at your registrar

## Step 4: Set Up HTTPS with Let's Encrypt

### For App Platform:
HTTPS is automatically configured for you.

### For Droplet:
1. SSH into your Droplet
2. Install Nginx:
   ```
   sudo apt update
   sudo apt install nginx
   ```
3. Install Certbot for Let's Encrypt:
   ```
   sudo apt install certbot python3-certbot-nginx
   ```
4. Configure Nginx for your domain:
   ```
   sudo nano /etc/nginx/sites-available/yourdomain.com
   ```
5. Add a basic configuration:
   ```
   server {
       listen 80;
       server_name yourdomain.com www.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;  # Your FastAPI port
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```
6. Enable the site:
   ```
   sudo ln -s /etc/nginx/sites-available/yourdomain.com /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```
7. Get SSL certificate:
   ```
   sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## Step 5: Deploy Your Application

### For App Platform:
Your application is already deployed.

### For Droplet:
1. Install required dependencies (Node.js, Python, etc.)
2. Clone your repository or upload your code
3. Set up environment variables
4. Install dependencies and build your application
5. Set up a process manager like PM2 to keep your app running

## Step 6: Update Your Application Configuration

Update your .env file with the new domain:

```
FRONTEND_URL=https://yourdomain.com
```

## Step 7: Configure Paddle Integration

1. Log in to your Paddle account
2. Go to "Developer Tools" > "Integration"
3. Add your new domain (https://yourdomain.com) to the allowed domains
4. Update your webhook URLs to use your new domain
5. For sandbox testing, make sure to add your domain to the sandbox environment too
6. Save your changes

## Step 8: Test Your Integration

1. Open your application at https://yourdomain.com
2. Try to create a subscription
3. Check if Paddle redirects properly
4. Verify transaction completion

## Troubleshooting App Platform Build Failures

If you encounter a "Build Error: Non-Zero Exit" or other build failures in DigitalOcean App Platform:

### 1. Check Your Build Command

Make sure your build command is correct:

- For a Node.js frontend: `npm run build` or `yarn build`
- For Python backend: `pip install -r requirements.txt`

Add a `Dockerfile` or `.do/app.yaml` file to your repository for more control over the build process.

### 2. Review Environment Variables

Ensure all required environment variables are properly set in the App Platform console:

1. Go to your app dashboard
2. Click on the "Settings" tab
3. Select "Environment Variables"
4. Add any missing variables that might be needed during the build process

### 3. Check Dependency Issues

1. Review your `package.json` or `requirements.txt` for incompatible dependencies
2. Make sure you're not using dependencies that aren't compatible with the Node.js or Python version you've selected
3. Check for any private dependencies that might require authentication

### 4. Add a Build Log Environment Variable

Add `BUILD_VERBOSE=true` to your environment variables to get more detailed build logs.

### 5. Examine the Specific Error Message

Common build errors and solutions:

- **Node.js memory issues**: Increase the build instance size
- **Missing dependencies**: Add them to your package.json or requirements.txt
- **Syntax errors**: Fix the identified code issues
- **Python version compatibility**: Use a .python-version file to specify your Python version
- **Node version compatibility**: Use a .nvmrc file or specify "engines" in package.json

### 6. Try a Manual Deployment

For quick testing, you can deploy your application manually to a Droplet:

1. SSH into your Droplet
2. Clone your repository
3. Install dependencies manually
4. Build the application manually
5. Use PM2 or a similar tool to run the application

This approach gives you more visibility into the build process and can help identify specific issues.

### 7. Sample Development .env Configuration

Here's a sample development `.env` file that works with Paddle sandbox and DigitalOcean App Platform:

```
# Development Environment
APP_ENV=development

# Domain Configuration
FRONTEND_URL=https://your-app-name.ondigitalocean.app

# Paddle Settings
PADDLE_SANDBOX=true
PADDLE_CHECKOUT_SUCCESS_URL=https://your-app-name.ondigitalocean.app/subscription/success
PADDLE_CHECKOUT_CANCEL_URL=https://your-app-name.ondigitalocean.app/subscription/cancel
```

## Using Paddle's Test Environment

When testing your integration:
1. Use Paddle's sandbox environment
2. Use test card numbers (e.g., 4242 4242 4242 4242)
3. Verify webhook receipt and transaction flows before going to production
