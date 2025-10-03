
# Frequently Asked Questions (FAQ)

## General Questions

### What is UpDownVid?
UpDownVid is a free, open-source multi-platform video downloader and metadata extraction tool. It supports 12+ platforms including YouTube, Instagram, Facebook, TikTok, Twitter/X, Vimeo, Reddit, Twitch, and more.

### Is UpDownVid free to use?
Yes! UpDownVid is completely free for personal use. We're open-source and community-driven.

### Do I need to create an account?
No account is required for basic video downloading and metadata extraction. However, you'll need to connect your Google account for YouTube upload automation features.

## Supported Platforms

### Which platforms are supported?
We currently support:

✅ **YouTube** - Videos, playlists, live streams  
✅ **Instagram** - Reels, posts, stories, IGTV  
✅ **Facebook** - Public videos and posts  
✅ **Twitter/X** - Video tweets and embedded videos  
✅ **TikTok** - Videos and user content  
✅ **Vimeo** - Public and unlisted videos  
✅ **Reddit** - Video posts and embedded content  
✅ **Twitch** - Clips and VODs  
✅ **Rumble** - Videos and livestreams  
✅ **Dailymotion** - Videos and playlists  
✅ **Pinterest** - Video pins  
✅ **Snapchat** - Spotlight videos  
✅ **Direct URLs** - Direct video file links (.mp4, .webm, .mkv)

### How do I request support for a new platform?
Open an issue on our [GitHub repository](https://github.com/yourusername/updownvid/issues) with the platform name and example URLs.

## Download Features

### What quality videos can I download?
- **Minimum Quality:** 720p HD
- **Maximum Quality:** 1080p Full HD
- **Formats:** MP4 (preferred), WebM (fallback)

### What's the file size limit?
Current public limit: **500 MB** per download  
For larger files, contact: business@updownvid.com

### Where are downloaded videos stored?
Videos are temporarily stored on our servers during processing and **automatically deleted** after successful upload or download completion. We do not permanently store your videos.

### Can I download private or restricted videos?
No. UpDownVid can only access publicly available content. Private videos, geo-restricted content, or videos requiring authentication cannot be downloaded.

## Metadata Extraction

### What metadata can I extract?
- Video title and description
- Creator/uploader name
- Duration and view count
- Upload date and publish time
- Hashtags and tags
- Thumbnail images
- Platform-specific metadata

### Can I edit metadata before uploading?
Yes! On the home page, you can customize title, description, tags, and privacy settings before uploading to YouTube.

## YouTube Automation

### How does YouTube automation work?
1. Connect your Google account
2. Add YouTube channels to monitor
3. Set monitoring interval (minimum 10 seconds)
4. When new videos are detected, they're automatically downloaded and uploaded to your channel

### What permissions do you need?
We only request:
- **YouTube Upload** - To upload videos to your channel
- **Basic Profile** - To identify your account

We **never** access your password or other sensitive data.

### Is automation safe?
Yes, but use responsibly:
- Respect copyright laws
- Don't re-upload copyrighted content without permission
- Follow YouTube's Terms of Service
- We're not responsible for account suspensions due to policy violations

## Troubleshooting

### Download failed - what should I do?
Try these steps:
1. **Check the URL** - Make sure it's a valid, public video link
2. **Try a VPN** - Some content may be geo-restricted
3. **Clear browser cache** - Old data may cause issues
4. **Check platform status** - The source platform may be down
5. **Contact support** - If issues persist: support@updownvid.com

### Why is the video quality lower than expected?
- Source video may not be available in higher quality
- Platform may restrict quality for certain videos
- Check [Platforms](/platforms) page for quality limitations

### Authentication errors when uploading to YouTube?
- Re-connect your Google account from [Accounts](/accounts)
- Check that you've granted YouTube upload permissions
- Your session may have expired - login again

### Metadata extraction is incomplete?
- Some platforms provide limited metadata
- Private or restricted content may have limited data
- Try using the direct platform URL instead of shortened links

## Privacy & Security

### Do you track my downloads?
No. We don't use analytics or tracking. See our [Privacy Policy](/privacy) for details.

### Is my data secure?
- Passwords are never stored (OAuth only)
- Temporary files are automatically deleted
- HTTPS encryption for all connections
- No data sharing with third parties

### Where is my data stored?
- **Temporary files:** Server storage (auto-deleted)
- **User settings:** Local session storage
- **OAuth tokens:** Encrypted session storage
- **No permanent databases** for user content

## Billing & Paid Features

### Are there any paid plans?
Currently, UpDownVid is **100% free**. We may introduce optional premium features in the future:
- Higher file size limits
- Faster processing
- Priority support
- Commercial usage licenses

### Can I use UpDownVid commercially?
Personal and educational use is free. For commercial use, please contact: business@updownvid.com

## Technical Questions

### What technology powers UpDownVid?
- **Backend:** Flask (Python)
- **Downloader:** yt-dlp
- **Frontend:** Bootstrap 5, Vanilla JavaScript
- **APIs:** YouTube Data API v3, Google OAuth 2.0

### Can I self-host UpDownVid?
Yes! It's open-source:
1. Clone from [GitHub](https://github.com/yourusername/updownvid)
2. Copy `.env.example` to `.env` and fill in your credentials
3. Run `python run.py`
4. See [README](https://github.com/yourusername/updownvid#readme) for details

### How can I contribute?
- Report bugs on [GitHub Issues](https://github.com/yourusername/updownvid/issues)
- Submit pull requests
- Improve documentation
- Share with others!

## Contact & Support

### How do I get help?
- **Email:** support@updownvid.com
- **GitHub Issues:** [Report bugs](https://github.com/yourusername/updownvid/issues)
- **Response time:** 48-72 hours

### Different contact emails:
- **General Support:** support@updownvid.com
- **Business Inquiries:** business@updownvid.com
- **Copyright/DMCA:** copyright@updownvid.com
- **Legal/Terms:** legal@updownvid.com

---

**Still have questions?** Contact us at support@updownvid.com or join our [community Discord](https://discord.gg/updownvid)!
