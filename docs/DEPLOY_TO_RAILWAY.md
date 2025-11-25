# 🚀 Deploy to Railway - Step by Step

## Prerequisites
- GitHub account
- Railway account (free)

---

## Step 1: Create GitHub Repository (5 minutes)

### 1.1 Create New Repository
1. Go to: https://github.com/new
2. Repository name: `twilio-voice-agent`
3. Description: `AI Voice Agent with Twilio and Sarvam AI`
4. **Keep it Private** (recommended - contains API keys)
5. **DO NOT** initialize with README (we already have one)
6. Click **"Create repository"**

### 1.2 Push Your Code
Open PowerShell in your project folder and run:

```powershell
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Twilio Voice Agent"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/twilio-voice-agent.git

# Push to GitHub
git push -u origin main
```

**Note:** If it asks for `master` instead of `main`, use:
```powershell
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Railway (5 minutes)

### 2.1 Sign Up for Railway
1. Go to: https://railway.app
2. Click **"Login"**
3. Choose **"Login with GitHub"**
4. Authorize Railway

### 2.2 Create New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: `twilio-voice-agent`
4. Railway will automatically detect it's a Python project

### 2.3 Add Environment Variables
1. Click on your deployed service
2. Go to **"Variables"** tab
3. Click **"Add Variable"** and add these:

```
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+12234007545
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_STT_URL=https://api.sarvam.ai/speech-to-text
SARVAM_TTS_URL=https://api.sarvam.ai/text-to-speech
SARVAM_LLM_URL=https://api.sarvam.ai/v1/chat/completions
PORT=8000
```

**Note:** Copy the actual values from your `.env` file when adding to Railway!

4. Click **"Add"** for each variable

### 2.4 Get Your Railway URL
1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Copy your URL (e.g., `https://twilio-voice-agent-production.up.railway.app`)

---

## Step 3: Configure Twilio (2 minutes)

### 3.1 Update Twilio Webhook
1. Go to: https://console.twilio.com/us1/develop/phone-numbers/manage/incoming
2. Click your number: **+1 223 400 7545**
3. Under "Voice Configuration":
   - **A CALL COMES IN:** Webhook
   - **URL:** `https://your-app.railway.app/voice/incoming`
   - **HTTP:** POST
4. Click **"Save"**

---

## Step 4: Test! 🎉

**Call +1 223 400 7545**

You should hear:
1. Twilio trial message (if not upgraded) - Press any key
2. "Congratulations! Your AI voice agent is working!"
3. Then connected to AI conversation

---

## Troubleshooting

### Deployment Failed
- Check Railway logs: Click on your service → "Deployments" → Click latest deployment
- Common issues:
  - Missing environment variables
  - Wrong Python version (should be 3.11)

### Call Not Working
- Check Railway logs for incoming requests
- Verify webhook URL in Twilio is correct
- Make sure all environment variables are set

### Server Not Starting
- Check if PORT is set to 8000
- Verify requirements.txt has all dependencies

---

## Next Steps

### Remove Twilio Trial Message
1. Go to: https://console.twilio.com/us1/billing/manage-billing/billing-overview
2. Add $20 credit
3. Trial message will be removed automatically

### Monitor Your App
- Railway Dashboard: https://railway.app/dashboard
- View logs, metrics, and usage
- Free tier: 500 hours/month (plenty for testing!)

---

## Cost Summary

- **Railway**: FREE (500 hours/month)
- **Twilio Trial**: FREE ($14 credit)
- **Sarvam AI**: FREE (with your API key)

**Total: $0** ✅

---

**Your AI Voice Agent is now live 24/7!** 🎉
