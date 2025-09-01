import os
import re
import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from playwright.async_api import async_playwright
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize GROQ client for future AI tasks (currently only initialized)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def extract_job_urls(text):
    """
    Extracts all URLs from the LinkedIn post text using regex.
    Regex finds all http/https links which are likely job listing links.
    """
    url_pattern = r"https?://[^\s)]+"
    urls = re.findall(url_pattern, text)
    return urls

async def apply_to_jobs_async(urls):
    """
    Uses async Playwright to visit each job URL.
    Searches for an 'Apply' button by text or button selector.
    Clicks the button to simulate applying.
    Collects URLs successfully applied to.
    """
    applied_jobs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for url in urls:
            print(f"Applying to {url} ...")
            await page.goto(url)
            try:
                # Attempt to find an apply button by text or button element with 'Apply'
                apply_button = await page.query_selector("text=Apply") or await page.query_selector("button:has-text('Apply')")
                if apply_button:
                    await apply_button.click()
                    # You can add custom form automation here if needed
                    applied_jobs.append(url)
                    print("Applied successfully.")
                else:
                    print(f"Apply button not found on {url}")
            except Exception as e:
                print(f"Could not apply on {url}: {str(e)}")
        await browser.close()
    return applied_jobs

def send_email_summary(user_email, job_urls):
    """
    Sends an email summary of successfully applied job URLs.
    Uses SMTP via Gmail. Email sender credentials should be set as environment variables.
    """
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("Error: Email credentials not set in environment variables.")
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = "Job Application Summary"
    message["From"] = sender_email
    message["To"] = user_email

    text = "You have successfully applied to the following job listings:\n\n"
    text += "\n".join(job_urls) if job_urls else "No applications were completed."

    part = MIMEText(text, "plain")
    message.attach(part)

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls(context=context)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, user_email, message.as_string())
        print(f"Summary email sent to {user_email}")
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

async def main_async():
    """
    Main async orchestration function for:
    - Extracting job URLs from LinkedIn post text
    - Applying to jobs asynchronously
    - Sending a summary email afterward
    """
    input_text = """
    This is the LinkedId post text.

    1. Google hiring Data Analytics Apprenticeship
    https://lnkd.in/gUMiSU8n

    2. JPMorganChase hiring Business Analyst
    https://lnkd.in/gyhadzQj

    3. American Express hiring Data Analytics
    https://lnkd.in/gviaPXZt
    """

    job_urls = extract_job_urls(input_text)
    print(f"Extracted URLs: {job_urls}")

    applied_jobs = await apply_to_jobs_async(job_urls)

    send_email_summary("YOUR-RECEIVER-EMAIL-ID", applied_jobs)

if __name__ == "__main__":
    try:
        asyncio.get_running_loop()
    except RuntimeError:  # No running event loop
        asyncio.run(main_async())
    else:
        # Running inside an existing event loop (e.g., Jupyter, Cursor)
        import nest_asyncio
        nest_asyncio.apply()
        await main_async()
