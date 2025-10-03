
# UpDownVid - Multi-Platform Video Downloader

> Fast, simple, and free video downloader supporting 12+ platforms. Download videos from YouTube, Instagram, Facebook, TikTok, and more.

## ✨ Features

- 🎬 **12+ Platforms** - YouTube, Instagram, Facebook, Twitter/X, TikTok, Vimeo, Reddit, Twitch, Rumble, Dailymotion, Pinterest, Snapchat
- 📺 **High Quality** - Minimum 720p, up to 1080p HD downloads
- 🎯 **Smart Metadata** - Automatic title, description, hashtag extraction
- 🤖 **YouTube Automation** - Monitor channels and auto-upload new videos
- 🔒 **Privacy-First** - No analytics, no tracking, no permanent storage
- 🌐 **Open Source** - Built with Flask, yt-dlp, Bootstrap 5

## 🚀 Quick Start on Replit

### 1. Fork/Import Repository

1. Click **Fork** or import this repository into Replit
2. Wait for the environment to build

### 2. Configure Secrets

Open **Secrets** (🔒 icon in left sidebar) and add these required keys:

```env
# Required
SESSION_SECRET=your-random-secret-key-here
FLASK_SECRET_KEY=another-random-secret-key
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret
GOOGLE_REDIRECT_URI=https://your-repl-name.repl.co/google_login/callback

# Optional but recommended
YOUTUBE_API_KEY=your-youtube-api-key
CONTACT_EMAIL=support@yourdomain.com
COPYRIGHT_EMAIL=copyright@yourdomain.com
```

**How to get credentials:**
- **Google OAuth:** [Google Cloud Console](https://console.cloud.google.com/) → Create OAuth 2.0 Client
- **YouTube API:** [Google Cloud Console](https://console.cloud.google.com/) → Enable YouTube Data API v3
- **Random secrets:** Use `openssl rand -hex 32` or online generator

### 3. Start the Application

Click the **Run** button! The app will:
1. Auto-install dependencies from `requirements.txt`
2. Start on port 5000
3. Open in a new browser tab

Your app is now live at: `https://your-repl-name.repl.co`

## 💻 Local Development

### Prerequisites
- Python 3.11+
- pip
- FFmpeg

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/yourusername/updownvid.git
cd updownvid

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor

# Run the application (auto-installs dependencies)
python run.py
```

Visit: `http://localhost:5000`

### Manual Installation (Alternative)

```bash
# Install dependencies manually
pip install -r requirements.txt

# Run with Flask development server
python main.py
```

## 🌐 Deployment on Replit

### Autoscale Deployment (Recommended)

1. Click **Deploy** in the top-right
2. Choose **Autoscale Deployment**
3. Configure:
   - **Machine:** 1 vCPU, 2 GiB RAM (default)
   - **Max machines:** 3 (adjust as needed)
   - **Domain:** Choose your custom domain
   - **Run command:** `python run.py` (or use default)
4. Click **Deploy**

Your app will be live with automatic scaling!

### Environment Variables for Production

Add these in Replit Secrets for production:

```env
DEBUG=False
FRONTEND_URL=https://yourdomain.com
BACKEND_URL=https://yourdomain.com
ENABLE_CONTACT_FORM=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

## 🔧 Configuration

### `.env` File Structure

See `.env.example` for all available options:

```env
# Server
PORT=5000
DEBUG=False

# Security (REQUIRED)
SESSION_SECRET=change-me
FLASK_SECRET_KEY=change-me

# Google OAuth (REQUIRED for YouTube upload)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=...

# Optional Features
YOUTUBE_API_KEY=...
ENABLE_AUTOMATION=true
ENABLE_CONTACT_FORM=true
MAX_FILE_SIZE_MB=500
```

### Supported Platforms Configuration

Edit `multi_platform_downloader.py` to customize:
- Video quality preferences
- Download formats
- Platform-specific settings
- Cookie authentication

## 📚 Documentation

- **[About](/about)** - Project story and mission
- **[FAQ](/faq)** - Common questions and troubleshooting
- **[Terms of Service](/tos)** - Usage rules and policies
- **[Privacy Policy](/privacy)** - Data handling and privacy
- **[Copyright/DMCA](/copyright)** - Takedown process
- **[Contact](/contact)** - Get help and support

## 🐛 Troubleshooting

### Common Issues

**Import errors on startup:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**OAuth redirect mismatch:**
- Update `GOOGLE_REDIRECT_URI` in `.env` to match your domain
- Add the URI in Google Cloud Console → OAuth consent screen

**Download fails:**
- Check if platform is supported: `/platforms`
- Verify URL is public and accessible
- Some platforms may require cookies (check `/faq`)

**Contact form not working:**
- Set `ENABLE_CONTACT_FORM=true` in `.env`
- Configure SMTP settings (Gmail App Password recommended)

### Getting Help

- **Email:** support@updownvid.com
- **GitHub Issues:** [Report bugs](https://github.com/yourusername/updownvid/issues)
- **Discord:** [Community support](https://discord.gg/updownvid)

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **yt-dlp** - Powerful video downloader library
- **Flask** - Python web framework
- **Bootstrap** - UI framework
- **Replit** - Development and hosting platform

## 📞 Contact & Support

- **Website:** [updownvid.com](https://updownvid.com)
- **Email:** support@updownvid.com
- **GitHub:** [github.com/yourusername/updownvid](https://github.com/yourusername/updownvid)
- **Discord:** [discord.gg/updownvid](https://discord.gg/updownvid)

---

**Built with ❤️ by the UpDownVid Team**

*Making online content accessible for everyone.*
