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

## Troubleshooting

- **DNS not working**: DNS changes can take up to 48 hours to propagate. Use tools like `dig` or `nslookup` to check DNS resolution.
- **SSL certificate issues**: Make sure Certbot completed successfully and check Nginx logs.
- **Paddle still returning localhost URLs**: Verify your Paddle account settings and ensure the domain is properly registered in your Paddle dashboard.
- **Application errors**: Check application logs with `pm2 logs` or App Platform logs.

## Using Paddle's Test Environment

When testing your integration:
1. Use Paddle's sandbox environment
2. Use test card numbers (e.g., 4242 4242 4242 4242)
3. Verify webhook receipt and transaction flows before going to production
