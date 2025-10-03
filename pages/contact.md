
# Contact Us

## Get in Touch

We're here to help! Whether you have questions, feedback, or need support, reach out to us using the information below.

## Contact Information

### General Support
**Email:** support@updownvid.com  
**Response Time:** 48-72 hours

### Business Inquiries
**Email:** business@updownvid.com  
For partnerships, commercial licenses, and enterprise solutions.

### Copyright & DMCA
**Email:** copyright@updownvid.com  
For copyright infringement reports and DMCA takedown requests.  
See our [Copyright Policy](/copyright) for the full process.

### Legal & Terms
**Email:** legal@updownvid.com  
For legal questions and terms of service inquiries.

## Community & Social

- **GitHub:** [github.com/yourusername/updownvid](https://github.com/yourusername/updownvid)
- **Discord:** [Join our community](https://discord.gg/updownvid) _(coming soon)_
- **Telegram:** [Follow updates](https://t.me/updownvid) _(coming soon)_
- **Twitter/X:** [@updownvid](https://twitter.com/updownvid) _(coming soon)_

## Report a Bug

Found a bug? Help us improve!

1. **Check existing issues:** [GitHub Issues](https://github.com/yourusername/updownvid/issues)
2. **Create a new issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots (if applicable)
   - Browser/device information

## Feature Requests

Have an idea? We'd love to hear it!

- **GitHub Discussions:** [Share your ideas](https://github.com/yourusername/updownvid/discussions)
- **Email:** support@updownvid.com with subject: "Feature Request"

## Contact Form

*Note: Contact form functionality requires SMTP configuration in `.env` file*

<div id="contact-form-container">
  <form id="contact-form" action="/submit_contact" method="POST">
    <div class="mb-3">
      <label for="name" class="form-label">Your Name *</label>
      <input type="text" class="form-control" id="name" name="name" required>
    </div>
    
    <div class="mb-3">
      <label for="email" class="form-label">Your Email *</label>
      <input type="email" class="form-control" id="email" name="email" required>
    </div>
    
    <div class="mb-3">
      <label for="subject" class="form-label">Subject *</label>
      <select class="form-select" id="subject" name="subject" required>
        <option value="">Select a topic...</option>
        <option value="general">General Inquiry</option>
        <option value="support">Technical Support</option>
        <option value="bug">Bug Report</option>
        <option value="feature">Feature Request</option>
        <option value="business">Business Inquiry</option>
        <option value="copyright">Copyright Issue</option>
      </select>
    </div>
    
    <div class="mb-3">
      <label for="message" class="form-label">Message *</label>
      <textarea class="form-control" id="message" name="message" rows="6" required></textarea>
    </div>
    
    <button type="submit" class="btn btn-primary">
      <i class="fas fa-paper-plane me-2"></i>Send Message
    </button>
  </form>
  
  <div id="form-response" class="mt-3" style="display: none;"></div>
</div>

<script>
document.getElementById('contact-form')?.addEventListener('submit', async (e) => {
  e.preventDefault();
  const form = e.target;
  const formData = new FormData(form);
  const responseDiv = document.getElementById('form-response');
  
  try {
    const response = await fetch('/submit_contact', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      responseDiv.className = 'alert alert-success mt-3';
      responseDiv.innerHTML = '<i class="fas fa-check-circle me-2"></i>' + result.message;
      form.reset();
    } else {
      responseDiv.className = 'alert alert-danger mt-3';
      responseDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>' + (result.error || 'Failed to send message');
    }
    
    responseDiv.style.display = 'block';
    setTimeout(() => { responseDiv.style.display = 'none'; }, 5000);
    
  } catch (error) {
    responseDiv.className = 'alert alert-danger mt-3';
    responseDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error sending message. Please try again or email us directly.';
    responseDiv.style.display = 'block';
  }
});
</script>

## Office Hours

**Support Team Availability:**
- Monday - Friday: 9:00 AM - 6:00 PM (UTC)
- Saturday - Sunday: Limited support

**Expected Response Times:**
- General inquiries: 48-72 hours
- Technical support: 24-48 hours
- Business inquiries: 1-2 business days
- Copyright issues: 24 hours (priority)

---

**Prefer direct email?** Reach us at support@updownvid.com
