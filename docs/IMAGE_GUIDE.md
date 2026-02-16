# CredStack Visual Documentation Guide

This document provides details about the screenshots and visual assets in the CredStack repository.

## 📸 Screenshot Overview

All screenshots are stored in `/docs/images/` and demonstrate the key features of CredStack.

### Screenshot Specifications

- **Format**: PNG
- **Optimization**: Web-optimized, compressed for fast loading
- **Resolution**: High-DPI ready
- **Size**: 350-400 KB each (optimized for web)
- **Capture Method**: Playwright browser automation
- **Last Updated**: February 2026

## Available Screenshots

### 1. Landing Page (`landing-page.png`)

**URL**: https://github.com/user-attachments/assets/79721434-bf1a-4dd0-80aa-096b92626c6e

**Description**: The CredStack homepage featuring the login interface and value proposition.

**Key Elements Shown:**
- CredStack branding and logo
- Main tagline: "Master Your Credit Score Through Automation"
- Login form with email and password fields
- Registration link
- Three value propositions:
  - Consistency: Never miss statement dates
  - Automation: Automatic dispute tracking
  - Insights: Visual credit health tracking
- Modern glassmorphism design
- Dark gradient background (navy to purple)

**Use Cases:**
- README hero image
- Documentation introduction
- Marketing materials
- Project presentations

**Alt Text**: "CredStack landing page with login form and three key features: consistency, automation, and insights"

### 2. Main Dashboard (`dashboard.png`)

**URL**: https://github.com/user-attachments/assets/67a6ac64-75a3-4b94-adc1-9d7140978753

**Description**: The primary dashboard view showing all major features in action with demo data.

**Key Elements Shown:**

**Credit Health Section:**
- Large circular score display: 780
- "Excellent! Keep it up" status message
- Real-time score calculation

**Upcoming Tasks Section:**
- Welcome task for new users
- Statement date reminder
- Weekly credit check reminder
- Task completion dates
- "Done" buttons for task management

**Active Automations Section:**
- 8 automation rules displayed:
  1. Autopay Reminder
  2. Statement Alert
  3. Monthly Report
  4. Weekly Scan
  5. Dispute Tracker
  6. Credit Builder
  7. Inquiry Alert
  8. Monthly Task
- All showing "Active" status
- Toggle controls for each rule

**Linked Accounts Section:**
- Table showing 3 credit card accounts:
  - American Express Gold: $325.50 (6.5% utilization)
  - Chase Sapphire Reserve: $1,250.00 (8.3% utilization)
  - Discover It: $0.00 (0.0% utilization)
- Balance update functionality
- Account deletion options
- "+ Add Account" button
- Due date tracking

**Dispute Tracker Section:**
- Bureau selection dropdown (Experian, Equifax, TransUnion)
- Account name input field
- "Start Tracking Dispute" button

**Header:**
- CredStack logo
- User email display (demo@credstack.com)
- Logout button

**Use Cases:**
- Feature demonstration
- User onboarding tutorials
- Documentation of core functionality
- Marketing materials

**Alt Text**: "CredStack dashboard showing credit health score of 780, three linked credit card accounts with utilization tracking, eight active automation rules, upcoming tasks, and dispute tracking interface"

### 3. Registration Page (`register-page.png`)

**URL**: https://github.com/user-attachments/assets/0460de11-4b8f-436a-9cca-8cc5a52e5e6c

**Description**: User registration form with security features and clear instructions.

**Key Elements Shown:**
- Page title: "Create Your Account"
- Descriptive subtitle about joining CredStack
- Registration form fields:
  - Email Address (with placeholder)
  - Full Name (marked optional)
  - Password (with requirements)
  - Confirm Password
- Password requirements displayed:
  - "Must be at least 8 characters with letters and numbers"
- "Create Account" button (prominent cyan color)
- "Already have an account? Log in here" link
- Terms and privacy policy notice
- Data privacy assurance: "Your data is stored locally and never shared with third parties"
- Footer with copyright

**Use Cases:**
- Onboarding documentation
- Security feature demonstration
- Privacy-focused marketing
- User registration tutorials

**Alt Text**: "CredStack registration page with secure signup form including email, name, password fields, and privacy policy notice emphasizing local data storage"

## Design Principles

### Color Scheme
- **Primary**: Cyan (#00D9FF)
- **Background**: Dark gradient (navy #1a1a2e to purple #16213e)
- **Glass Effects**: Semi-transparent containers with backdrop blur
- **Text**: White and light gray for readability
- **Accents**: Green for success states (#4CAF50)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Headings**: Bold (600-800 weight)
- **Body**: Regular (400 weight)
- **Hierarchy**: Clear size differentiation

### UI Components
- **Glassmorphism cards**: Frosted glass effect with blur
- **Rounded corners**: Modern, friendly appearance
- **Consistent spacing**: Grid-based layout
- **Responsive design**: Adapts to different screen sizes

## Usage Guidelines

### In Documentation
```markdown
![CredStack Dashboard](https://github.com/user-attachments/assets/67a6ac64-75a3-4b94-adc1-9d7140978753)
*Real-time credit health monitoring with automation management*
```

### In HTML
```html
<img src="docs/images/dashboard.png" 
     alt="CredStack dashboard showing credit health score and account management" 
     width="800">
```

### Accessibility
- Always include descriptive alt text
- Provide text descriptions of key features
- Ensure sufficient color contrast
- Support screen reader navigation

## Screenshot Maintenance

### When to Update Screenshots

1. **Major UI changes**: Any significant design updates
2. **New features**: When adding prominent features
3. **Branding changes**: Logo or color scheme updates
4. **User feedback**: If screenshots are unclear or outdated

### How to Update Screenshots

1. Run the application locally:
   ```bash
   python app.py
   ```

2. Use Playwright or similar tool to capture:
   ```bash
   playwright codegen http://localhost:5000
   ```

3. Optimize images:
   ```bash
   # Using imagemagick
   convert original.png -quality 85 -resize 1920x docs/images/new-screenshot.png
   
   # Using pngquant
   pngquant --quality=80-90 docs/images/new-screenshot.png
   ```

4. Upload to GitHub and update URLs in README

### Optimization Tips

- Target file size: 300-500 KB per screenshot
- Resolution: 1920px width (or appropriate for content)
- Format: PNG for UI screenshots (better for text clarity)
- Compression: Use tools like TinyPNG, ImageOptim, or pngquant
- Naming: Use descriptive, lowercase, hyphenated names

## Future Visual Assets

### Planned Additions

1. **Demo Video/GIF**
   - Duration: 30-60 seconds
   - Shows login → dashboard → add account flow
   - Hosted on GitHub or YouTube
   - Embedded in README

2. **Feature-Specific Screenshots**
   - Automation rules configuration
   - Dispute tracking workflow
   - API token generation
   - Settings page

3. **Mobile Screenshots**
   - Responsive design on mobile devices
   - Touch-optimized interface
   - Mobile workflows

4. **Dark/Light Mode**
   - Current: Dark mode only
   - Future: Light mode screenshots

5. **Localization**
   - Screenshots in multiple languages
   - International date/currency formats

## License and Attribution

All screenshots in this repository are:
- Created using actual CredStack application
- © 2024 WADELABS / CredStack Open Source Project
- Licensed under MIT License
- Free to use for:
  - Documentation
  - Educational purposes
  - Marketing materials
  - Presentations
  - Blog posts and articles

### Attribution Template

When using screenshots externally:
```
Screenshot from CredStack - Open Source Credit Optimization Platform
https://github.com/WADELABS/Credit-Worthy
```

## Technical Details

### Capture Environment
- **Browser**: Chromium via Playwright
- **Resolution**: 1920x1080 viewport
- **OS**: Linux (Ubuntu)
- **Python Version**: 3.12
- **Flask Version**: 3.1.2

### Screenshot Metadata
```yaml
landing-page.png:
  size: 405 KB
  dimensions: 1920x1080
  format: PNG
  captured: 2026-02-16

dashboard.png:
  size: 383 KB
  dimensions: 1920x1200+ (full page)
  format: PNG
  captured: 2026-02-16

register-page.png:
  size: 357 KB
  dimensions: 1920x1080
  format: PNG
  captured: 2026-02-16
```

## Questions and Support

For questions about visual assets:
- Open an issue on GitHub
- Tag with `documentation` label
- Include specific screenshot or asset reference

---

*This guide is maintained as part of the CredStack documentation suite.*
